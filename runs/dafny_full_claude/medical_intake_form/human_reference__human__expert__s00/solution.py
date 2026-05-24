from __future__ import annotations


def validate_intake(payload: dict) -> dict:
    errors = []
    if not isinstance(payload.get('patient_id'), str) or not payload.get('patient_id'):
        errors.append('patient_id')
    if not isinstance(payload.get('age'), int) or payload.get('age') < 0:
        errors.append('age')
    symptoms = payload.get('symptoms')
    if not isinstance(symptoms, list) or not all(isinstance(item, str) for item in symptoms):
        errors.append('symptoms')
    if errors:
        raise ValueError(', '.join(errors))
    return {'patient_id': payload['patient_id'], 'age': payload['age'], 'symptoms': list(symptoms)}
