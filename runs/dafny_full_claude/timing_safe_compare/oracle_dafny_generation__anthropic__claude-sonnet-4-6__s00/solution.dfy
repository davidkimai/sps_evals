method timing_safe_compare(left: seq<int>, right: seq<int>) returns (result: bool)
  ensures result <==> (left == right)
{
  if |left| != |right| {
    return false;
  }
  var diff := 0;
  var i := 0;
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
