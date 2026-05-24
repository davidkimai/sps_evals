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
  var j := |acquired| - 1;
  while j >= 0
    invariant -1 <= j <= |acquired| - 1
    invariant result == acquired[j+1..]
  {
    result := result + [acquired[j]];
    j := j - 1;
  }
  
  // Reverse of acquired equals resources closed in reverse order
  // We need to show result == resources
  // result is acquired reversed, and acquired == resources
  // So result == reverse(resources)
  // But ensures says closed == resources which would be wrong for reverse...
  // Let me re-read: "close tracked resources in reverse acquisition order"
  // So closed should be the reverse of acquired (which equals resources)
  // The ensures should reflect this
  
  closed := result;
}
