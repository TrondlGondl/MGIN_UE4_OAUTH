import json
import os
import zipfile
from pathlib import Path

import requests
from jsonschema import Draft6Validator

FHIR_SCHEMA_ZIP_URL = "https://www.hl7.org/fhir/fhir.schema.json.zip"

def _project_root() -> Path:
    
    return Path(__file__).resolve().parents[1]

def ensure_fhir_schema_cached() -> Path:
    """
    Downloads and extracts fhir.schema.json once into tests/_schemas/.
    Returns path to fhir.schema.json
    """
    cache_dir = _project_root() / "tests" / "_schemas"
    cache_dir.mkdir(parents=True, exist_ok=True)

    schema_json_path = cache_dir / "fhir.schema.json"
    if schema_json_path.exists():
        return schema_json_path

    zip_path = cache_dir / "fhir.schema.json.zip"
    r = requests.get(FHIR_SCHEMA_ZIP_URL, timeout=60)
    r.raise_for_status()
    zip_path.write_bytes(r.content)

    with zipfile.ZipFile(zip_path, "r") as z:
        # In dem Zip liegt üblicherweise genau fhir.schema.json
        candidates = [n for n in z.namelist() if n.endswith("fhir.schema.json")]
        if not candidates:
            raise RuntimeError(f"Could not find fhir.schema.json in {zip_path}")
        with z.open(candidates[0]) as f:
            schema_json_path.write_bytes(f.read())

    return schema_json_path


def load_fhir_schema() -> dict:
    schema_path = ensure_fhir_schema_cached()
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_fhir_resource(instance: dict, resource_type: str) -> None:
    """
    Validates instance against official FHIR JSON schema (draft-06).
    Picks the specific resource definition from the monolithic schema.
    """
    schema = load_fhir_schema()

    # Validieren gegen den spezifischen ResourceType
    # Schema enthält definitions.<ResourceType>
    sub_schema = {
        "$schema": schema.get("$schema", "http://json-schema.org/draft-06/schema#"),
        "$ref": f"#/definitions/{resource_type}",
        "definitions": schema.get("definitions", {}),
    }

    Draft6Validator(sub_schema).validate(instance)
