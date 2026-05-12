import time

import anthropic
from django.conf import settings

from .models import Patient, Provider, Order, CarePlan


# ── Order creation ──

def create_order(validated_data):
    patient, _ = Patient.objects.get_or_create(
        mrn=validated_data['patient_mrn'],
        defaults={
            'first_name': validated_data['patient_first_name'],
            'last_name': validated_data['patient_last_name'],
            'dob': validated_data['patient_dob'],
        },
    )

    provider, _ = Provider.objects.get_or_create(
        npi=validated_data['provider_npi'],
        defaults={
            'name': validated_data['provider_name'],
        },
    )

    order = Order.objects.create(
        patient=patient,
        provider=provider,
        medication_name=validated_data['medication_name'],
        primary_diagnosis=validated_data['primary_diagnosis'],
        additional_diagnoses=validated_data.get('additional_diagnoses', ''),
        medication_history=validated_data.get('medication_history', ''),
        patient_records=validated_data.get('patient_records', ''),
    )

    care_plan = CarePlan.objects.create(order=order, status='pending')

    from .tasks import generate_care_plan
    generate_care_plan.delay(care_plan.id)

    return {
        'id': order.id,
        'care_plan_id': care_plan.id,
        'patient_first_name': patient.first_name,
        'patient_last_name': patient.last_name,
        'patient_mrn': patient.mrn,
        'medication_name': order.medication_name,
        'status': care_plan.status,
        'care_plan': '',
    }


# ── Order query ──

def get_order_detail(order_id):
    order = Order.objects.select_related('patient', 'provider', 'care_plan').get(id=order_id)
    care_plan = getattr(order, 'care_plan', None)

    return {
        'id': order.id,
        'patient_first_name': order.patient.first_name,
        'patient_last_name': order.patient.last_name,
        'patient_mrn': order.patient.mrn,
        'provider_name': order.provider.name,
        'provider_npi': order.provider.npi,
        'medication_name': order.medication_name,
        'primary_diagnosis': order.primary_diagnosis,
        'status': care_plan.status if care_plan else 'no care plan',
        'care_plan': care_plan.content if care_plan else '',
    }


# ── CarePlan status query ──

def get_careplan_status(careplan_id):
    care_plan = CarePlan.objects.get(id=careplan_id)
    data = {'status': care_plan.status}
    if care_plan.status in ('completed', 'failed'):
        data['content'] = care_plan.content
    return data


# ── LLM calling (moved from tasks.py) ──

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


def generate_llm_care_plan(patient, order):
    if settings.USE_MOCK_LLM:
        return call_mock_llm(patient, order)
    return call_real_llm(patient, order)
