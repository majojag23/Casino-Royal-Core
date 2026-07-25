from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from apps.users.models import CustomUser
from apps.payments.models import Transaction
from apps.games.models import GameResult
from .models import AdminPanel, AdminLog


class AdminPanelViewSet(viewsets.ViewSet):
    """Panel de administrador"""
    permission_classes = [IsAuthenticated]

    def check_admin(self, user):
        if not user.is_superuser:
            raise PermissionError('Only superusers')
        return True

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Dashboard del admin"""
        self.check_admin(request.user)

        total_users = CustomUser.objects.count()
        active_users = CustomUser.objects.filter(status='active').count()
        total_balance = CustomUser.objects.aggregate(Sum('balance'))['balance__sum'] or 0

        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_deposits = Transaction.objects.filter(
            transaction_type='deposit',
            status='completed',
            created_at__gte=today_start
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'total_balance': float(total_balance),
            'today_deposits': float(today_deposits),
        })

    @action(detail=False, methods=['get'])
    def users(self, request):
        """Listar usuarios"""
        self.check_admin(request.user)

        users = CustomUser.objects.all().values('id', 'username', 'email', 'balance', 'status')[:100]
        return Response(list(users))

    @action(detail=False, methods=['post'])
    def suspend_user(self, request):
        """Suspender usuario"""
        self.check_admin(request.user)

        user_id = request.data.get('user_id')
        try:
            user = CustomUser.objects.get(id=user_id)
            user.status = 'suspended'
            user.save()
            return Response({'message': 'User suspended'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Ver transacciones"""
        self.check_admin(request.user)

        txns = Transaction.objects.select_related('user').all().values(
            'id', 'user__username', 'transaction_type', 'amount', 'status', 'created_at'
        )[:100]
        return Response(list(txns))
