method HandleUnderspecified(mode: string, value: int, hasMode: bool, hasValue: bool) returns (result: int, success: bool)
  requires hasMode && hasValue ==> true
  ensures mode == "echo" && hasMode && hasValue ==> success && result == value
  ensures !(mode == "echo" && hasMode && hasValue) ==> !success
{
  if hasMode && hasValue && mode == "echo" {
    result := value;
    success := true;
  } else {
    result := 0;
    success := false;
  }
}

method Main()
{
  var result, success := HandleUnderspecified("echo", 42, true, true);
  assert success;
  assert result == 42;

  var result2, success2 := HandleUnderspecified("other", 42, true, true);
  assert !success2;

  var result3, success3 := HandleUnderspecified("echo", 10, false, true);
  assert !success3;
}
