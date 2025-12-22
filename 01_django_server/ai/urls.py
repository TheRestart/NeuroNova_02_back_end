from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'jobs', views.AIJobViewSet, basename='ai-job')

urlpatterns = [
    path('submit/', views.submit_ai_job, name='submit-ai-job'),
    path('', include(router.urls)),
]
