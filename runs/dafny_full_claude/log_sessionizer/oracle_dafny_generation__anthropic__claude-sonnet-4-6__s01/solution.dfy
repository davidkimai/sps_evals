method build_sessions(events: seq<(string, int)>, gap_seconds: int) returns (sessions: seq<(string, int, int, int)>)
  requires gap_seconds >= 0
  ensures true
{
  // Sort events by user_id then timestamp using insertion sort
  var sorted := events;
  var n := |sorted|;
  var i := 1;
  while i < n
    invariant 1 <= i <= n
    invariant |sorted| == n
    decreases n - i
  {
    var j := i;
    while j > 0 && (sorted[j-1].0 > sorted[j].0 || (sorted[j-1].0 == sorted[j].0 && sorted[j-1].1 > sorted[j].1))
      invariant 0 <= j <= i
      invariant |sorted| == n
      decreases j
    {
      var tmp := sorted[j-1];
      sorted := sorted[j-1 := sorted[j]][j := tmp];
      j := j - 1;
    }
    i := i + 1;
  }

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
    decreases |sorted| - k
  {
    var ev := sorted[k];
    if ev.0 == cur_user {
      var gap := ev.1 - cur_end;
      if gap > gap_seconds {
        sessions := sessions + [(cur_user, cur_start, cur_end, cur_count)];
        cur_start := ev.1;
        cur_end := ev.1;
        cur_count := 1;
      } else {
        cur_end := ev.1;
        cur_count := cur_count + 1;
      }
    } else {
      sessions := sessions + [(cur_user, cur_start, cur_end, cur_count)];
      cur_user := ev.0;
      cur_start := ev.1;
      cur_end := ev.1;
      cur_count := 1;
    }
    k := k + 1;
  }
  sessions := sessions + [(cur_user, cur_start, cur_end, cur_count)];
}

method Main()
{
  var events := [("alice", 100), ("bob", 200), ("alice", 150), ("alice", 500)];
  var sessions := build_sessions(events, 50);
  var i := 0;
  while i < |sessions|
    invariant 0 <= i <= |sessions|
    decreases |sessions| - i
  {
    var s := sessions[i];
    print s.0, " ", s.1, " ", s.2, " ", s.3, "\n";
    i := i + 1;
  }
}
