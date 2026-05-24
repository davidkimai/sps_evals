method build_sessions(events: seq<(string, int)>, gap_seconds: int) returns (sessions: seq<(string, int, int, int)>)
  requires gap_seconds >= 0
  ensures true
{
  // Sort events by user_id then timestamp using insertion sort
  var sorted := events;
  var n := |sorted|;
  
  // Insertion sort
  var i := 1;
  while i < n
    invariant 1 <= i <= n
    invariant |sorted| == n
  {
    var j := i;
    while j > 0 && (sorted[j-1].0 > sorted[j].0 || (sorted[j-1].0 == sorted[j].0 && sorted[j-1].1 > sorted[j].1))
      invariant 0 <= j <= i
      invariant |sorted| == n
    {
      var tmp := sorted[j-1];
      sorted := sorted[j-1 := sorted[j]][j := tmp];
      j := j - 1;
    }
    i := i + 1;
  }
  
  // Build sessions
  sessions := [];
  
  if |sorted| == 0 {
    return;
  }
  
  var cur_user := sorted[0].0;
  var cur_start := sorted[0].1;
  var cur_end := sorted[0].1;
  var cur_count := 1;
  
  var k := 1;
  while k < |sorted|
    invariant 1 <= k <= |sorted|
    invariant cur_count >= 1
  {
    var ev := sorted[k];
    if ev.0 == cur_user {
      if ev.1 - cur_end > gap_seconds {
        // Close current session and start new one
        sessions := sessions + [(cur_user, cur_start, cur_end, cur_count)];
        cur_start := ev.1;
        cur_end := ev.1;
        cur_count := 1;
      } else {
        cur_end := ev.1;
        cur_count := cur_count + 1;
      }
    } else {
      // New user, close current session
      sessions := sessions + [(cur_user, cur_start, cur_end, cur_count)];
      cur_user := ev.0;
      cur_start := ev.1;
      cur_end := ev.1;
      cur_count := 1;
    }
    k := k + 1;
  }
  
  // Close last session
  sessions := sessions + [(cur_user, cur_start, cur_end, cur_count)];
  
  return sessions;
}

method Main() {
  var events: seq<(string, int)> := [("alice", 100), ("bob", 200), ("alice", 150), ("alice", 500)];
  var gap := 100;
  var result := build_sessions(events, gap);
  var i := 0;
  while i < |result| {
    print result[i], "\n";
    i := i + 1;
  }
}
