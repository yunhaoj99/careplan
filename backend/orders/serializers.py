from rest_framework import serializers


class OrderCreateSerializer(serializers.Serializer):
    patient_first_name = serializers.CharField()
    patient_last_name = serializers.CharField()
    patient_mrn = serializers.CharField()
    patient_dob = serializers.DateField()
    provider_name = serializers.CharField()
    provider_npi = serializers.CharField()
    primary_diagnosis = serializers.CharField()
    medication_name = serializers.CharField()
    additional_diagnoses = serializers.CharField(required=False, default='')
    medication_history = serializers.CharField(required=False, default='')
    patient_records = serializers.CharField(required=False, default='')


class OrderResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    care_plan_id = serializers.IntegerField()
    patient_first_name = serializers.CharField()
    patient_last_name = serializers.CharField()
    patient_mrn = serializers.CharField()
    medication_name = serializers.CharField()
    status = serializers.CharField()
    care_plan = serializers.CharField()


class OrderDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    patient_first_name = serializers.CharField()
    patient_last_name = serializers.CharField()
    patient_mrn = serializers.CharField()
    provider_name = serializers.CharField()
    provider_npi = serializers.CharField()
    medication_name = serializers.CharField()
    primary_diagnosis = serializers.CharField()
    status = serializers.CharField()
    care_plan = serializers.CharField()


class CarePlanStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    content = serializers.CharField(required=False)
