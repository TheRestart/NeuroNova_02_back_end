from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicationMasterViewSet, DiagnosisMasterViewSet

router = DefaultRouter()
router.register(r'medications', MedicationMasterViewSet, basename='medication-master')
router.register(r'diagnoses', DiagnosisMasterViewSet, basename='diagnosis-master')

urlpatterns = [
    path('', include(router.urls)),
]
