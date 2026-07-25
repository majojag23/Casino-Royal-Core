"""
Configuración de Stripe para procesamiento de pagos
"""

import stripe
from django.conf import settings
from decimal import Decimal

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentProcessor:
    """Procesa pagos con Stripe"""

    @staticmethod
    def create_payment_intent(amount: Decimal, currency: str = 'usd', metadata: dict = None) -> dict:
        """
        Crea un Payment Intent en Stripe

        Args:
            amount: Monto en USD (Decimal)
            currency: Moneda (default: 'usd')
            metadata: Datos adicionales para el pago

        Returns:
            dict con client_secret y payment_intent_id
        """
        try:
            amount_cents = int(amount * 100)

            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={
                    'enabled': True,
                }
            )

            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'amount': float(amount),
                'status': intent.status
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': e.code if hasattr(e, 'code') else 'unknown'
            }

    @staticmethod
    def confirm_payment(payment_intent_id: str) -> dict:
        """
        Confirma el estado de un payment intent
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                'success': True,
                'payment_intent_id': intent.id,
                'status': intent.status,
                'amount': Decimal(str(intent.amount / 100)),
                'currency': intent.currency,
                'latest_charge': intent.latest_charge
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def create_customer(email: str, name: str, metadata: dict = None) -> dict:
        """
        Crea un customer en Stripe
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )

            return {
                'success': True,
                'customer_id': customer.id,
                'email': customer.email
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def attach_payment_method(customer_id: str, payment_method_id: str) -> dict:
        """
        Adjunta un payment method a un customer
        """
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )

            return {
                'success': True,
                'payment_method_id': payment_method.id,
                'type': payment_method.type,
                'card': payment_method.card.to_dict() if payment_method.type == 'card' else None
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def create_charge(customer_id: str, amount: Decimal, description: str = '', metadata: dict = None) -> dict:
        """
        Crea un cargo directo en Stripe (deprecated en favor de PaymentIntent)
        """
        try:
            amount_cents = int(amount * 100)

            charge = stripe.Charge.create(
                amount=amount_cents,
                currency='usd',
                customer=customer_id,
                description=description,
                metadata=metadata or {}
            )

            return {
                'success': True,
                'charge_id': charge.id,
                'amount': float(amount),
                'status': charge.status,
                'paid': charge.paid
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def refund_charge(charge_id: str, amount: Decimal = None) -> dict:
        """
        Reembolsa un cargo

        Args:
            charge_id: ID del cargo a reembolsar
            amount: Monto a reembolsar (None = completo)
        """
        try:
            kwargs = {
                'charge': charge_id,
            }

            if amount:
                kwargs['amount'] = int(amount * 100)

            refund = stripe.Refund.create(**kwargs)

            return {
                'success': True,
                'refund_id': refund.id,
                'amount': Decimal(str(refund.amount / 100)),
                'status': refund.status
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def list_payment_methods(customer_id: str) -> dict:
        """
        Lista todos los payment methods de un customer
        """
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card'
            )

            return {
                'success': True,
                'payment_methods': [
                    {
                        'id': pm.id,
                        'type': pm.type,
                        'card': {
                            'brand': pm.card.brand,
                            'last4': pm.card.last4,
                            'exp_month': pm.card.exp_month,
                            'exp_year': pm.card.exp_year,
                        } if pm.type == 'card' else None
                    }
                    for pm in payment_methods.data
                ]
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def delete_payment_method(payment_method_id: str) -> dict:
        """
        Elimina un payment method
        """
        try:
            stripe.PaymentMethod.detach(payment_method_id)

            return {
                'success': True,
                'message': 'Payment method deleted'
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }
