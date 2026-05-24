method validate_intake(patient_id: string, age: int, symptoms: seq<string>) returns (result: (string, int, seq<string>))
  requires |patient_id| > 0
  requires age >= 0
  ensures result.0 == patient_id
  ensures result.1 == age
  ensures result.2 == symptoms
{
  result := (patient_id, age, symptoms);
}

method Main() {
  var r := validate_intake("P001", 30, ["fever", "cough"]);
  print "patient_id: ", r.0, "\n";
  print "age: ", r.1, "\n";
  print "symptoms: ", r.2, "\n";
}
