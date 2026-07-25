from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import json

from .models import Transaction, PaymentMethod
from .stripe_config import StripePaymentProcessor
from apps.core.websocket_utils import WebSocketBroadcaster


class PaymentViewSet(viewsets.ViewSet):
    """Vistas para pagos con Stripe integrado"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def create_deposit_intent(self, request):
        """Crear Payment Intent para depósito con Stripe"""
        user = request.user
        amount = Decimal(str(request.data.get('amount', 0)))
        payment_method_type = request.data.get('payment_method_type', 'card')

        if amount <= 0:
            return Response({'error': 'Monto inválido'}, status=status.HTTP_400_BAD_REQUEST)

        if amount < Decimal('1') or amount > Decimal('10000'):
            return Response({'error': 'Monto debe estar entre $1 y $10,000'}, status=status.HTTP_400_BAD_REQUEST)

        # Crear Payment Intent en Stripe
        result = StripePaymentProcessor.create_payment_intent(
            amount=amount,
            currency='usd',
            metadata={
                'user_id': user.id,
                'email': user.email,
                'type': 'deposit',
                'payment_method_type': payment_method_type
            }
        )

        if not result['success']:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

        # Crear transacción pendiente
        txn = Transaction.objects.create(
            user=user,
            transaction_id=result['payment_intent_id'],
            transaction_type='deposit',
            amount=amount,
            payment_method=payment_method_type,
            status='pending',
            metadata={
                'payment_intent_id': result['payment_intent_id'],
                'stripe_status': result['status']
            }
        )

        return Response({
            'transaction_id': txn.id,
            'client_secret': result['client_secret'],
            'payment_intent_id': result['payment_intent_id'],
            'amount': float(amount),
            'status': 'pending',
            'publishable_key': settings.STRIPE_PUBLISHABLE_KEY
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def confirm_deposit(self, request):
        """Confirmar depósito después de pago exitoso"""
        user = request.user
        payment_intent_id = request.data.get('payment_intent_id')

        if not payment_intent_id:
            return Response({'error': 'Payment Intent ID requerido'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            txn = Transaction.objects.get(
                transaction_id=payment_intent_id,
                user=user,
                transaction_type='deposit'
            )
        except Transaction.DoesNotExist:
            return Response({'error': 'Transacción no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        # Confirmar estado en Stripe
        result = StripePaymentProcessor.confirm_payment(payment_intent_id)

        if not result['success']:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

        if result['status'] != 'succeeded':
            return Response({
                'error': f'Pago no procesado: {result["status"]}',
                'status': result['status']
            }, status=status.HTTP_400_BAD_REQUEST)

        # Actualizar transacción y balance
        with transaction.atomic():
            txn.status = 'completed'
            txn.metadata['stripe_status'] = 'succeeded'
            txn.save()

            user.balance += txn.amount
            user.save()

            # Bono de bienvenida: 100% hasta $200 en el primer depósito.
            # Se acredita como bonus_balance (no retirable), solo para jugar,
            # y se libera al saldo real al cumplir el requisito de apuesta (20x).
            bonus_amount = user.grant_welcome_bonus(txn.amount, match_rate=1.0, max_bonus=200, rollover=20)
            if bonus_amount:
                Transaction.objects.create(
                    user=user,
                    transaction_id=f"BONUS-WELCOME-{user.id}-{timezone.now().timestamp()}",
                    transaction_type='bonus',
                    amount=bonus_amount,
                    status='completed',
                    metadata={'bonus_type': 'welcome', 'wagering_required': float(user.bonus_wagering_required)}
                )
                WebSocketBroadcaster.send_notification(
                    user_id=user.id,
                    title='¡Bono de bienvenida activado!',
                    message=f'Recibiste ${float(bonus_amount):.2f} de bono para jugar (no retirable en efectivo)',
                    level='success'
                )

            # Emitir evento WebSocket
            WebSocketBroadcaster.broadcast_balance_update(
                user_id=user.id,
                balance=user.balance
            )

            WebSocketBroadcaster.send_notification(
                user_id=user.id,
                title='Depósito Exitoso',
                message=f'Se agregaron ${float(txn.amount):.2f} a tu balance',
                level='success'
            )

        return Response({
            'transaction_id': txn.id,
            'status': 'completed',
            'amount': float(txn.amount),
            'new_balance': float(user.balance),
            'bonus_awarded': float(bonus_amount) if bonus_amount else 0,
            'bonus_balance': float(user.bonus_balance),
            'message': 'Depósito completado exitosamente'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        """Crear retiro (requiere verificación KYC)"""
        user = request.user

        if not user.kyc_verified:
            return Response({
                'error': 'Debe completar verificación KYC para retirar',
                'kyc_verified': False
            }, status=status.HTTP_403_FORBIDDEN)

        amount = Decimal(str(request.data.get('amount', 0)))

        if amount <= 0:
            return Response({'error': 'Monto inválido'}, status=status.HTTP_400_BAD_REQUEST)

        if amount < Decimal('10') or amount > Decimal('50000'):
            return Response({'error': 'Monto debe estar entre $10 y $50,000'}, status=status.HTTP_400_BAD_REQUEST)

        if user.balance < amount:
            return Response({'error': 'Saldo insuficiente'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user.balance -= amount
            user.save()

            txn = Transaction.objects.create(
                user=user,
                transaction_id=f"WITHDRAW-{user.id}-{timezone.now().timestamp()}",
                transaction_type='withdrawal',
                amount=amount,
                payment_method='bank_transfer',
                status='pending',
                metadata={
                    'withdraw_method': request.data.get('withdraw_method', 'bank_transfer'),
                    'bank_details': request.data.get('bank_details', {})
                }
            )

            WebSocketBroadcaster.send_notification(
                user_id=user.id,
                title='Retiro Pendiente',
                message=f'Tu retiro de ${float(amount):.2f} está siendo procesado',
                level='info'
            )

        return Response({
            'transaction_id': txn.id,
            'status': 'pending',
            'amount': float(amount),
            'message': 'Retiro pendiente. Se procesará en 1-3 días hábiles'
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Obtener historial de transacciones"""
        txns = Transaction.objects.filter(user=request.user).order_by('-created_at')[:50]
        data = [
            {
                'id': t.id,
                'type': t.transaction_type,
                'amount': float(t.amount),
                'status': t.status,
                'payment_method': t.payment_method,
                'created_at': t.created_at.isoformat()
            }
            for t in txns
        ]
        return Response(data)

    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Obtener balance actual del usuario"""
        return Response({
            'balance': float(request.user.balance),
            'bonus_balance': float(request.user.bonus_balance),
            'total': float(request.user.balance + request.user.bonus_balance)
        })

    @action(detail=False, methods=['post'])
    def add_payment_method(self, request):
        """Agregar un payment method para futuras transacciones"""
        user = request.user
        payment_method_id = request.data.get('payment_method_id')
        nickname = request.data.get('nickname', 'Mi tarjeta')

        if not payment_method_id:
            return Response({'error': 'Payment Method ID requerido'}, status=status.HTTP_400_BAD_REQUEST)

        # Crear customer en Stripe si no existe
        if not user.stripe_customer_id:
            result = StripePaymentProcessor.create_customer(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                metadata={'user_id': user.id}
            )

            if not result['success']:
                return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

            user.stripe_customer_id = result['customer_id']
            user.save()

        # Adjuntar payment method
        result = StripePaymentProcessor.attach_payment_method(
            customer_id=user.stripe_customer_id,
            payment_method_id=payment_method_id
        )

        if not result['success']:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

        # Guardar en BD
        PaymentMethod.objects.create(
            user=user,
            stripe_payment_method_id=payment_method_id,
            type=result['type'],
            nickname=nickname,
            last_four=result['card']['last4'] if result['card'] else '',
            metadata=result
        )

        return Response({
            'success': True,
            'payment_method_id': payment_method_id,
            'type': result['type'],
            'last_four': result['card']['last4'] if result['card'] else ''
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def payment_methods(self, request):
        """Listar payment methods guardados"""
        methods = PaymentMethod.objects.filter(user=request.user, active=True)
        data = [
            {
                'id': m.id,
                'stripe_id': m.stripe_payment_method_id,
                'type': m.type,
                'nickname': m.nickname,
                'last_four': m.last_four
            }
            for m in methods
        ]
        return Response(data)

    @action(detail=False, methods=['post'])
    def remove_payment_method(self, request):
        """Remover un payment method"""
        user = request.user
        payment_method_id = request.data.get('payment_method_id')

        try:
            method = PaymentMethod.objects.get(
                user=user,
                id=payment_method_id
            )
        except PaymentMethod.DoesNotExist:
            return Response({'error': 'Payment method no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # Eliminar de Stripe
        result = StripePaymentProcessor.delete_payment_method(method.stripe_payment_method_id)

        if not result['success']:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

        # Marcar como inactivo
        method.active = False
        method.save()

        return Response({'success': True, 'message': 'Payment method removido'})
