import time

import anthropic
from celery import shared_task
from django.conf import settings


def call_real_llm(patient, order):
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

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

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def call_mock_llm(patient, order):
    time.sleep(3)
    return f"""# Mock Care Plan

**Patient:** {patient.first_name} {patient.last_name}
**MRN:** {patient.mrn}
**Medication:** {order.medication_name}
**Diagnosis:** {order.primary_diagnosis}

## 1. Problem List / Drug Therapy Problems (DTPs)
- DTP #1: Need for {order.medication_name} therapy management
- DTP #2: Potential drug interactions to monitor
- DTP #3: Adherence assessment needed

## 2. Goals (SMART)
- Achieve therapeutic response within 4-8 weeks
- Maintain medication adherence > 90% over 6 months
- Monitor and prevent adverse effects throughout treatment

## 3. Pharmacist Interventions / Plan
- Verify dosing and adjust based on renal/hepatic function
- Provide patient counseling on medication use and side effects
- Coordinate with prescriber for follow-up labs

## 4. Monitoring Plan & Lab Schedule
- Baseline: CBC, CMP, LFTs
- Month 1: Follow-up labs and symptom assessment
- Month 3: Efficacy evaluation and dose adjustment if needed
- Ongoing: Adverse effect monitoring at each visit

---
*[MOCK] This is a mock care plan generated for development/testing purposes.*"""


@shared_task(bind=True, max_retries=3)
def generate_care_plan(self, care_plan_id):
    from .models import CarePlan

    care_plan = CarePlan.objects.select_related('order__patient').get(id=care_plan_id)
    order = care_plan.order
    patient = order.patient

    care_plan.status = 'processing'
    care_plan.save()

    try:
        if settings.USE_MOCK_LLM:
            care_plan.content = call_mock_llm(patient, order)
        else:
            care_plan.content = call_real_llm(patient, order)

        care_plan.status = 'completed'
        care_plan.save()
        return f"CarePlan #{care_plan_id} completed ({'mock' if settings.USE_MOCK_LLM else 'real'})"

    except Exception as exc:
        if self.request.retries < self.max_retries:
            countdown = 2 ** (self.request.retries + 1)
            care_plan.status = 'pending'
            care_plan.save()
            raise self.retry(exc=exc, countdown=countdown)

        care_plan.status = 'failed'
        care_plan.content = f"Failed after {self.max_retries} retries: {exc}"
        care_plan.save()
        return f"CarePlan #{care_plan_id} failed"
