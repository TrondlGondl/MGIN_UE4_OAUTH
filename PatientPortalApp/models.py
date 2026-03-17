from django.db import models
from django.contrib.auth.models import User

class Practitioner(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)


class Patient(models.Model):
    id = models.AutoField(primary_key=True)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
  
    practitioner = models.ForeignKey(
        "Practitioner",
        null=True,
        on_delete=models.SET_NULL,
        related_name="patients"
    )
    
    questionare_completed = models.BooleanField(default=False)
    questionare_data = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateField(null=True)
    
    identifier_system = models.CharField(
        max_length=200,
        default="https://myclinic.example/patient-id"
    )
    identifier_value = models.CharField(
        max_length=50,
        unique=True
    )
    
    family_name = models.CharField(max_length=100)
    given_name = models.CharField(max_length=100)
    # FHIR: gender
    gender = models.CharField(
        max_length=10,
        choices=[("male","male"), ("female","female"), ("other","other"), ("unknown","unknown")],
        default="unknown"
    )
    # FHIR: birthDate
    birth_date = models.DateTimeField()
    # FHIR: address
    address_line = models.CharField(max_length=255,  blank=True, default=0)
    address_city = models.CharField(max_length=100,  blank=True,default=0)
    address_postalcode = models.CharField(max_length=20, blank=True, default=0)
    address_country = models.CharField(max_length=100,  blank=True, default=0)
    # Lokale Felder (aus deinem Projekt)
    SVNR = models.CharField(max_length=11)
    treatment_plan = models.TextField(null=True, blank=True)


class Questionaire_Template(models.Model):
    questions = models.JSONField()
    version = models.IntegerField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class TreatmentPlan(models.Model):
    practitioner = models.ForeignKey("Practitioner", on_delete=models.CASCADE)
    patient = models.ForeignKey("Patient", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Plan für {self.patient.user.username} von {self.practitioner.user.username}"

class Message(models.Model):
    sender = models.ForeignKey(User, related_name="sent_messages", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="received_messages", on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nachricht von {self.sender.username} an {self.receiver.username}"

class Medication(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=200)   # z.B. Wirkstoff / Handelsname
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "active"),
            ("inactive", "inactive"),
            ("entered-in-error", "entered-in-error")
        ],
        default="active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
