from django.urls import path
from . import views

app_name = 'emr'

urlpatterns = [
    path('health/', views.health_check, name='health'),
    path('auth/', views.authenticate, name='authenticate'),
    path('patients/', views.list_patients, name='list_patients'),
    path('patients/search/', views.search_patients, name='search_patients'),
    path('patients/<str:patient_id>/', views.get_patient, name='get_patient'),
]
