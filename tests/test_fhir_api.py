import json
import pytest

from tests.fhir_schema import validate_fhir_resource

pytestmark = pytest.mark.django_db


def _json(resp):
    return json.loads(resp.content.decode("utf-8"))


# -------------------------
# Patient CRUD + Schema
# -------------------------
def test_patient_crud_and_schema(client):
    patient_body = {
        "resourceType": "Patient",
        "identifier": [{
            "use": "official",
            "system": "https://myclinic.example/svnr",
            "value": "p-001"
        }],
        "name": [{
            "family": "Mustermann",
            "given": ["Max"]
        }],
        "gender": "male",
        "birthDate": "2000-01-01",
        "address": [{
            "line": ["Teststraße 1"],
            "city": "Wien",
            "postalCode": "1010",
            "country": "AT"
        }]
    }

    
    r = client.post("/api/patient/", data=json.dumps(patient_body), content_type="application/json")
    assert r.status_code == 200
    created = _json(r)
    validate_fhir_resource(created, "Patient")
    pid = created["id"]

    r = client.get(f"/api/patient/{pid}/")
    assert r.status_code == 200
    got = _json(r)
    validate_fhir_resource(got, "Patient")
    assert got["id"] == str(pid)

    update_body = {
        "resourceType": "Patient",
        "name": [{
            "family": "Mustermann",
            "given": ["Maximilian"]
        }]
    }
    r = client.put(f"/api/patient/{pid}/", data=json.dumps(update_body), content_type="application/json")
    assert r.status_code == 200
    updated = _json(r)
    validate_fhir_resource(updated, "Patient")
    assert updated["name"][0]["given"][0] == "Maximilian"

    r = client.delete(f"/api/patient/{pid}/")
    assert r.status_code == 204

    r = client.get(f"/api/patient/{pid}/")
    assert r.status_code == 404


# -------------------------
# Practitioner CRUD + Schema
# -------------------------
def test_practitioner_crud_and_schema(client):
    body = {
        "resourceType": "Practitioner",
        "identifier": [{
            "system": "https://myclinic.example/practitioner-id",
            "value": "prac-001"
        }],
        "name": [{
            "family": "Mayer",
            "given": ["Anna"]
        }],
        "qualification": [{
            "code": {"text": "Psychotherapie"}
        }]
    }

    
    r = client.post("/api/practitioner/", data=json.dumps(body), content_type="application/json")
    assert r.status_code == 200
    created = _json(r)
    validate_fhir_resource(created, "Practitioner")
    prid = created["id"]

    r = client.get(f"/api/practitioner/{prid}/")
    assert r.status_code == 200
    got = _json(r)
    validate_fhir_resource(got, "Practitioner")

    update_body = {
        "resourceType": "Practitioner",
        "qualification": [{
            "code": {"text": "Klinische Psychologie"}
        }]
    }
    r = client.put(f"/api/practitioner/{prid}/", data=json.dumps(update_body), content_type="application/json")
    assert r.status_code == 200
    updated = _json(r)
    validate_fhir_resource(updated, "Practitioner")
    assert updated["qualification"][0]["code"]["text"] == "Klinische Psychologie"

    r = client.delete(f"/api/practitioner/{prid}/")
    assert r.status_code == 204

    r = client.get(f"/api/practitioner/{prid}/")
    assert r.status_code == 404


# -------------------------
# Medication CRUD + Schema
# -------------------------
def test_medication_crud_and_schema(client):
    body = {
        "resourceType": "Medication",
        "status": "active",
        "code": {"text": "Ibuprofen 400mg"}
    }

    
    r = client.post("/api/medication/", data=json.dumps(body), content_type="application/json")
    assert r.status_code == 200
    created = _json(r)
    validate_fhir_resource(created, "Medication")
    mid = created["id"]

    r = client.get(f"/api/medication/{mid}/")
    assert r.status_code == 200
    got = _json(r)
    validate_fhir_resource(got, "Medication")

    update_body = {
        "resourceType": "Medication",
        "status": "inactive",
        "code": {"text": "Ibuprofen 600mg"}
    }
    r = client.put(f"/api/medication/{mid}/", data=json.dumps(update_body), content_type="application/json")
    assert r.status_code == 200
    updated = _json(r)
    validate_fhir_resource(updated, "Medication")
    assert updated["status"] == "inactive"

    
    r = client.delete(f"/api/medication/{mid}/")
    assert r.status_code == 204

    r = client.get(f"/api/medication/{mid}/")
    assert r.status_code == 404


# -------------------------
# PlanDefinition (TreatmentPlan) CRUD + Schema
# -------------------------
def test_plandefinition_crud_and_schema(client):
    # Practitioner create (POST -> 200)
    pr_body = {
        "resourceType": "Practitioner",
        "identifier": [{"system": "https://myclinic.example/practitioner-id", "value": "prac-100"}],
        "name": [{"family": "TestDoc", "given": ["Tina"]}],
        "qualification": [{"code": {"text": "Allgemeinmedizin"}}]
    }
    r = client.post("/api/practitioner/", data=json.dumps(pr_body), content_type="application/json")
    assert r.status_code == 200
    pr = _json(r)
    validate_fhir_resource(pr, "Practitioner")
    practitioner_id = pr["id"]

    # Patient create (POST -> 200)
    pa_body = {
    "resourceType": "Patient",
    "identifier": [{"use": "official", "system": "https://myclinic.example/svnr", "value": "p-100"}],
    "name": [{"family": "Plan", "given": ["Paul"]}],
    "gender": "male",
    "birthDate": "1999-01-01",
    "address": [{
        "line": ["Testgasse 1"],
        "city": "Wien",
        "postalCode": "1010",
        "country": "AT"
    }]
}

    r = client.post("/api/patient/", data=json.dumps(pa_body), content_type="application/json")
    assert r.status_code == 200
    pa = _json(r)
    validate_fhir_resource(pa, "Patient")
    patient_id = pa["id"]

    # PlanDefinition create 
    pd_body = {
        "resourceType": "PlanDefinition",
        "status": "active",
        "title": "Therapieplan Woche 1",
        "description": "Täglich 10 Minuten Atemübung.",
        "subjectReference": {"reference": f"Patient/{patient_id}"},
        "author": [{"name": f"Practitioner/{practitioner_id}"}]
    }

    r = client.post("/api/plandefinition/", data=json.dumps(pd_body), content_type="application/json")
    assert r.status_code == 200
    created = _json(r)
    validate_fhir_resource(created, "PlanDefinition")
    plan_id = created["id"]

    # READ
    r = client.get(f"/api/plandefinition/{plan_id}/")
    assert r.status_code == 200
    got = _json(r)
    validate_fhir_resource(got, "PlanDefinition")

    # UPDATE
    upd = {
        "resourceType": "PlanDefinition",
        "title": "Therapieplan Woche 1 (Update)",
        "description": "Täglich 15 Minuten Atemübung."
    }
    r = client.put(f"/api/plandefinition/{plan_id}/", data=json.dumps(upd), content_type="application/json")
    assert r.status_code == 200
    updated = _json(r)
    validate_fhir_resource(updated, "PlanDefinition")
    assert updated["title"].endswith("(Update)")

    # DELETE (
    r = client.delete(f"/api/plandefinition/{plan_id}/")
    assert r.status_code == 204

    r = client.get(f"/api/plandefinition/{plan_id}/")
    assert r.status_code == 404
