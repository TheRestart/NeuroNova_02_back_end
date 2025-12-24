from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'jobs', views.AIJobViewSet, basename='ai-job')

urlpatterns = [
    path('submit/', views.submit_ai_job, name='submit-ai-job'),
    path('callback/', views.ai_callback, name='ai-callback'),
    path('', include(router.urls)),
]
