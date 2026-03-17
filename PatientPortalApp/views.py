from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpRequest
from PatientPortalApp.models import Patient, Practitioner, Questionaire_Template
from datetime import datetime
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import AbstractUser
from .models import Practitioner, Patient, TreatmentPlan, Message



def perform_register(request):  # nur Patienten Registrierung
    registration_status = ""

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        svnr = request.POST.get("svnr")

        given_name = request.POST.get("given_name")
        family_name = request.POST.get("family_name")
        gender = request.POST.get("gender")
        birth_date = request.POST.get("birthday")

        address_line = request.POST.get("address_line")
        address_city = request.POST.get("address_city")
        address_postalcode = request.POST.get("address_postalcode")
        address_country = request.POST.get("address_country")

        # Validierung
        if not all([username, password, email, svnr, given_name, family_name, gender, birth_date]):
            registration_status = "Bitte fülle alle Pflichtfelder aus."
        elif User.objects.filter(username=username).exists():
            registration_status = "Benutzername existiert bereits."
        else:
            # User erstellen
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email
            )
            user.is_active = False
            user.save()

            # Patient erstellen (FHIR-konform)
            Patient.objects.create(
                user=user,
                SVNR=svnr,
                identifier_value=svnr,
                given_name=given_name,
                family_name=family_name,
                gender=gender,
                birth_date=birth_date,
                address_line=address_line,
                address_city=address_city,
                address_postalcode=address_postalcode,
                address_country=address_country,
            )

            registration_status = (
                "Registrierung erfolgreich! Dein Konto muss von einem Admin aktiviert werden."
            )

    return render(
        request,
        "register.html",
        {
            "registration_status": registration_status,
        },
    )



def perform_register_practitioner(request):
    registration_status = ""

    if request.method == "POST":
        username = request.POST.get("username").strip()
        password = request.POST.get("password").strip()
        email = request.POST.get("email").strip()
        specialization = request.POST.get("specialization").strip()

        # Eingabeprüfung
        if not username or not password or not email or not specialization:
            registration_status = "Bitte fülle alle Felder aus."
        elif User.objects.filter(username=username).exists():
            registration_status = "Benutzername existiert bereits."
        elif User.objects.filter(email=email).exists():
            registration_status = "E-Mail-Adresse ist bereits registriert."
        else:
            # User erstellen
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=request.POST.get("first_name", "").strip(),
                last_name=request.POST.get("last_name", "").strip()
            )
            user.is_active = False  # muss von Admin aktiviert werden
            user.save()

            # Practitioner erstellen
            Practitioner.objects.create(
                user=user,
                specialization=specialization
            )

            registration_status = (
                "Registrierung erfolgreich! Dein Konto muss von einem Admin aktiviert werden."
            )

    return render(
        request,
        "register_staff.html",
        {"registration_status": registration_status},
    )



def perform_login(request: HttpRequest): 
    login_status = ""
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user: AbstractUser | None = authenticate(request, username=username, password = password)
        
        
        if user is not None:
            login(request, user)
            login_status = "SUCCESFULL" 
            return redirect("/dashboard")  #wird direkt umgeleitet zum Dashboard
        else:
            login_status = "Failed"
    
    


    return render(request, "login.html", context={"login_status": login_status})


def perform_logout(request: HttpRequest): 
    logout(request)
    return redirect("/login")


# def dashboard(request: HttpRequest):
   
#     return render(request, "dashboard.html")


def practitioner_assigned(request: HttpRequest):
    
    if(Patient.practitioner is not None):
        practitioner = None

    else: 
        practitioner = Patient.practitioner


    return render(request, "login.html", context={"login_status": practitioner})




def dashboard(request):
    user = request.user

    # Wenn niemand eingeloggt ist
    if not user.is_authenticated:
        return render(request, "dashboard.html", {"error": "❌ Sie sind nicht angemeldet. Bitte loggen Sie sich zuerst ein."})

    status_message = None
    practitioners = Practitioner.objects.all()
    patients = Patient.objects.all()
    practitioner_patients = None
    patient_fragebogen = None
    assigned_practitioner = None
    treatment_plan = None
    messages_between = None

    # ------------------ ADMIN DASHBOARD ------------------
    if user.is_superuser:
        if request.method == "POST" and "practitioner_id" in request.POST:
            practitioner_id = request.POST.get("practitioner_id")
            patient_id = request.POST.get("patient_id")

            practitioner = Practitioner.objects.filter(id=practitioner_id).first()
            patient = Patient.objects.filter(id=patient_id).first()

            if practitioner and patient:
                patient.practitioner = practitioner
                patient.save()
                status_message = f" {patient.user.username} wurde {practitioner.user.username} zugewiesen."
            else:
                status_message = " Ungültige Auswahl."

    # ------------------ PRACTITIONER DASHBOARD ------------------
    elif user.is_staff:
        practitioner = Practitioner.objects.filter(user=user).first()               #Patienten abrufen
        practitioner_patients = Patient.objects.filter(practitioner=practitioner)

        # Behandlungsplan speichern
        if request.method == "POST" and "assign_plan" in request.POST:
            patient_id = request.POST.get("patient_id")
            plan_text = request.POST.get("treatment_plan")
            patient = Patient.objects.filter(id=patient_id, practitioner=practitioner).first()
            if patient:
                patient.treatment_plan = plan_text
                patient.save()
                status_message = f" Behandlungsplan für {patient.user.username} gespeichert."

        # Nachricht senden
        if request.method == "POST" and "send_message" in request.POST:
            receiver_id = request.POST.get("receiver_id")
            msg_content = request.POST.get("message_text")
            if receiver_id and msg_content.strip():
                receiver = User.objects.filter(id=receiver_id).first()
                if receiver:
                    Message.objects.create(sender=user, receiver=receiver, content=msg_content)

        # Nachrichten mit eigenen Patienten laden
        patient_user_ids = practitioner_patients.values_list("user", flat=True)
        messages_between = Message.objects.filter(
            sender__in=list(patient_user_ids) + [user.id],
            receiver__in=list(patient_user_ids) + [user.id]
        ).order_by("timestamp")

    # ------------------ PATIENT DASHBOARD ------------------
    elif user.is_authenticated:
        patient = Patient.objects.filter(user=user).first()
        if not patient:
            return render(request, "dashboard.html", {"error": " Kein Patientenkonto gefunden."})

        patient_fragebogen = patient.questionare_completed          #Daten anzeigen (Behandlungsplan und Fragebogen)
        assigned_practitioner = patient.practitioner 
        treatment_plan = getattr(patient, "treatment_plan", None)

        # Nachricht an Practitioner senden
        if assigned_practitioner and request.method == "POST" and "send_message" in request.POST:
            msg_content = request.POST.get("message_text")
            if msg_content.strip():
                Message.objects.create(sender=user, receiver=assigned_practitioner.user, content=msg_content)

        # Chat laden (Patient ↔ Practitioner)
        if assigned_practitioner:
            messages_between = Message.objects.filter(
                sender__in=[user, assigned_practitioner.user],
                receiver__in=[user, assigned_practitioner.user]
            ).order_by("timestamp")

    return render(
        request,
        "dashboard.html",
        {
            "practitioners": practitioners,
            "patients": patients,
            "status_message": status_message,
            "practitioner_patients": practitioner_patients,
            "patient_fragebogen": patient_fragebogen,
            "assigned_practitioner": assigned_practitioner,
            "treatment_plan": treatment_plan,
            "messages_between": messages_between,
        },
    )



def fill_questionaire(request):
    # Prüfen, ob Benutzer eingeloggt ist
    if not request.user.is_authenticated:
        return redirect("login")

    # Patient holen
    patient = Patient.objects.filter(user=request.user).first()
    if not patient:
        return redirect("dashboard")  # Nur Patienten dürfen Fragebogen ausfüllen

    # Aktives Template holen
    template = Questionaire_Template.objects.filter(is_active=True).order_by('-version').first()
    if not template:
        return render(request, "questionaire.html", {"error": "Kein aktiver Fragebogen vorhanden."})

    # POST -> Antworten speichern
    if request.method == "POST":
        answers = {}
        for i, question in enumerate(template.questions):
            selected_answer = request.POST.get(f"question_{i}")
            if selected_answer:
                answers[question["question"]] = selected_answer

        # Antworten speichern
        patient.questionare_data = answers
        patient.questionare_completed = True
        patient.save()

        return redirect("dashboard")

    # GET -> Formular anzeigen
    return render(request, "questionaire.html", {"template": template})


def home_redirect(request):
    return redirect("login/")


def edit_patient(request):
    edit_status = ""

    if request.method == "POST":
        user = get_object_or_404(User, pk=request.user.pk)
        patient = get_object_or_404(Patient, user=user)

        # Nur die Felder aktualisieren, die im POST vorhanden sind
        username = request.POST.get("username")
        if username:
            user.username = username

        email = request.POST.get("email")
        if email:
            user.email = email

        password = request.POST.get("password")
        if password:
            user.set_password(password)  # wichtig: Passwort hashen

        # User speichern, falls sich etwas geändert hat
        user.save()
        #Dasselbe für den Patienten nochmal
        svnr = request.POST.get("svnr")
        if svnr:
            patient.SVNR = svnr

        birthday_str = request.POST.get("birthday")
        if birthday_str:
            patient.birthday = birthday_str

        patient.save()

        edit_status = "Die Änderungen wurden erfolgreich übernommen."

    return render(request, "edit.html", {"registration_status": edit_status})