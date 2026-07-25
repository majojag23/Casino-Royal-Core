"""
Webhook handlers para eventos de Stripe
"""

import json
import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction as db_transaction

from .models import Transaction
from apps.core.websocket_utils import WebSocketBroadcaster

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    """
    Webhook endpoint para eventos de Stripe
    POST /api/payments/stripe_webhook/
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Manejar eventos
    if event['type'] == 'payment_intent.succeeded':
        handle_payment_intent_succeeded(event['data']['object'])
    elif event['type'] == 'payment_intent.payment_failed':
        handle_payment_intent_failed(event['data']['object'])
    elif event['type'] == 'charge.refunded':
        handle_charge_refunded(event['data']['object'])

    return JsonResponse({'status': 'success'}, status=200)


def handle_payment_intent_succeeded(payment_intent):
    """Manejar payment intent exitoso"""
    try:
        # Buscar transacción por payment_intent_id
        txn = Transaction.objects.get(
            transaction_id=payment_intent['id'],
            transaction_type='deposit',
            status='pending'
        )

        with db_transaction.atomic():
            # Actualizar transacción
            txn.status = 'completed'
            txn.metadata = {
                'stripe_status': 'succeeded',
                'payment_intent_id': payment_intent['id'],
                'charges': payment_intent.get('charges', {}).get('data', [])
            }
            txn.save()

            # Actualizar balance
            user = txn.user
            user.balance += txn.amount
            user.save()

            # Emitir evento WebSocket
            WebSocketBroadcaster.broadcast_balance_update(
                user_id=user.id,
                balance=user.balance
            )

            WebSocketBroadcaster.send_notification(
                user_id=user.id,
                title='Depósito Completado',
                message=f'Se depositaron ${float(txn.amount):.2f} a tu cuenta',
                level='success'
            )

    except Transaction.DoesNotExist:
        pass


def handle_payment_intent_failed(payment_intent):
    """Manejar payment intent fallido"""
    try:
        txn = Transaction.objects.get(
            transaction_id=payment_intent['id'],
            transaction_type='deposit',
            status='pending'
        )

        with db_transaction.atomic():
            # Actualizar transacción
            txn.status = 'failed'
            txn.metadata = {
                'stripe_status': 'failed',
                'payment_intent_id': payment_intent['id'],
                'error': payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
            }
            txn.save()

            # Notificar al usuario
            user = txn.user
            WebSocketBroadcaster.send_notification(
                user_id=user.id,
                title='Depósito Fallido',
                message=f'No se pudo procesar tu depósito de ${float(txn.amount):.2f}',
                level='error'
            )

    except Transaction.DoesNotExist:
        pass


def handle_charge_refunded(charge):
    """Manejar reembolso de cargo"""
    try:
        txn = Transaction.objects.get(
            metadata__contains={'charge_id': charge['id']},
            transaction_type='deposit',
            status='completed'
        )

        with db_transaction.atomic():
            # Revertir balance
            user = txn.user
            user.balance -= txn.amount
            user.save()

            # Crear transacción de reembolso
            refund_txn = Transaction.objects.create(
                user=user,
                transaction_id=f"REFUND-{charge['id']}",
                transaction_type='refund',
                amount=txn.amount,
                status='completed',
                metadata={
                    'original_transaction_id': txn.id,
                    'charge_id': charge['id']
                }
            )

            # Notificar
            WebSocketBroadcaster.send_notification(
                user_id=user.id,
                title='Reembolso Procesado',
                message=f'Se reembolsaron ${float(txn.amount):.2f}',
                level='warning'
            )

    except Transaction.DoesNotExist:
        pass
