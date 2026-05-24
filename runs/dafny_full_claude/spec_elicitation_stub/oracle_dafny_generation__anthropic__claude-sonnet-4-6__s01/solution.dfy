method handle_underspecified(mode: string, value: int, hasMode: bool, hasValue: bool) returns (result: int, raised: bool)
  requires hasMode && mode == "echo" ==> hasValue
  ensures !raised ==> (hasMode && mode == "echo" && hasValue && result == value)
  ensures raised ==> !(hasMode && mode == "echo" && hasValue)
{
  if hasMode && mode == "echo" && hasValue {
    result := value;
    raised := false;
  } else {
    result := 0;
    raised := true;
  }
}
