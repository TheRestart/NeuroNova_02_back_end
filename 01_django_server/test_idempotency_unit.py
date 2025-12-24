
import os
import django
import json
import uuid
from django.test import RequestFactory, TestCase
from django.http import JsonResponse
from rest_framework import status
from django.core.cache import cache

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
django.setup()

from cdss_backend.middleware import IdempotencyMiddleware

class IdempotencyMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.idempotency_key = str(uuid.uuid4())
        cache.clear()

    def dummy_view(self, request):
        # 성공적인 응답 반환 (JSON)
        return JsonResponse({"message": "Success", "key": str(uuid.uuid4())}, status=201)

    def test_idempotent_request(self):
        print("\n--- Testing Idempotency Middleware (Unit) ---")
        middleware = IdempotencyMiddleware(self.dummy_view)

        # 1. 첫 번째 요청
        request1 = self.factory.post('/api/test/', 
                                    data=json.dumps({"test": "data"}), 
                                    content_type='application/json',
                                    HTTP_X_IDEMPOTENCY_KEY=self.idempotency_key)
        request1.user = type('User', (), {'user_id': 'test_user'})() # Mock User
        
        response1 = middleware(request1)
        data1 = json.loads(response1.content)
        print(f"First request response: {data1}")

        # 2. 두 번째 요청 (동일한 키)
        request2 = self.factory.post('/api/test/', 
                                    data=json.dumps({"test": "data"}), 
                                    content_type='application/json',
                                    HTTP_X_IDEMPOTENCY_KEY=self.idempotency_key)
        request2.user = type('User', (), {'user_id': 'test_user'})() # Mock User
        
        response2 = middleware(request2)
        data2 = json.loads(response2.content)
        print(f"Second request response: {data2}")

        # 3. 결과 검증: 두 응답이 동일해야 함 (idempotency key에 의해 캐싱된 응답 반환)
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response2.status_code, 201)
        self.assertEqual(data1['key'], data2['key'])
        print("Idempotency Unit Test Passed!")

    def test_concurrent_idempotent_request(self):
        print("\n--- Testing Concurrent Idempotency Key Request ---")
        middleware = IdempotencyMiddleware(self.dummy_view)

        # 1. 멱등성 키 설정
        import hashlib
        user_id = 'test_user'
        path = '/api/test/'
        full_cache_key = f"idempotency_{hashlib.md5(f'{user_id}:{self.idempotency_key}:{path}'.encode()).hexdigest()}"
        
        # 2. 처리 중 상태로 설정
        cache.set(full_cache_key, 'PROCESSING', timeout=60)
        
        # 3. 요청 시도
        request = self.factory.post(path, 
                                   data=json.dumps({"test": "data"}), 
                                   content_type='application/json',
                                   HTTP_X_IDEMPOTENCY_KEY=self.idempotency_key)
        request.user = type('User', (), {'user_id': 'test_user'})() # Mock User
        
        response = middleware(request)
        print(f"Concurrent request status: {response.status_code}")
        
        self.assertEqual(response.status_code, 409)
        self.assertIn("already being processed", json.loads(response.content)['error'])
        print("Concurrent Idempotency Key Conflict Test Passed!")

if __name__ == "__main__":
    from django.test.utils import setup_test_environment
    setup_test_environment()
    t = IdempotencyMiddlewareTest()
    t.setUp()
    t.test_idempotent_request()
    t.test_concurrent_idempotent_request()
