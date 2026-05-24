method build_retry_schedule(attempts: int, base_seconds: int, cap_seconds: int) returns (result: seq<int>)
  requires attempts >= 0
  requires base_seconds >= 1
  requires cap_seconds >= 1
  ensures |result| == attempts
  ensures forall i :: 0 <= i < |result| ==> result[i] >= 1
  ensures forall i :: 0 <= i < |result| ==> result[i] <= cap_seconds
{
  if attempts == 0 {
    return [];
  }
  
  var schedule: seq<int> := [];
  var delay := base_seconds;
  var i := 0;
  
  while i < attempts
    invariant 0 <= i <= attempts
    invariant |schedule| == i
    invariant delay >= 1
    invariant forall k :: 0 <= k < |schedule| ==> schedule[k] >= 1
    invariant forall k :: 0 <= k < |schedule| ==> schedule[k] <= cap_seconds
  {
    var capped := if delay > cap_seconds then cap_seconds else delay;
    schedule := schedule + [capped];
    
    // Double the delay for next iteration, but cap to avoid overflow
    if delay <= cap_seconds / 2 {
      delay := delay * 2;
    } else {
      delay := cap_seconds;
    }
    
    i := i + 1;
  }
  
  return schedule;
}

method Main() {
  var s1 := build_retry_schedule(5, 1, 30);
  print s1, "\n";
  
  var s2 := build_retry_schedule(0, 1, 30);
  print s2, "\n";
  
  var s3 := build_retry_schedule(3, 10, 25);
  print s3, "\n";
}
