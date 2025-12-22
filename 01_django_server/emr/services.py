
from datetime import datetime
from .repositories import PatientRepository, OrderRepository

class PatientService:
    """환자 비즈니스 로직"""
    
    @staticmethod
    def create_patient(data):
        """
        환자 생성 및 ID 자동 생성 (P-YYYY-NNNNNN)
        """
        year = datetime.now().year
        last_patient = PatientRepository.get_last_patient_by_year(year)
        
        if last_patient:
            last_number = int(last_patient.patient_id.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
            
        patient_id = f'P-{year}-{new_number:06d}'
        data['patient_id'] = patient_id
        
        return PatientRepository.create_patient(data)


class OrderService:
    """처방 비즈니스 로직"""
    
    @staticmethod
    def create_order(order_data, items_data):
        """
        처방 생성 및 ID 자동 생성 (O-YYYY-NNNNNN)
        처방 항목 ID 자동 생성 (OI-ORDERID-NNN)
        """
        year = datetime.now().year
        last_order = OrderRepository.get_last_order_by_year(year)
        
        if last_order:
            last_number = int(last_order.order_id.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
            
        order_id = f'O-{year}-{new_number:06d}'
        order_data['order_id'] = order_id
        
        # 항목 ID 생성 정책 적용
        final_items_data = []
        for idx, item in enumerate(items_data, 1):
            item_id = f'OI-{order_id}-{idx:03d}'
            item['item_id'] = item_id
            final_items_data.append(item)
            
        return OrderRepository.create_order(order_data, final_items_data)
