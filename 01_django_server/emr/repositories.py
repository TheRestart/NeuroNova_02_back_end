
from django.db import transaction
from .models import PatientCache, Order, OrderItem

class PatientRepository:
    """환자 데이터 저장소"""
    
    @staticmethod
    def create_patient(data):
        """환자 생성"""
        return PatientCache.objects.create(**data)
    
    @staticmethod
    def get_patient_by_id(patient_id):
        """환자 조회"""
        return PatientCache.objects.filter(patient_id=patient_id).first()
        
    @staticmethod
    def get_last_patient_by_year(year):
        """해당 연도의 마지막 환자 조회 (ID 생성용)"""
        return PatientCache.objects.filter(
            patient_id__startswith=f'P-{year}-'
        ).order_by('-patient_id').first()


class OrderRepository:
    """처방 데이터 저장소"""
    
    @staticmethod
    def create_order(order_data, items_data):
        """처방 및 처방 항목 생성 (Transaction 보장)"""
        with transaction.atomic():
            order = Order.objects.create(**order_data)
            
            for item_datum in items_data:
                OrderItem.objects.create(order=order, **item_datum)
                
            return order

    @staticmethod
    def get_last_order_by_year(year):
        """해당 연도의 마지막 처방 조회 (ID 생성용)"""
        return Order.objects.filter(
            order_id__startswith=f'O-{year}-'
        ).order_by('-order_id').first()
