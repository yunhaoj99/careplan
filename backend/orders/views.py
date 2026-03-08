import uuid

import anthropic
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

# MVP: in-memory storage — restarts lose all data (Day 3 adds a real database)
orders_db = {}


@api_view(['POST'])
def create_order(request):
    data = request.data
    order_id = str(uuid.uuid4())[:8]

    order = {
        'id': order_id,
        'patient_first_name': data.get('patient_first_name', ''),
        'patient_last_name': data.get('patient_last_name', ''),
        'patient_mrn': data.get('patient_mrn', ''),
        'patient_dob': data.get('patient_dob', ''),
        'provider_name': data.get('provider_name', ''),
        'provider_npi': data.get('provider_npi', ''),
        'primary_diagnosis': data.get('primary_diagnosis', ''),
        'medication_name': data.get('medication_name', ''),
        'additional_diagnoses': data.get('additional_diagnoses', ''),
        'medication_history': data.get('medication_history', ''),
        'patient_records': data.get('patient_records', ''),
        'status': 'processing',
        'care_plan': None,
    }

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        prompt = f"""You are a clinical pharmacist. Generate a comprehensive pharmaceutical care plan based on the following patient information.

Patient: {order['patient_first_name']} {order['patient_last_name']}
MRN: {order['patient_mrn']}
DOB: {order['patient_dob']}
Primary Diagnosis: {order['primary_diagnosis']}
Additional Diagnoses: {order['additional_diagnoses']}
Current Medication: {order['medication_name']}
Medication History: {order['medication_history']}
Patient Records/Notes: {order['patient_records']}

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
        order['care_plan'] = message.content[0].text
        order['status'] = 'completed'
    except Exception as e:
        order['status'] = 'failed'
        order['care_plan'] = f"Failed to generate care plan: {e}"

    orders_db[order_id] = order
    return Response(order, status=201)


@api_view(['GET'])
def get_order(request, order_id):
    order = orders_db.get(order_id)
    if not order:
        return Response({'error': 'Order not found'}, status=404)
    return Response(order)
