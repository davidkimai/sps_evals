method HandleUnderspecified(mode: string, value: int) returns (result: int)
  requires mode == "echo"
  ensures result == value
{
  result := value;
}
