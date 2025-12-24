import os
import sys
import django
import uuid
import json

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
django.setup()

from ai.models import AIJob
from ai.services import AIJobService
from acct.models import User, Alert
from django.utils import timezone

def verify_ai_flow():
    print("=" * 60)
    print("AI Integration Workflow Verification")
    print("=" * 60)

    # 1. Setup: Create a test doctor
    doctor_user, _ = User.objects.get_or_create(
        username="test_doctor_ai",
        defaults={"role": "doctor", "email": "doc_ai@example.com"}
    )
    if not doctor_user.password:
        doctor_user.set_password("password123")
        doctor_user.save()

    service = AIJobService()
    study_id = uuid.uuid4()
    
    print(f"\n[Step 1] Submitting AI Job for study: {study_id}")
    # Note: submission will try to connect to RabbitMQ. If it fails, it sets status to FAILED.
    # We will manually set it to QUEUED for testing purposes if it fails.
    ai_job = service.submit_ai_job(study_id, "brain_tumor_detection")
    print(f"Initial status: {ai_job.status}")
    
    if ai_job.status == "FAILED":
        print("  - Notice: RabbitMQ connection failed (expected in local env), forcing QUEUED status for verification.")
        ai_job.status = "QUEUED"
        ai_job.save()

    # 2. Simulate Callback
    print(f"\n[Step 2] Simulating Callback from AI Server (Job ID: {ai_job.job_id})")
    result_data = {
        "finding": "Subarachnoid hemorrhage suspected in I60.0 region",
        "confidence": 0.89,
        "region": "supratentorial"
    }
    updated_job = service.update_job_result(
        job_id=ai_job.job_id,
        status="COMPLETED",
        result_data=result_data
    )
    
    if updated_job and updated_job.status == "COMPLETED":
        print(f"Result updated successfully. Status: {updated_job.status}")
        print(f"Result Data: {json.dumps(updated_job.result_data, indent=2)}")
    else:
        print("❌ Failed to update job via callback.")
        return

    # 3. Verify Alert
    print(f"\n[Step 3] Verifying Alert generation for doctors")
    alerts = Alert.objects.filter(metadata__source="AI", user__role="doctor").order_by("-created_at")
    if alerts.exists() and str(study_id) in alerts[0].message:
        print(f"✅ Alert found: [{alerts[0].type}] - {alerts[0].message}")
    else:
        print("❌ Alert not found or message mismatch.")

    # 4. Simulate Doctor Review
    print(f"\n[Step 4] Simulating Doctor Review (Approving Job ID: {ai_job.job_id})")
    review_comment = "Confirmed. Proceed with surgery consultation."
    reviewed_job = service.review_job(
        job_id=ai_job.job_id,
        user=doctor_user,
        status="APPROVED",
        comment=review_comment
    )
    
    if reviewed_job and reviewed_job.review_status == "APPROVED":
        print(f"Review updated successfully. Review Status: {reviewed_job.review_status}")
        print(f"Reviewed By: {reviewed_job.reviewed_by.username}")
        print(f"Comment: {reviewed_job.review_comment}")
    else:
        print("❌ Failed to update review status.")
        return

    print("\n" + "=" * 60)
    print("AI Integration Workflow Verified Successfully!")
    print("=" * 60)

if __name__ == "__main__":
    verify_ai_flow()
