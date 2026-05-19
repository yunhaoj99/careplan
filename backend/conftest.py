import pytest


VALID_ORDER_DATA = {
    'patient_first_name': 'John',
    'patient_last_name': 'Doe',
    'patient_mrn': '000001',
    'patient_dob': '1990-05-15',
    'provider_name': 'Dr. Smith',
    'provider_npi': '1234567890',
    'primary_diagnosis': 'I10 - Hypertension',
    'medication_name': 'Lisinopril',
    'additional_diagnoses': '',
    'medication_history': '',
    'patient_records': '',
}


@pytest.fixture
def order_data():
    return VALID_ORDER_DATA.copy()
