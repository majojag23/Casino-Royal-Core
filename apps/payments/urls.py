from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet
from .webhooks import stripe_webhook

router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payments')

urlpatterns = [
    path('', include(router.urls)),
    path('stripe_webhook/', stripe_webhook, name='stripe_webhook'),
]
