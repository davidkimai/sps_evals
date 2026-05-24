method timing_safe_compare(left: seq<int>, right: seq<int>) returns (result: bool)
  requires |left| >= 0
  requires |right| >= 0
  ensures result == (left == right)
{
  if |left| != |right| {
    return false;
  }
  var i := 0;
  var diff := 0;
  while i < |left|
    invariant 0 <= i <= |left|
    invariant diff == 0 <==> left[..i] == right[..i]
  {
    if left[i] != right[i] {
      diff := diff + 1;
    }
    i := i + 1;
  }
  result := diff == 0;
}
