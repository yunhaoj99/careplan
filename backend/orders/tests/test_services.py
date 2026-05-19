from unittest.mock import patch

import pytest

from orders.exceptions import BlockError, WarningException
from orders.models import Patient, Provider, Order, CarePlan
from orders import services


@pytest.mark.django_db
class TestProviderDuplicateDetection:

    def test_new_provider_is_created(self, order_data):
        with patch('orders.tasks.generate_care_plan') as mock_task:
            mock_task.delay.return_value = None
            services.create_order(order_data)

        assert Provider.objects.filter(npi='1234567890').exists()

    def test_same_npi_same_name_reuses_provider(self, order_data):
        Provider.objects.create(name='Dr. Smith', npi='1234567890')

        with patch('orders.tasks.generate_care_plan') as mock_task:
            mock_task.delay.return_value = None
            services.create_order(order_data)

        assert Provider.objects.filter(npi='1234567890').count() == 1

    def test_same_npi_different_name_raises_block(self, order_data):
        Provider.objects.create(name='Dr. Original', npi='1234567890')

        with pytest.raises(BlockError) as exc_info:
            services.create_order(order_data)

        assert 'Dr. Original' in exc_info.value.message
        assert 'Dr. Smith' in exc_info.value.message
        assert exc_info.value.detail['npi'] == '1234567890'


@pytest.mark.django_db
class TestPatientDuplicateDetection:

    def _create_provider(self):
        return Provider.objects.create(name='Dr. Smith', npi='1234567890')

    def test_new_patient_is_created(self, order_data):
        with patch('orders.tasks.generate_care_plan') as mock_task:
            mock_task.delay.return_value = None
            services.create_order(order_data)

        assert Patient.objects.filter(mrn='000001').exists()

    def test_same_mrn_same_info_reuses_patient(self, order_data):
        self._create_provider()
        Patient.objects.create(
            first_name='John', last_name='Doe', mrn='000001', dob='1990-05-15'
        )

        with patch('orders.tasks.generate_care_plan') as mock_task:
            mock_task.delay.return_value = None
            result = services.create_order(order_data)

        assert Patient.objects.filter(mrn='000001').count() == 1
        assert 'warnings' not in result

    def test_same_mrn_different_first_name_warns(self, order_data):
        self._create_provider()
        Patient.objects.create(
            first_name='Jane', last_name='Doe', mrn='000001', dob='1990-05-15'
        )

        with pytest.raises(WarningException) as exc_info:
            services.create_order(order_data)

        assert any("first_name" in w for w in exc_info.value.warnings)

    def test_same_mrn_different_last_name_warns(self, order_data):
        self._create_provider()
        Patient.objects.create(
            first_name='John', last_name='Smith', mrn='000001', dob='1990-05-15'
        )

        with pytest.raises(WarningException) as exc_info:
            services.create_order(order_data)

        assert any("last_name" in w for w in exc_info.value.warnings)

    def test_same_mrn_different_dob_warns(self, order_data):
        self._create_provider()
        Patient.objects.create(
            first_name='John', last_name='Doe', mrn='000001', dob='1999-12-31'
        )

        with pytest.raises(WarningException) as exc_info:
            services.create_order(order_data)

        assert any("dob" in w for w in exc_info.value.warnings)

    def test_same_name_dob_different_mrn_warns(self, order_data):
        self._create_provider()
        Patient.objects.create(
            first_name='John', last_name='Doe', mrn='999999', dob='1990-05-15'
        )

        with pytest.raises(WarningException) as exc_info:
            services.create_order(order_data)

        assert any("999999" in w for w in exc_info.value.warnings)

    def test_patient_warning_with_confirm_proceeds(self, order_data):
        self._create_provider()
        Patient.objects.create(
            first_name='Jane', last_name='Doe', mrn='000001', dob='1990-05-15'
        )
        order_data['confirm'] = True

        with patch('orders.tasks.generate_care_plan') as mock_task:
            mock_task.delay.return_value = None
            result = services.create_order(order_data)

        assert result['patient_first_name'] == 'Jane'
        assert 'warnings' in result


@pytest.mark.django_db
class TestOrderDuplicateDetection:

    def _setup_patient_provider(self):
        patient = Patient.objects.create(
            first_name='John', last_name='Doe', mrn='000001', dob='1990-05-15'
        )
        provider = Provider.objects.create(name='Dr. Smith', npi='1234567890')
        return patient, provider

    def test_same_patient_same_med_same_day_blocks(self, order_data):
        patient, provider = self._setup_patient_provider()
        Order.objects.create(
            patient=patient, provider=provider,
            medication_name='Lisinopril', primary_diagnosis='I10',
        )

        with pytest.raises(BlockError) as exc_info:
            services.create_order(order_data)

        assert 'Lisinopril' in exc_info.value.message
        assert 'today' in exc_info.value.message

    def test_same_patient_different_med_ok(self, order_data):
        patient, provider = self._setup_patient_provider()
        Order.objects.create(
            patient=patient, provider=provider,
            medication_name='Amlodipine', primary_diagnosis='I10',
        )

        with patch('orders.tasks.generate_care_plan') as mock_task:
            mock_task.delay.return_value = None
            result = services.create_order(order_data)

        assert result['medication_name'] == 'Lisinopril'

    def test_same_patient_same_med_different_day_warns(self, order_data):
        patient, provider = self._setup_patient_provider()
        old_order = Order.objects.create(
            patient=patient, provider=provider,
            medication_name='Lisinopril', primary_diagnosis='I10',
        )
        Order.objects.filter(id=old_order.id).update(created_at='2020-01-01')

        with pytest.raises(WarningException) as exc_info:
            services.create_order(order_data)

        assert any("previous order" in w for w in exc_info.value.warnings)

    def test_same_med_different_day_with_confirm_proceeds(self, order_data):
        patient, provider = self._setup_patient_provider()
        old_order = Order.objects.create(
            patient=patient, provider=provider,
            medication_name='Lisinopril', primary_diagnosis='I10',
        )
        Order.objects.filter(id=old_order.id).update(created_at='2020-01-01')
        order_data['confirm'] = True

        with patch('orders.tasks.generate_care_plan') as mock_task:
            mock_task.delay.return_value = None
            result = services.create_order(order_data)

        assert result['medication_name'] == 'Lisinopril'
        assert 'warnings' in result


@pytest.mark.django_db
class TestCreateOrderSuccess:

    def test_creates_order_and_careplan(self, order_data):
        with patch('orders.tasks.generate_care_plan') as mock_task:
            mock_task.delay.return_value = None
            result = services.create_order(order_data)

        assert result['status'] == 'pending'
        assert result['care_plan_id'] is not None
        assert CarePlan.objects.filter(id=result['care_plan_id']).exists()

    def test_triggers_celery_task(self, order_data):
        with patch('orders.tasks.generate_care_plan') as mock_task:
            mock_task.delay.return_value = None
            result = services.create_order(order_data)

        mock_task.delay.assert_called_once_with(result['care_plan_id'])


@pytest.mark.django_db
class TestGetOrderDetail:

    def test_returns_order_with_careplan(self):
        patient = Patient.objects.create(
            first_name='John', last_name='Doe', mrn='000001', dob='1990-05-15'
        )
        provider = Provider.objects.create(name='Dr. Smith', npi='1234567890')
        order = Order.objects.create(
            patient=patient, provider=provider,
            medication_name='Lisinopril', primary_diagnosis='I10',
        )
        CarePlan.objects.create(order=order, status='completed', content='Plan content')

        result = services.get_order_detail(order.id)

        assert result['patient_first_name'] == 'John'
        assert result['status'] == 'completed'
        assert result['care_plan'] == 'Plan content'

    def test_nonexistent_order_raises(self):
        with pytest.raises(Order.DoesNotExist):
            services.get_order_detail(99999)


@pytest.mark.django_db
class TestGetCarePlanStatus:

    def _create_careplan(self, status, content=''):
        patient = Patient.objects.create(
            first_name='A', last_name='B', mrn='000001', dob='2000-01-01'
        )
        provider = Provider.objects.create(name='Dr. X', npi='1111111111')
        order = Order.objects.create(
            patient=patient, provider=provider,
            medication_name='Med', primary_diagnosis='Dx',
        )
        return CarePlan.objects.create(order=order, status=status, content=content)

    def test_pending_returns_status_only(self):
        cp = self._create_careplan('pending')
        result = services.get_careplan_status(cp.id)

        assert result['status'] == 'pending'
        assert 'content' not in result

    def test_completed_returns_status_and_content(self):
        cp = self._create_careplan('completed', content='Full plan here')
        result = services.get_careplan_status(cp.id)

        assert result['status'] == 'completed'
        assert result['content'] == 'Full plan here'

    def test_failed_returns_status_and_content(self):
        cp = self._create_careplan('failed', content='Error: timeout')
        result = services.get_careplan_status(cp.id)

        assert result['status'] == 'failed'
        assert result['content'] == 'Error: timeout'

    def test_nonexistent_careplan_raises(self):
        with pytest.raises(CarePlan.DoesNotExist):
            services.get_careplan_status(99999)
