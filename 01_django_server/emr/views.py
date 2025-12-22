from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import os
from .openemr_client import OpenEMRClient


# OpenEMR 클라이언트 인스턴스
openemr_url = os.getenv('OPENEMR_BASE_URL', 'http://localhost:80')
client = OpenEMRClient(base_url=openemr_url)


@require_http_methods(["GET"])
def health_check(request):
    """OpenEMR 서버 상태 확인"""
    result = client.health_check()
    return JsonResponse(result)


@csrf_exempt
@require_http_methods(["POST"])
def authenticate(request):
    """OpenEMR 인증"""
    result = client.authenticate()
    return JsonResponse(result)


@require_http_methods(["GET"])
def list_patients(request):
    """환자 목록 조회"""
    limit = int(request.GET.get('limit', 10))
    patients = client.get_patients(limit=limit)
    return JsonResponse({
        "count": len(patients),
        "results": patients
    })


@require_http_methods(["GET"])
def search_patients(request):
    """환자 검색"""
    given = request.GET.get('given')
    family = request.GET.get('family')

    patients = client.search_patients(given=given, family=family)
    return JsonResponse({
        "count": len(patients),
        "results": patients
    })


@require_http_methods(["GET"])
def get_patient(request, patient_id):
    """특정 환자 조회"""
    patient = client.get_patient(patient_id)

    if patient:
        return JsonResponse(patient)
    else:
        return JsonResponse({
            "error": "Patient not found"
        }, status=404)
