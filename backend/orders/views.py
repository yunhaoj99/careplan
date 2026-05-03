import anthropic
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Patient, Provider, Order, CarePlan


@api_view(['POST'])
def create_order(request):
    data = request.data

    patient, _ = Patient.objects.get_or_create(
        mrn=data.get('patient_mrn', ''),
        defaults={
            'first_name': data.get('patient_first_name', ''),
            'last_name': data.get('patient_last_name', ''),
            'dob': data.get('patient_dob', '2000-01-01'),
        },
    )

    provider, _ = Provider.objects.get_or_create(
        npi=data.get('provider_npi', ''),
        defaults={
            'name': data.get('provider_name', ''),
        },
    )

    order = Order.objects.create(
        patient=patient,
        provider=provider,
        medication_name=data.get('medication_name', ''),
        primary_diagnosis=data.get('primary_diagnosis', ''),
        additional_diagnoses=data.get('additional_diagnoses', ''),
        medication_history=data.get('medication_history', ''),
        patient_records=data.get('patient_records', ''),
    )

    care_plan = CarePlan.objects.create(order=order, status='processing')

    try:
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
        care_plan.content = message.content[0].text
        care_plan.status = 'completed'
    except Exception as e:
        care_plan.status = 'failed'
        care_plan.content = f"Failed to generate care plan: {e}"

    care_plan.save()

    return Response({
        'id': order.id,
        'patient_first_name': patient.first_name,
        'patient_last_name': patient.last_name,
        'patient_mrn': patient.mrn,
        'medication_name': order.medication_name,
        'status': care_plan.status,
        'care_plan': care_plan.content,
    }, status=201)


@api_view(['GET'])
def get_order(request, order_id):
    try:
        order = Order.objects.select_related('patient', 'provider', 'care_plan').get(id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)

    care_plan = getattr(order, 'care_plan', None)

    return Response({
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
    })
