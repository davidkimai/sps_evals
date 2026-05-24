method summarize_windows(events: seq<(int, int)>, window_size: int) returns (result: seq<(int, int, int)>)
  requires window_size > 0
  ensures true
{
  // We'll collect window data as we go
  // events is seq of (timestamp, value) pairs (malformed already filtered)
  // We need to group by floor(timestamp / window_size)
  
  // First, find all unique window keys and accumulate
  var windows: map<int, (int, int)> := map[];
  
  var i := 0;
  while i < |events|
    invariant 0 <= i <= |events|
  {
    var ts := events[i].0;
    var val := events[i].1;
    var key := ts / window_size;
    // Handle negative timestamps: Dafny integer division truncates toward zero
    // We need floor division
    if ts < 0 && ts % window_size != 0 {
      key := key - 1;
    }
    var start := key * window_size;
    if key in windows {
      var cur := windows[key];
      windows := windows[key := (cur.0 + 1, cur.1 + val)];
    } else {
      windows := windows[key := (1, val)];
    }
    i := i + 1;
  }
  
  // Collect keys and sort them
  var keys: seq<int> := [];
  var keySet := windows.Keys;
  
  // Extract keys from map
  var remaining := keySet;
  while remaining != {}
    invariant remaining <= keySet
    decreases |remaining|
  {
    var k :| k in remaining;
    keys := keys + [k];
    remaining := remaining - {k};
  }
  
  // Sort keys using insertion sort
  var n := |keys|;
  var sortedKeys := keys;
  var j := 1;
  while j < |sortedKeys|
    invariant 0 <= j <= |sortedKeys|
  {
    var cur := sortedKeys[j];
    var k2 := j;
    while k2 > 0 && sortedKeys[k2 - 1] > cur
      invariant 0 <= k2 <= j
    {
      sortedKeys := sortedKeys[k2 := sortedKeys[k2 - 1]];
      k2 := k2 - 1;
    }
    sortedKeys := sortedKeys[k2 := cur];
    j := j + 1;
  }
  
  // Build result
  result := [];
  var idx := 0;
  while idx < |sortedKeys|
    invariant 0 <= idx <= |sortedKeys|
  {
    var k3 := sortedKeys[idx];
    var start := k3 * window_size;
    var data := windows[k3];
    result := result + [(start, data.0, data.1)];
    idx := idx + 1;
  }
}

method Main() {
  var events := [(0, 10), (1, 20), (5, 30), (10, 40)];
  var result := summarize_windows(events, 5);
  var i := 0;
  while i < |result| {
    print result[i], "\n";
    i := i + 1;
  }
}
