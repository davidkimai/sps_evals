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
  var i := 0;
  var current := base_seconds;
  
  while i < attempts
    invariant 0 <= i <= attempts
    invariant |schedule| == i
    invariant current >= 1
    invariant forall k :: 0 <= k < |schedule| ==> schedule[k] >= 1
    invariant forall k :: 0 <= k < |schedule| ==> schedule[k] <= cap_seconds
  {
    var delay: int;
    if current > cap_seconds {
      delay := cap_seconds;
    } else {
      delay := current;
    }
    schedule := schedule + [delay];
    
    // Double current for next iteration, but cap to avoid overflow
    if current <= cap_seconds / 2 {
      current := current * 2;
    } else {
      current := cap_seconds;
    }
    
    i := i + 1;
  }
  
  return schedule;
}

method Main() {
  var s1 := build_retry_schedule(0, 1, 100);
  assert |s1| == 0;
  
  var s2 := build_retry_schedule(3, 1, 100);
  assert |s2| == 3;
  
  var s3 := build_retry_schedule(5, 2, 10);
  assert |s3| == 5;
}
