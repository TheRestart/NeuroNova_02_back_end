from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, viewsets

app_name = 'emr'

# DRF Router for CRUD ViewSets
router = DefaultRouter()
router.register(r'patients', viewsets.PatientCacheViewSet, basename='patient')
router.register(r'encounters', viewsets.EncounterViewSet, basename='encounter')
router.register(r'orders', viewsets.OrderViewSet, basename='order')
router.register(r'order-items', viewsets.OrderItemViewSet, basename='order-item')

urlpatterns = [
    # OpenEMR 연동 API (기존)
    path('health/', views.health_check, name='health'),
    path('auth/', views.authenticate, name='authenticate'),
    path('openemr/patients/', views.list_patients, name='list_patients'),
    path('openemr/patients/search/', views.search_patients, name='search_patients'),
    path('openemr/patients/<str:patient_id>/', views.get_patient, name='get_patient'),
    path('openemr/verify-emr/<str:patient_id>/', views.verify_emr_data, name='verify_emr_data'),

    # CRUD API (ViewSets)
    path('', include(router.urls)),
    
    # Test Dashboard (UI)
    path('test-dashboard/', views.test_dashboard, name='test_dashboard'),
    path('test-ui/', views.test_ui_legacy, name='test_ui_legacy'),
    path('comprehensive-test/', views.comprehensive_test, name='comprehensive_test'),
]
