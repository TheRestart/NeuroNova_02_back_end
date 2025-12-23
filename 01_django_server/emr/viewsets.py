"""
EMR ViewSets for CRUD Operations
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import PatientCache, Encounter, Order, OrderItem
from .serializers import (
    PatientCacheSerializer, PatientCreateSerializer,
    EncounterSerializer, EncounterCreateSerializer,
    OrderSerializer, OrderCreateSerializer,
    OrderItemSerializer, OrderItemUpdateSerializer
)
from .services import PatientService, EncounterService, OrderService


class PatientCacheViewSet(viewsets.ModelViewSet):
    """
    환자 CRUD ViewSet

    - list: GET /api/emr/patients/
    - retrieve: GET /api/emr/patients/{id}/
    - create: POST /api/emr/patients/
    - update: PUT /api/emr/patients/{id}/
    - partial_update: PATCH /api/emr/patients/{id}/
    - destroy: DELETE /api/emr/patients/{id}/
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
        """처방 실행"""
        order = self.get_object()
        executed_by = request.data.get('executed_by')

        if not executed_by:
            return Response(
                {"error": "executed_by is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.utils import timezone
        order.status = 'completed'
        order.executed_at = timezone.now()
        order.executed_by = executed_by
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data)


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
