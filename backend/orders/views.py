import redis
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Patient, Provider, Order, CarePlan

redis_client = redis.from_url(settings.REDIS_URL)
QUEUE_NAME = 'careplan_queue'


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

    care_plan = CarePlan.objects.create(order=order, status='pending')

    # Push care_plan id into Redis queue for later processing
    redis_client.lpush(QUEUE_NAME, care_plan.id)

    return Response({
        'id': order.id,
        'care_plan_id': care_plan.id,
        'patient_first_name': patient.first_name,
        'patient_last_name': patient.last_name,
        'patient_mrn': patient.mrn,
        'medication_name': order.medication_name,
        'status': care_plan.status,
        'care_plan': '',
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
