from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from orders.models import Patient, Provider, Order, CarePlan


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
class TestCreateOrderAPI:

    def test_success_returns_201(self, client, order_data):
        with patch('orders.tasks.generate_care_plan') as mock_task:
            mock_task.delay.return_value = None
            resp = client.post('/api/orders/', order_data, format='json')

        assert resp.status_code == 201
        assert resp.data['status'] == 'pending'
        assert resp.data['patient_mrn'] == '000001'

    def test_provider_block_returns_409(self, client, order_data):
        Provider.objects.create(name='Dr. Original', npi='1234567890')

        resp = client.post('/api/orders/', order_data, format='json')

        assert resp.status_code == 409
        assert resp.data['type'] == 'block'
        assert resp.data['code'] == 'BLOCKED'
        assert 'Dr. Original' in resp.data['message']

    def test_patient_warning_returns_200(self, client, order_data):
        Provider.objects.create(name='Dr. Smith', npi='1234567890')
        Patient.objects.create(
            first_name='Jane', last_name='Doe', mrn='000001', dob='1990-05-15'
        )

        resp = client.post('/api/orders/', order_data, format='json')

        assert resp.status_code == 200
        assert resp.data['type'] == 'warning'
        assert resp.data['requires_confirmation'] is True
        assert len(resp.data['warnings']) > 0

    def test_patient_warning_with_confirm_returns_201(self, client, order_data):
        Provider.objects.create(name='Dr. Smith', npi='1234567890')
        Patient.objects.create(
            first_name='Jane', last_name='Doe', mrn='000001', dob='1990-05-15'
        )
        order_data['confirm'] = True

        with patch('orders.tasks.generate_care_plan') as mock_task:
            mock_task.delay.return_value = None
            resp = client.post('/api/orders/', order_data, format='json')

        assert resp.status_code == 201
        assert 'warnings' in resp.data

    def test_same_day_order_block_returns_409(self, client, order_data):
        patient = Patient.objects.create(
            first_name='John', last_name='Doe', mrn='000001', dob='1990-05-15'
        )
        provider = Provider.objects.create(name='Dr. Smith', npi='1234567890')
        Order.objects.create(
            patient=patient, provider=provider,
            medication_name='Lisinopril', primary_diagnosis='I10',
        )

        resp = client.post('/api/orders/', order_data, format='json')

        assert resp.status_code == 409
        assert resp.data['type'] == 'block'
        assert 'today' in resp.data['message']

    def test_same_name_dob_different_mrn_warning(self, client, order_data):
        Provider.objects.create(name='Dr. Smith', npi='1234567890')
        Patient.objects.create(
            first_name='John', last_name='Doe', mrn='999999', dob='1990-05-15'
        )

        resp = client.post('/api/orders/', order_data, format='json')

        assert resp.status_code == 200
        assert resp.data['type'] == 'warning'
        assert any('999999' in w for w in resp.data['warnings'])


@pytest.mark.django_db
class TestGetOrderAPI:

    def test_existing_order_returns_200(self, client):
        patient = Patient.objects.create(
            first_name='John', last_name='Doe', mrn='000001', dob='1990-05-15'
        )
        provider = Provider.objects.create(name='Dr. Smith', npi='1234567890')
        order = Order.objects.create(
            patient=patient, provider=provider,
            medication_name='Lisinopril', primary_diagnosis='I10',
        )
        CarePlan.objects.create(order=order, status='completed', content='Plan')

        resp = client.get(f'/api/orders/{order.id}/')

        assert resp.status_code == 200
        assert resp.data['patient_first_name'] == 'John'
        assert resp.data['status'] == 'completed'

    def test_nonexistent_order_returns_404(self, client):
        resp = client.get('/api/orders/99999/')

        assert resp.status_code == 404
        assert resp.data['type'] == 'error'
        assert resp.data['code'] == 'NOT_FOUND'


@pytest.mark.django_db
class TestCarePlanStatusAPI:

    def test_pending_returns_status_only(self, client):
        patient = Patient.objects.create(
            first_name='A', last_name='B', mrn='000001', dob='2000-01-01'
        )
        provider = Provider.objects.create(name='Dr. X', npi='1111111111')
        order = Order.objects.create(
            patient=patient, provider=provider,
            medication_name='Med', primary_diagnosis='Dx',
        )
        cp = CarePlan.objects.create(order=order, status='pending')

        resp = client.get(f'/api/careplan/{cp.id}/status/')

        assert resp.status_code == 200
        assert resp.data['status'] == 'pending'
        assert 'content' not in resp.data

    def test_completed_returns_content(self, client):
        patient = Patient.objects.create(
            first_name='A', last_name='B', mrn='000001', dob='2000-01-01'
        )
        provider = Provider.objects.create(name='Dr. X', npi='1111111111')
        order = Order.objects.create(
            patient=patient, provider=provider,
            medication_name='Med', primary_diagnosis='Dx',
        )
        cp = CarePlan.objects.create(order=order, status='completed', content='Full plan')

        resp = client.get(f'/api/careplan/{cp.id}/status/')

        assert resp.status_code == 200
        assert resp.data['content'] == 'Full plan'

    def test_nonexistent_careplan_returns_404(self, client):
        resp = client.get('/api/careplan/99999/status/')

        assert resp.status_code == 404
        assert resp.data['code'] == 'NOT_FOUND'
