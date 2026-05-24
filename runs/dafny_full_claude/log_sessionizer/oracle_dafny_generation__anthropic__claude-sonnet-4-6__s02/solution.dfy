method build_sessions(events: seq<(string, int)>, gap_seconds: int) returns (sessions: seq<(string, int, int, int)>)
  requires gap_seconds >= 0
  ensures true
{
  // Sort events by user_id then timestamp
  var sorted := SortEvents(events);
  
  sessions := [];
  
  if |sorted| == 0 {
    return;
  }
  
  var i := 0;
  var current_user := sorted[0].0;
  var session_start := sorted[0].1;
  var session_end := sorted[0].1;
  var session_count := 1;
  
  i := 1;
  while i < |sorted|
    invariant 0 <= i <= |sorted|
    invariant session_count >= 1
  {
    var ev := sorted[i];
    var user := ev.0;
    var ts := ev.1;
    
    if user != current_user {
      // Save current session
      sessions := sessions + [(current_user, session_start, session_end, session_count)];
      // Start new session for new user
      current_user := user;
      session_start := ts;
      session_end := ts;
      session_count := 1;
    } else {
      // Same user - check gap
      if ts - session_end > gap_seconds {
        // Save current session and start new one
        sessions := sessions + [(current_user, session_start, session_end, session_count)];
        session_start := ts;
        session_end := ts;
        session_count := 1;
      } else {
        // Continue current session
        session_end := ts;
        session_count := session_count + 1;
      }
    }
    
    i := i + 1;
  }
  
  // Don't forget the last session
  sessions := sessions + [(current_user, session_start, session_end, session_count)];
}

method SortEvents(events: seq<(string, int)>) returns (sorted: seq<(string, int)>)
  ensures |sorted| == |events|
  ensures forall i, j :: 0 <= i < j < |sorted| ==>
    sorted[i].0 < sorted[j].0 ||
    (sorted[i].0 == sorted[j].0 && sorted[i].1 <= sorted[j].1)
{
  sorted := events;
  // Insertion sort
  var n := |sorted|;
  var i := 1;
  while i < n
    invariant 1 <= i <= n
    invariant |sorted| == n
    invariant forall a, b :: 0 <= a < b < i ==>
      sorted[a].0 < sorted[b].0 ||
      (sorted[a].0 == sorted[b].0 && sorted[a].1 <= sorted[b].1)
  {
    var key := sorted[i];
    var j := i - 1;
    while j >= 0 && (sorted[j].0 > key.0 || (sorted[j].0 == key.0 && sorted[j].1 > key.1))
      invariant -1 <= j < i
      invariant |sorted| == n
      invariant forall a, b :: 0 <= a < b < i && b != j + 1 ==>
        sorted[a].0 < sorted[b].0 ||
        (sorted[a].0 == sorted[b].0 && sorted[a].1 <= sorted[b].1)
      invariant forall a :: j + 1 < a <= i ==>
        key.0 < sorted[a].0 ||
        (key.0 == sorted[a].0 && key.1 <= sorted[a].1)
      invariant forall a, b :: 0 <= a < b <= i && a != j + 1 && b != j + 1 ==>
        sorted[a].0 < sorted[b].0 ||
        (sorted[a].0 == sorted[b].0 && sorted[a].1 <= sorted[b].1)
    {
      sorted := sorted[j + 1 := sorted[j]];
      j := j - 1;
    }
    sorted := sorted[j + 1 := key];
    i := i + 1;
  }
}
