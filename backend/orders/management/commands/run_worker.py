import time
import redis
import anthropic
from django.conf import settings
from django.core.management.base import BaseCommand
from orders.models import CarePlan

QUEUE_NAME = 'careplan_queue'


class Command(BaseCommand):
    help = 'Worker that pulls care plan tasks from Redis and calls LLM to generate them'

    def handle(self, *args, **options):
        redis_client = redis.from_url(settings.REDIS_URL)
        llm_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        self.stdout.write("Worker started. Waiting for tasks...")

        while True:
            # brpop blocks until a message arrives — no polling, no wasted queries
            result = redis_client.brpop(QUEUE_NAME, timeout=0)

            care_plan_id = int(result[1])
            self.stdout.write(f"\nReceived care_plan_id={care_plan_id}")

            try:
                care_plan = CarePlan.objects.select_related('order__patient').get(id=care_plan_id)
            except CarePlan.DoesNotExist:
                self.stderr.write(f"  CarePlan {care_plan_id} not found, skipping.")
                continue

            order = care_plan.order
            patient = order.patient

            care_plan.status = 'processing'
            care_plan.save()
            self.stdout.write(f"  Processing: {order.medication_name} for {patient.first_name} {patient.last_name}")

            try:
                prompt = f"""You are a clinical pharmacist. Generate a comprehensive pharmaceutical care plan based on the following patient information.

Patient: {patient.first_name} {patient.last_name}
MRN: {patient.mrn}
DOB: {patient.dob}
Primary Diagnosis: {order.primary_diagnosis}
Additional Diagnoses: {order.additional_diagnoses}
Current Medication: {order.medication_name}
Medication History: {order.medication_history}
Patient Records/Notes: {order.patient_records}

Generate the care plan with EXACTLY these four sections:

1. Problem List / Drug Therapy Problems (DTPs)
2. Goals (SMART - Specific, Measurable, Achievable, Relevant, Time-bound)
3. Pharmacist Interventions / Plan
4. Monitoring Plan & Lab Schedule

Be clinically specific. Include dosing considerations, potential drug interactions, and evidence-based recommendations."""

                start = time.time()
                message = llm_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )
                elapsed = time.time() - start

                care_plan.content = message.content[0].text
                care_plan.status = 'completed'
                care_plan.save()
                self.stdout.write(self.style.SUCCESS(f"  Completed in {elapsed:.1f}s"))

            except Exception as e:
                care_plan.status = 'failed'
                care_plan.content = f"Failed to generate care plan: {e}"
                care_plan.save()
                self.stderr.write(self.style.ERROR(f"  Failed: {e}"))
