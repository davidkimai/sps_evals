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
  var current: int := base_seconds;
  var i: int := 0;
  
  while i < attempts
    invariant 0 <= i <= attempts
    invariant |schedule| == i
    invariant forall k :: 0 <= k < |schedule| ==> schedule[k] >= 1
    invariant forall k :: 0 <= k < |schedule| ==> schedule[k] <= cap_seconds
    invariant current >= 1
  {
    var delay: int;
    if current > cap_seconds {
      delay := cap_seconds;
    } else {
      delay := current;
    }
    
    schedule := schedule + [delay];
    
    // Double current for next iteration, but guard against overflow by capping
    if current <= cap_seconds / 2 {
      current := current * 2;
    } else {
      current := cap_seconds;
    }
    
    i := i + 1;
  }
  
  return schedule;
}
