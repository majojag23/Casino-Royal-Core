from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login as auth_login
from django.utils import timezone
from django.core.mail import send_mail
from datetime import timedelta
from decimal import Decimal
import secrets

from .models import CustomUser, LoginHistory, PasswordReset
from .serializers import (
    UserSerializer, UserRegisterSerializer, LoginSerializer,
    UserProfileSerializer, ChangePasswordSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer
)


class AuthViewSet(viewsets.ViewSet):
    """Vistas de autenticación"""

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Registrar nuevo usuario"""
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Usuario registrado exitosamente',
                'user': UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Autenticación"""
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                'error': 'Email y contraseña requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
            if user.check_password(password):
                # Verificar bloqueo de cuenta
                if user.is_account_locked():
                    return Response({
                        'error': 'Cuenta bloqueada temporalmente'
                    }, status=status.HTTP_401_UNAUTHORIZED)

                # Login exitoso
                user.login_attempts = 0
                user.last_login = timezone.now()
                user.save()

                auth_login(request, user)

                return Response({
                    'message': 'Login exitoso',
                    'user': UserSerializer(user).data
                }, status=status.HTTP_200_OK)
            else:
                user.login_attempts += 1
                user.save()
                return Response({
                    'error': 'Credenciales incorrectas'
                }, status=status.HTTP_401_UNAUTHORIZED)

        except CustomUser.DoesNotExist:
            return Response({
                'error': 'Credenciales incorrectas'
            }, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout (invalidar token)"""
        return Response({'message': 'Logout exitoso'})

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def forgot_password(self, request):
        """Solicitar recuperación de contraseña"""
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                # No revelar si el email existe
                return Response({
                    'message': 'Si el email existe, se ha enviado un enlace de recuperación.'
                })

            # Crear token de recuperación
            token = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(hours=24)

            PasswordReset.objects.create(
                user=user,
                token=token,
                expires_at=expires_at
            )

            # Enviar email
            reset_url = f"http://127.0.0.1:8000/reset-password/{token}"
            send_mail(
                'Recupera tu contraseña - Casino Online',
                f'Haz clic en este enlace para recuperar tu contraseña:\n{reset_url}\n\nEste enlace expira en 24 horas.',
                'noreply@casino-online.com',
                [user.email],
                fail_silently=True,
            )

            return Response({
                'message': 'Email de recuperación enviado'
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def reset_password(self, request):
        """Reestablecer contraseña con token"""
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['password']

            try:
                reset = PasswordReset.objects.get(token=token)
            except PasswordReset.DoesNotExist:
                return Response({
                    'error': 'Token inválido'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not reset.is_valid():
                return Response({
                    'error': 'Token expirado. Solicita uno nuevo.'
                }, status=status.HTTP_400_BAD_REQUEST)

            reset.user.set_password(new_password)
            reset.user.save()

            reset.used = True
            reset.save()

            return Response({
                'message': 'Contraseña reestablecida exitosamente'
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _get_client_ip(self, request):
        """Obtener IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserViewSet(viewsets.ViewSet):
    """Vistas para operaciones de usuario"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Obtener perfil del usuario autenticado"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        """Actualizar perfil del usuario"""
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Cambiar contraseña"""
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user

            # Verificar contraseña antigua
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({
                    'error': 'Contraseña actual incorrecta'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Establecer nueva contraseña
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            return Response({'message': 'Contraseña cambiada exitosamente'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas reales del usuario para la pantalla de Perfil"""
        from apps.games.models import GameResult
        from apps.payments.models import Transaction

        user = request.user
        games = GameResult.objects.filter(user=user)
        total_bet = sum((g.bet_amount for g in games), Decimal('0'))
        total_payout = sum((g.payout for g in games), Decimal('0'))
        best_prize = max((g.payout for g in games), default=Decimal('0'))
        bonus_count = Transaction.objects.filter(user=user, transaction_type='bonus', status='completed').count()
        free_spins_remaining = request.session.get('slots_free_spins_remaining', 0)

        return Response({
            'games_played': games.count(),
            'total_payout': float(total_payout),
            'best_prize': float(best_prize),
            'springs': int(total_bet // 10),
            'free_spins_remaining': free_spins_remaining,
            'bonus_count': bonus_count,
            'member_since': user.date_joined.strftime('%d/%m/%Y'),
        })

    @action(detail=False, methods=['get'])
    def login_history(self, request):
        """Obtener historial de logins"""
        history = LoginHistory.objects.filter(user=request.user).order_by('-created_at')[:10]
        data = [
            {
                'ip_address': h.ip_address,
                'success': h.success,
                'created_at': h.created_at
            }
            for h in history
        ]
        return Response(data)
