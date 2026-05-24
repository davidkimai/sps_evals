method ResourceScope(resources: seq<int>) returns (closed: seq<int>)
  ensures closed == resources
{
  var acquired: seq<int> := [];
  var i := 0;
  while i < |resources|
    invariant 0 <= i <= |resources|
    invariant acquired == resources[..i]
  {
    acquired := acquired + [resources[i]];
    i := i + 1;
  }
  
  var result: seq<int> := [];
  var j := |acquired|;
  while j > 0
    invariant 0 <= j <= |acquired|
    invariant result == acquired[j..]
  {
    j := j - 1;
    result := [acquired[j]] + result;
  }
  
  closed := result;
}
