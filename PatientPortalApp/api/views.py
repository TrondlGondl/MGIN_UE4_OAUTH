from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from PatientPortalApp.models import Patient, Practitioner, Medication, TreatmentPlan
from datetime import datetime#




# -------------------------
#  FHIR Patient Converter
# -------------------------
def patient_to_fhir(patient):
    return {
        "resourceType": "Patient",
        "id": str(patient.id),
        "identifier": [{
            "use": "official",
            "system": "https://myclinic.example/svnr",
            "value": patient.identifier_value
        }],
        "name": [{
            "use": "official",
            "family": patient.family_name,
            "given": [patient.given_name]
        }],
        "gender": patient.gender,
        "birthDate": patient.birth_date.strftime("%Y-%m-%d") if patient.birth_date else None,
        "address": [{
            "line": [patient.address_line] if patient.address_line else [],
            "city": patient.address_city,
            "postalCode": patient.address_postalcode,
            "country": patient.address_country
        }],
        "active": patient.user.is_active,
        "text": {
            "status": "generated",
            "div": (
                f"<div xmlns='http://www.w3.org/1999/xhtml'>"
                f"{patient.given_name} {patient.family_name}</div>"
            )
        }
    }


# -------------------------
#  Patient List / Create
# -------------------------
@csrf_exempt
def api_patient_list(request):

    # --- POST: Create Patient + User ---
    if request.method == "POST":
        data = json.loads(request.body)

        # 1. Extract FHIR fields
        identifier_value = data["identifier"][0]["value"]
        family_name = data["name"][0]["family"]
        given_name = data["name"][0]["given"][0]
        gender = data.get("gender", "unknown")
        birth_date = data.get("birthDate")

        address = data.get("address", [{}])[0]
        address_line = address.get("line", [""])[0]
        address_city = address.get("city")
        address_postalcode = address.get("postalCode")
        address_country = address.get("country")

        # Determine email
        email = None
        if "telecom" in data:
            for t in data["telecom"]:
                if t.get("system") == "email":
                    email = t.get("value")

        if email is None:
            email = f"{identifier_value}@auto.local"

        # 2. Check if user already exists
        try:
            user = User.objects.get(username=identifier_value)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=identifier_value,
                password="Password",
                email=email
            )
            user.is_active = False
            user.save()

        # 3. Check if patient already exists
        existing_patient = Patient.objects.filter(
            identifier_value=identifier_value
        ).first()

        if existing_patient:
            return JsonResponse(
                {"error": "Patient with this identifier already exists"},
                status=409
            )

        # 4. Create new patient
        birth_date_obj = None
        if birth_date:
            try:
                birth_date_obj = datetime.strptime(
                    birth_date, "%Y-%m-%d"
                ).date()
            except ValueError:
                return JsonResponse(
                    {"error": "Invalid birthDate format. Use YYYY-MM-DD."},
                    status=400
                )

        patient = Patient.objects.create(
            user=user,
            identifier_value=identifier_value,
            given_name=given_name,
            family_name=family_name,
            gender=gender,
            birth_date=birth_date_obj,
            address_line=address_line,
            address_city=address_city,
            address_postalcode=address_postalcode,
            address_country=address_country,
        )

        return JsonResponse(
            patient_to_fhir(patient),
            status=200,
            json_dumps_params={"indent": 2}
        )

    # --- GET / PUT / DELETE NOT ALLOWED ---
    return HttpResponse(status=405)




# -------------------------
#  Patient Detail / Update
# -------------------------
@csrf_exempt
def api_patient_detail(request, id):

    try:
        patient = Patient.objects.get(id=id)
    except Patient.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == "GET":
        return JsonResponse(patient_to_fhir(patient), json_dumps_params={"indent": 2})

    
    elif request.method == "PUT":
        data = json.loads(request.body)

        # --- Name ---
        if "name" in data and len(data["name"]) > 0:
            name = data["name"][0]
            patient.family_name = name.get("family", patient.family_name)
            if "given" in name and len(name["given"]) > 0:
                patient.given_name = name["given"][0]

        # --- Gender ---
        if "gender" in data:
            patient.gender = data["gender"]

        # --- Birth Date ---
        if "birthDate" in data:
            try:
                patient.birth_date = datetime.strptime(
                    data["birthDate"], "%Y-%m-%d"
                ).date()
            except ValueError:
                return JsonResponse(
                    {"error": "Invalid birthDate format (YYYY-MM-DD)"},
                    status=400
                )

        # --- Address ---
        if "address" in data and len(data["address"]) > 0:
            address = data["address"][0]
            patient.address_line = address.get("line", [patient.address_line])[0]
            patient.address_city = address.get("city", patient.address_city)
            patient.address_postalcode = address.get("postalCode", patient.address_postalcode)
            patient.address_country = address.get("country", patient.address_country)

        patient.save()

        return JsonResponse(patient_to_fhir(patient), json_dumps_params={"indent": 2})

    
    

    elif request.method == "DELETE":
        patient.delete()
        return HttpResponse(status=204)





#Medication

def medication_to_fhir(medication):
    return {
        "resourceType": "Medication",
        "id": str(medication.id),
        "status": medication.status,
        "code": {"text": medication.code},
    }

@csrf_exempt
def api_medication_list(request):
    # CREATE
    if request.method == "POST":
        try:
            data = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # FHIR: code.text ist Pflicht bei deinem Model
        code_text = (data.get("code") or {}).get("text")
        if not code_text:
            return JsonResponse(
                {"error": "Missing required field: code.text"},
                status=400
            )

        status = data.get("status", "active")

        medication = Medication.objects.create(
            code=code_text,
            status=status
        )

        return JsonResponse(medication_to_fhir(medication), status=200)

    return HttpResponse(status=405)


@csrf_exempt
def api_medication_detail(request, id):
    try:
        medication = Medication.objects.get(id=id)
    except Medication.DoesNotExist:
        return HttpResponse(status=404)

    # READ
    if request.method == "GET":
        return JsonResponse(medication_to_fhir(medication))

    # UPDATE
    if request.method == "PUT":
        try:
            data = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if "status" in data:
            medication.status = data["status"]

        if "code" in data and isinstance(data["code"], dict) and "text" in data["code"]:
            medication.code = data["code"]["text"]

        medication.save()
        return JsonResponse(medication_to_fhir(medication))

    # DELETE
    if request.method == "DELETE":
        medication.delete()
        return HttpResponse(status=204)

    return HttpResponse(status=405)









#Practitioner

def practitioner_to_fhir(practitioner):
    return {
        "resourceType": "Practitioner",
        "id": str(practitioner.id),
        "active": True,
        "name": [{
            "use": "official",
            "family": practitioner.user.last_name,
            "given": [practitioner.user.first_name]
        }],
        "qualification": [{
            "code": {
                "text": practitioner.specialization
            }
        }],
        "text": {
            "status": "generated",
            "div": (
                "<div xmlns='http://www.w3.org/1999/xhtml'>"
                f"{practitioner.user.get_full_name()}"
                "</div>"
            )
        }
    }



@csrf_exempt
def api_practitioner_list(request):

    if request.method == "POST":
        try:
            data = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # --- FHIR name ---
        name = (data.get("name") or [{}])[0]
        family = name.get("family", "")
        given_list = name.get("given") or []
        given = given_list[0] if given_list else ""

        # --- specialization from qualification.code.text ---
        qualification = (data.get("qualification") or [{}])[0]
        specialization = (
            (qualification.get("code") or {}).get("text")
            or "unknown"
        )

        # --- username ---
        username = None
        identifiers = data.get("identifier") or []
        if identifiers:
            username = identifiers[0].get("value")

        if not username:
            username = f"prac_{family.lower()}_{given.lower()}".strip("_")
            if not username:
                username = "practitioner_auto"

        # --- User erstellen ---
        user, created = User.objects.get_or_create(username=username)
        user.first_name = given
        user.last_name = family
        user.is_active = False
        if created:
            user.set_password("Password")
        user.save()

        practitioner = Practitioner.objects.create(
            user=user,
            specialization=specialization
        )

        return JsonResponse(
            practitioner_to_fhir(practitioner),
            status=200,
            json_dumps_params={"indent": 2}
        )

    return HttpResponse(status=405)


# -------------------------
#  Practitioner Detail CRUD
# -------------------------
@csrf_exempt
def api_practitioner_detail(request, id):

    try:
        practitioner = Practitioner.objects.get(id=id)
    except Practitioner.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == "GET":
        return JsonResponse(
            practitioner_to_fhir(practitioner),
            json_dumps_params={"indent": 2}
        )

    elif request.method == "PUT":
        try:
            data = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # --- Update name ---
        if "name" in data and data["name"]:
            name = data["name"][0]
            practitioner.user.last_name = name.get(
                "family", practitioner.user.last_name
            )

            given_list = name.get("given")
            if isinstance(given_list, list) and given_list:
                practitioner.user.first_name = given_list[0]

        # --- Update specialization ---
        if "qualification" in data and data["qualification"]:
            qual = data["qualification"][0]
            code = qual.get("code") or {}
            if "text" in code:
                practitioner.specialization = code["text"]

        practitioner.user.save()
        practitioner.save()

        return JsonResponse(
            practitioner_to_fhir(practitioner),
            json_dumps_params={"indent": 2}
        )

    elif request.method == "DELETE":
        practitioner.delete()
        return HttpResponse(status=204)

    return HttpResponse(status=405)




#Plan Definition bzw bei mir der Treatment Plan

def plandefinition_to_fhir(plan):
    return {
        "resourceType": "PlanDefinition",
        "id": str(plan.id),
        "status": "active",
        "title": plan.title,
        "description": plan.description,
        "subjectReference": {
            "reference": f"Patient/{plan.patient.id}"
        },
        "author": [
            {"name": f"Practitioner/{plan.practitioner.id}"}
        ],
        "text": {
            "status": "generated",
            "div": (
                "<div xmlns='http://www.w3.org/1999/xhtml'>"
                f"{plan.title}</div>"
            )
        }
    }







@csrf_exempt
def api_plandefinition_list(request):
    """
    POST /api/plandefinition/ -> create TreatmentPlan as FHIR PlanDefinition
    GET list disabled

    Expected (FHIR-friendly):
      - title (required)
      - description (optional)
      - subjectReference.reference = "Patient/{id}" (required)
      - author[0].name = "Practitioner/{id}" (recommended)

    Backwards compatible (optional):
      - contributor[0].type = "author"
      - contributor[0].name = "Practitioner/{id}"
    """

    if request.method != "POST":
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    title = data.get("title")
    description = data.get("description", "")

    if not title:
        return JsonResponse({"error": "Missing required field: title"}, status=400)

    # --- Patient reference ---
    subject_ref = (data.get("subjectReference") or {}).get("reference")
    if not subject_ref or not isinstance(subject_ref, str) or not subject_ref.startswith("Patient/"):
        return JsonResponse(
            {"error": "Missing/invalid subjectReference.reference. Use 'Patient/{id}'"},
            status=400
        )

    # --- Practitioner reference (prefer author[]) ---
    practitioner_ref = None

    author = data.get("author")
    if isinstance(author, list) and len(author) > 0:
        practitioner_ref = (author[0] or {}).get("name")

    # --- Fallback: contributor[] (old variant) ---
    if not practitioner_ref:
        contributor = data.get("contributor")
        if isinstance(contributor, list) and len(contributor) > 0:
            first = contributor[0] or {}
            if first.get("type") == "author":
                practitioner_ref = first.get("name")

    if (not practitioner_ref or not isinstance(practitioner_ref, str)
            or not practitioner_ref.startswith("Practitioner/")):
        return JsonResponse(
            {
                "error": (
                    "Missing/invalid practitioner reference. Provide either "
                    "author[0].name='Practitioner/{id}' (recommended) "
                    "or contributor[0]={type:'author', name:'Practitioner/{id}'}."
                )
            },
            status=400
        )

    # --- Parse IDs ---
    try:
        patient_id = int(subject_ref.split("/")[1])
        practitioner_id = int(practitioner_ref.split("/")[1])
    except (IndexError, ValueError):
        return JsonResponse(
            {"error": "Invalid reference format. Use 'Patient/{id}' and 'Practitioner/{id}'"},
            status=400
        )

    # --- Load FK objects ---
    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return JsonResponse({"error": "Patient not found"}, status=404)

    try:
        practitioner = Practitioner.objects.get(id=practitioner_id)
    except Practitioner.DoesNotExist:
        return JsonResponse({"error": "Practitioner not found"}, status=404)

    # --- Create TreatmentPlan ---
    plan = TreatmentPlan.objects.create(
        patient=patient,
        practitioner=practitioner,
        title=title,
        description=description
    )

    return JsonResponse(
        plandefinition_to_fhir(plan),
        status=200,
        json_dumps_params={"indent": 2}
    )





@csrf_exempt
def api_plandefinition_detail(request, id):

    try:
        plan = TreatmentPlan.objects.get(id=id)
    except TreatmentPlan.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == "GET":
        return JsonResponse(
            plandefinition_to_fhir(plan),
            json_dumps_params={"indent": 2}
        )

    elif request.method == "PUT":
        try:
            data = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # allow updating title/description
        if "title" in data:
            plan.title = data["title"]
        if "description" in data:
            plan.description = data["description"]

        # optional: allow re-assign patient/practitioner via references
        if "subject" in data and isinstance(data["subject"], dict):
            subject_ref = data["subject"].get("reference")
            if subject_ref and subject_ref.startswith("Patient/"):
                try:
                    patient_id = int(subject_ref.split("/")[1])
                    plan.patient = Patient.objects.get(id=patient_id)
                except (ValueError, Patient.DoesNotExist):
                    return JsonResponse({"error": "Invalid subject.reference / Patient not found"}, status=400)

        if "author" in data and isinstance(data["author"], list) and len(data["author"]) > 0:
            author_ref = (data["author"][0] or {}).get("reference")
            if author_ref and author_ref.startswith("Practitioner/"):
                try:
                    practitioner_id = int(author_ref.split("/")[1])
                    plan.practitioner = Practitioner.objects.get(id=practitioner_id)
                except (ValueError, Practitioner.DoesNotExist):
                    return JsonResponse({"error": "Invalid author.reference / Practitioner not found"}, status=400)

        plan.save()

        return JsonResponse(
            plandefinition_to_fhir(plan),
            json_dumps_params={"indent": 2}
        )

    elif request.method == "DELETE":
        plan.delete()
        return HttpResponse(status=204)

    return HttpResponse(status=405)
