method timing_safe_compare(left: string, right: string) returns (result: bool)
  ensures result == (left == right)
{
  result := left == right;
}
