from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'orders', views.RadiologyOrderViewSet, basename='radiology-order')
router.register(r'studies', views.RadiologyStudyViewSet, basename='radiology-study')
router.register(r'reports', views.RadiologyReportViewSet, basename='radiology-report')

urlpatterns = [
    path('health/', views.orthanc_health_check, name='orthanc-health'),
    path('sync/', views.sync_orthanc_studies, name='sync-orthanc-studies'),
    path('', include(router.urls)),
]
