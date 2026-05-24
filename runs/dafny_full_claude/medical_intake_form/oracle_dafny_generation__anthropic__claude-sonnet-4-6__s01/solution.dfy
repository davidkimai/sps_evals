method ValidateIntake(
  hasPatientId: bool,
  patientIdNonEmpty: bool,
  hasAge: bool,
  ageValue: int,
  hasSymptoms: bool,
  symptomsNonEmpty: bool
) returns (valid: bool, errorField: string)
  ensures valid ==>
    hasPatientId && patientIdNonEmpty &&
    hasAge && ageValue >= 0 &&
    hasSymptoms
  ensures !valid ==> errorField != ""
{
  if !hasPatientId {
    valid := false;
    errorField := "patient_id";
    return;
  }
  if !patientIdNonEmpty {
    valid := false;
    errorField := "patient_id";
    return;
  }
  if !hasAge {
    valid := false;
    errorField := "age";
    return;
  }
  if ageValue < 0 {
    valid := false;
    errorField := "age";
    return;
  }
  if !hasSymptoms {
    valid := false;
    errorField := "symptoms";
    return;
  }
  valid := true;
  errorField := "";
}

method Main() {
  var valid, errorField := ValidateIntake(true, true, true, 25, true, true);
  assert valid;

  var valid2, errorField2 := ValidateIntake(false, false, true, 25, true, true);
  assert !valid2;
  assert errorField2 == "patient_id";

  var valid3, errorField3 := ValidateIntake(true, true, true, -1, true, true);
  assert !valid3;
  assert errorField3 == "age";
}
