from django.db import models


class Patient(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    mrn = models.CharField(max_length=6, unique=True)
    dob = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (MRN: {self.mrn})"


class Provider(models.Model):
    name = models.CharField(max_length=200)
    npi = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (NPI: {self.npi})"


class Order(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='orders')
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='orders')
    medication_name = models.CharField(max_length=200)
    primary_diagnosis = models.CharField(max_length=200)
    additional_diagnoses = models.TextField(blank=True, default='')
    medication_history = models.TextField(blank=True, default='')
    patient_records = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id}: {self.medication_name} for {self.patient}"


class CarePlan(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='care_plan')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    content = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CarePlan for Order #{self.order_id} ({self.status})"
