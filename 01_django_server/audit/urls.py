from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet
from .views_admin import log_viewer

router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('', include(router.urls)),
    path('viewer/', log_viewer, name='audit-log-viewer'),
]
