from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LabTestMasterViewSet, LabResultViewSet

router = DefaultRouter()
router.register(r'tests', LabTestMasterViewSet, basename='lab-test-master')
router.register(r'results', LabResultViewSet, basename='lab-result')

urlpatterns = [
    path('', include(router.urls)),
]
