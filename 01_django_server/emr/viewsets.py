"""
EMR ViewSets for CRUD Operations

아키텍처:
- Single Source of Truth: OpenEMR (FHIR Server)
- Django DB: Read Cache Only
- Write-Through Strategy: FHIR 서버 먼저 업데이트 → 성공 시 Django DB 업데이트
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
import logging

from .models import PatientCache, Encounter, Order, OrderItem
from .serializers import (
    PatientCacheSerializer, PatientCreateSerializer,
    EncounterSerializer, EncounterCreateSerializer,
    OrderSerializer, OrderCreateSerializer,
    OrderItemSerializer, OrderItemUpdateSerializer
)
from .services import PatientService, EncounterService, OrderService
from .fhir_adapter import FHIRServiceAdapter

logger = logging.getLogger(__name__)


class PatientCacheViewSet(viewsets.ModelViewSet):
    """
    환자 CRUD ViewSet (Write-Through Pattern)

    - list: GET /api/emr/patients/
    - retrieve: GET /api/emr/patients/{id}/
    - create: POST /api/emr/patients/
    - update: PUT /api/emr/patients/{id}/
    - partial_update: PATCH /api/emr/patients/{id}/  (Write-Through 적용)
    - destroy: DELETE /api/emr/patients/{id}/

    데이터 수정 흐름:
    1. FHIR 서버에 수정 요청
    2. 성공 시 Django DB 업데이트
    3. 실패 시 Django DB 수정 없이 에러 반환
    """
    queryset = PatientCache.objects.all()
    permission_classes = [AllowAny]  # 개발 모드

    def get_serializer_class(self):
        if self.action == 'create':
            return PatientCreateSerializer
        return PatientCacheSerializer

    def create(self, request, *args, **kwargs):
        """환자 생성 (Service 레이어 사용)"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Service 레이어에서 ID 자동 생성
        patient = PatientService.create_patient(serializer.validated_data)

        # 응답용 Serializer
        response_serializer = PatientCacheSerializer(patient)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """
        환자 프로필 수정 (PATCH) - Write-Through Pattern

        처리 흐름:
        1. Django DB에서 환자 조회
        2. FHIR Adapter를 통해 FHIR 서버에 수정 요청
        3. FHIR 서버 응답 처리:
           - 성공 (200): Django DB 업데이트 후 200 응답
           - 거절 (400): Django DB 수정 없이 400 에러 응답
           - 장애 (Exception): Django DB 수정 없이 503 에러 응답
        """
        # Given: 환자 조회
        patient = self.get_object()

        # Serializer 검증
        serializer = self.get_serializer(patient, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # OpenEMR Patient ID 확인
        if not patient.openemr_patient_id:
            logger.warning(f"Patient {patient.patient_id} has no OpenEMR ID - skipping FHIR sync")
            # OpenEMR과 동기화되지 않은 환자는 Django DB만 업데이트
            self.perform_update(serializer)
            return Response(serializer.data)

        # When: FHIR Adapter를 통해 FHIR 서버에 수정 요청
        fhir_adapter = FHIRServiceAdapter()
        update_data = {
            key: value for key, value in serializer.validated_data.items()
            if key in ['phone', 'email', 'address']  # FHIR 동기화 대상 필드만
        }

        try:
            # FHIR 서버에 업데이트 요청 (선행)
            success, result = fhir_adapter.update_patient(
                patient.openemr_patient_id,
                update_data
            )

            # Then: 결과 처리
            if success:
                # Case A: FHIR 서버 업데이트 성공 -> Django DB 업데이트 (Service Layer 사용)
                logger.info(f"FHIR update success for patient {patient.patient_id}")
                
                # 낙관적 락을 위해 현재 버전 포함
                update_data['version'] = patient.version
                
                try:
                    updated_patient = PatientService.update_patient(patient.patient_id, update_data)
                    # 시리얼라이저 데이터 갱신
                    serializer = self.get_serializer(updated_patient)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                except Exception as e:
                    return Response(
                        {"error": "Database update failed", "detail": str(e)},
                        status=status.HTTP_409_CONFLICT
                    )

            else:
                # Case B: FHIR 서버 거절 (유효성 검사 실패 등)
                error_msg = result.get('error', 'FHIR validation failed')
                logger.warning(f"FHIR validation failed for patient {patient.patient_id}: {error_msg}")
                return Response(
                    {"error": error_msg, "detail": "FHIR server rejected the update"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            # Case C: FHIR 서버 통신 장애
            error_msg = str(e)
            logger.error(f"FHIR server error for patient {patient.patient_id}: {error_msg}")
            return Response(
                {"error": "FHIR server communication failed", "detail": error_msg},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @action(detail=False, methods=['get'])
    def search(self, request):
        """환자 검색 (이름, 전화번호, 이메일)"""
        query = request.query_params.get('q', '')

        queryset = self.queryset.filter(
            family_name__icontains=query
        ) | self.queryset.filter(
            given_name__icontains=query
        ) | self.queryset.filter(
            phone__icontains=query
        ) | self.queryset.filter(
            email__icontains=query
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class EncounterViewSet(viewsets.ModelViewSet):
    """
    진료 기록 CRUD ViewSet

    - list: GET /api/emr/encounters/
    - retrieve: GET /api/emr/encounters/{id}/
    - create: POST /api/emr/encounters/
    - update: PUT /api/emr/encounters/{id}/
    - partial_update: PATCH /api/emr/encounters/{id}/
    - destroy: DELETE /api/emr/encounters/{id}/
    """
    queryset = Encounter.objects.all()
    permission_classes = [AllowAny]  # 개발 모드

    def get_serializer_class(self):
        if self.action == 'create':
            return EncounterCreateSerializer
        return EncounterSerializer

    def create(self, request, *args, **kwargs):
        """진료 기록 생성 (Service 레이어 사용)"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Service 레이어에서 ID 자동 생성
        encounter = EncounterService.create_encounter(serializer.validated_data)

        # 응답용 Serializer
        response_serializer = EncounterSerializer(encounter)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def by_patient(self, request):
        """특정 환자의 진료 기록 조회"""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response(
                {"error": "patient_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.queryset.filter(patient_id=patient_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    """
    처방 CRUD ViewSet

    - list: GET /api/emr/orders/
    - retrieve: GET /api/emr/orders/{id}/
    - create: POST /api/emr/orders/
    - update: PUT /api/emr/orders/{id}/
    - partial_update: PATCH /api/emr/orders/{id}/
    - destroy: DELETE /api/emr/orders/{id}/
    """
    queryset = Order.objects.all()
    permission_classes = [AllowAny]  # 개발 모드

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        """처방 생성 (Service 레이어 사용)"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_data = serializer.validated_data
        items_data = order_data.pop('order_items', [])

        # Service 레이어에서 ID 자동 생성
        order = OrderService.create_order(order_data, items_data)

        # 응답용 Serializer
        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def by_patient(self, request):
        """특정 환자의 처방 목록 조회"""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response(
                {"error": "patient_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.queryset.filter(patient_id=patient_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """처방 실행 (Service 레이어 및 Locking 적용)"""
        order = self.get_object()
        executed_by = request.data.get('executed_by')
        current_version = request.data.get('version')  # 클라이언트가 보낸 버전

        if not executed_by:
            return Response(
                {"error": "executed_by is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if current_version is None:
             return Response(
                {"error": "version is required for optimistic locking"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            updated_order = OrderService.execute_order(order.order_id, executed_by, current_version)
            serializer = self.get_serializer(updated_order)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_409_CONFLICT
            )


class OrderItemViewSet(viewsets.ModelViewSet):
    """
    처방 항목(상세) CRUD ViewSet
    
    - update/patch: 처방 내역 수정 (용량, 횟수 등)
    - destroy: 처방 약품 삭제
    """
    queryset = OrderItem.objects.all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return OrderItemUpdateSerializer
        return OrderItemSerializer
