"""
Sistema de notificaciones por email
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from celery import shared_task


class EmailNotifier:
    """Enviar notificaciones por email"""

    FROM_EMAIL = settings.DEFAULT_FROM_EMAIL

    @staticmethod
    def send_welcome_email(user):
        """Email de bienvenida"""
        subject = 'Bienvenido a Casino Online'
        context = {
            'user': user,
            'site_name': 'Casino Online',
            'login_url': 'http://localhost:8000/login/'
        }

        html_content = render_to_string('emails/welcome.html', context)
        text_content = f"Bienvenido {user.get_full_name()}, tu cuenta está lista para jugar!"

        EmailNotifier._send_email(
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            recipient_email=user.email
        )

    @staticmethod
    def send_deposit_confirmation(user, transaction):
        """Email de confirmación de depósito"""
        subject = f'Depósito de ${float(transaction.amount):.2f} Confirmado'
        context = {
            'user': user,
            'transaction': transaction,
            'amount': float(transaction.amount),
            'new_balance': float(user.balance)
        }

        html_content = render_to_string('emails/deposit_confirmation.html', context)
        text_content = f"Tu depósito de ${float(transaction.amount):.2f} ha sido confirmado. Tu nuevo saldo es ${float(user.balance):.2f}"

        EmailNotifier._send_email(
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            recipient_email=user.email
        )

    @staticmethod
    def send_withdrawal_initiated(user, transaction):
        """Email cuando se inicia un retiro"""
        subject = f'Retiro de ${float(transaction.amount):.2f} Iniciado'
        context = {
            'user': user,
            'transaction': transaction,
            'amount': float(transaction.amount),
            'status_url': 'http://localhost:8000/profile/transactions/'
        }

        html_content = render_to_string('emails/withdrawal_initiated.html', context)
        text_content = f"Tu solicitud de retiro de ${float(transaction.amount):.2f} ha sido recibida y está siendo procesada."

        EmailNotifier._send_email(
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            recipient_email=user.email
        )

    @staticmethod
    def send_withdrawal_completed(user, transaction):
        """Email cuando el retiro se completa"""
        subject = f'Retiro de ${float(transaction.amount):.2f} Completado'
        context = {
            'user': user,
            'transaction': transaction,
            'amount': float(transaction.amount),
            'date': transaction.completed_at
        }

        html_content = render_to_string('emails/withdrawal_completed.html', context)
        text_content = f"Tu retiro de ${float(transaction.amount):.2f} ha sido completado y llegará a tu cuenta."

        EmailNotifier._send_email(
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            recipient_email=user.email
        )

    @staticmethod
    def send_big_win_notification(user, game_result, multiplier):
        """Email para ganancias grandes"""
        subject = f'¡Ganaste ${float(game_result.profit_loss):.2f}!'
        context = {
            'user': user,
            'game': game_result.game_type,
            'bet': float(game_result.bet_amount),
            'payout': float(game_result.payout),
            'profit': float(game_result.profit_loss),
            'multiplier': multiplier
        }

        html_content = render_to_string('emails/big_win.html', context)
        text_content = f"¡Felicitaciones! Ganaste ${float(game_result.profit_loss):.2f} en {game_result.game_type} con multiplicador {multiplier}x"

        EmailNotifier._send_email(
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            recipient_email=user.email
        )

    @staticmethod
    def send_password_reset(user, reset_token):
        """Email de recuperación de contraseña"""
        subject = 'Recuperar tu Contraseña'
        reset_url = f'http://localhost:8000/reset_password/{reset_token}/'
        context = {
            'user': user,
            'reset_url': reset_url,
            'expires_in': '24 horas'
        }

        html_content = render_to_string('emails/password_reset.html', context)
        text_content = f"Haz click en este enlace para recuperar tu contraseña: {reset_url}"

        EmailNotifier._send_email(
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            recipient_email=user.email
        )

    @staticmethod
    def send_kyc_verification_reminder(user):
        """Email recordatorio para completar KYC"""
        subject = 'Completa tu Verificación de Identidad'
        context = {
            'user': user,
            'kyc_url': 'http://localhost:8000/kyc_verification/',
            'benefits': ['Retirar dinero', 'Límites mayores de apuesta', 'Soporte prioritario']
        }

        html_content = render_to_string('emails/kyc_reminder.html', context)
        text_content = "Completa tu verificación KYC para desbloquear todas las características del casino."

        EmailNotifier._send_email(
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            recipient_email=user.email
        )

    @staticmethod
    def send_account_security_alert(user, alert_type: str, details: dict = None):
        """Email de alerta de seguridad"""
        subject = 'Alerta de Seguridad en tu Cuenta'
        context = {
            'user': user,
            'alert_type': alert_type,
            'timestamp': timezone.now(),
            'details': details or {},
            'support_url': 'http://localhost:8000/support/'
        }

        html_content = render_to_string('emails/security_alert.html', context)
        text_content = f"Se ha detectado una actividad inusual en tu cuenta: {alert_type}"

        EmailNotifier._send_email(
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            recipient_email=user.email
        )

    @staticmethod
    def send_monthly_statement(user, stats: dict):
        """Extracto mensual de actividad"""
        subject = 'Tu Extracto de Casino - Mes Actual'
        context = {
            'user': user,
            'stats': stats,
            'month': timezone.now().strftime('%B %Y')
        }

        html_content = render_to_string('emails/monthly_statement.html', context)
        text_content = f"Resumen de tu actividad del mes: {stats}"

        EmailNotifier._send_email(
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            recipient_email=user.email
        )

    @staticmethod
    def _send_email(subject: str, text_content: str, html_content: str = None, recipient_email: str = None):
        """Método base para enviar email"""
        if not recipient_email:
            return False

        try:
            if html_content:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=EmailNotifier.FROM_EMAIL,
                    to=[recipient_email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            else:
                send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=EmailNotifier.FROM_EMAIL,
                    recipient_list=[recipient_email]
                )
            return True
        except Exception as e:
            print(f"Error enviando email: {str(e)}")
            return False


# Tareas Celery (opcional, requiere Redis)
@shared_task
def send_welcome_email_task(user_id):
    """Enviar email de bienvenida asíncronamente"""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
        EmailNotifier.send_welcome_email(user)
    except User.DoesNotExist:
        pass


@shared_task
def send_deposit_confirmation_task(user_id, transaction_id):
    """Enviar confirmación de depósito asíncronamente"""
    from django.contrib.auth import get_user_model
    from apps.payments.models import Transaction
    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
        transaction = Transaction.objects.get(id=transaction_id)
        EmailNotifier.send_deposit_confirmation(user, transaction)
    except (User.DoesNotExist, Transaction.DoesNotExist):
        pass


@shared_task
def send_kyc_reminder_task(user_id):
    """Enviar recordatorio KYC asíncronamente"""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        user = User.objects.get(id=user_id, kyc_verified=False)
        EmailNotifier.send_kyc_verification_reminder(user)
    except User.DoesNotExist:
        pass
