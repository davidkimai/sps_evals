method summarize_windows(events: seq<(int, int)>, window_size: int) returns (result: seq<(int, int, int)>)
  requires window_size > 0
  ensures forall i :: 0 <= i < |result| ==> result[i].0 % window_size == 0
{
  // Collect unique window starts and compute count/total
  var window_starts: seq<int> := [];
  var window_counts: seq<int> := [];
  var window_totals: seq<int> := [];
  
  var i := 0;
  while i < |events|
    invariant 0 <= i <= |events|
    invariant |window_starts| == |window_counts|
    invariant |window_starts| == |window_totals|
    invariant forall k :: 0 <= k < |window_starts| ==> window_starts[k] % window_size == 0
  {
    var ts := events[i].0;
    var v := events[i].1;
    
    // Compute window start using floor division
    var k: int;
    if ts >= 0 {
      k := (ts / window_size) * window_size;
    } else {
      // Floor division for negative numbers
      var q := ts / window_size;
      var r := ts % window_size;
      if r < 0 {
        k := (q - 1) * window_size;
      } else if r == 0 {
        k := q * window_size;
      } else {
        k := q * window_size;
      }
    }
    
    // Find if window already exists
    var found := false;
    var j := 0;
    while j < |window_starts|
      invariant 0 <= j <= |window_starts|
      invariant |window_starts| == |window_counts|
      invariant |window_starts| == |window_totals|
      invariant forall kk :: 0 <= kk < |window_starts| ==> window_starts[kk] % window_size == 0
    {
      if window_starts[j] == k {
        window_counts := window_counts[j := window_counts[j] + 1];
        window_totals := window_totals[j := window_totals[j] + v];
        found := true;
        break;
      }
      j := j + 1;
    }
    
    if !found {
      window_starts := window_starts + [k];
      window_counts := window_counts + [1];
      window_totals := window_totals + [v];
    }
    
    i := i + 1;
  }
  
  // Sort by window start (insertion sort)
  var n := |window_starts|;
  var sorted_starts := window_starts;
  var sorted_counts := window_counts;
  var sorted_totals := window_totals;
  
  var si := 1;
  while si < n
    invariant 1 <= si <= n
    invariant |sorted_starts| == n
    invariant |sorted_counts| == n
    invariant |sorted_totals| == n
    invariant forall k :: 0 <= k < n ==> sorted_starts[k] % window_size == 0
  {
    var key_start := sorted_starts[si];
    var key_count := sorted_counts[si];
    var key_total := sorted_totals[si];
    var sj := si - 1;
    
    while sj >= 0 && sorted_starts[sj] > key_start
      invariant -1 <= sj <= si - 1
      invariant |sorted_starts| == n
      invariant |sorted_counts| == n
      invariant |sorted_totals| == n
      invariant forall k :: 0 <= k < n ==> sorted_starts[k] % window_size == 0
    {
      sorted_starts := sorted_starts[sj + 1 := sorted_starts[sj]];
      sorted_counts := sorted_counts[sj + 1 := sorted_counts[sj]];
      sorted_totals := sorted_totals[sj + 1 := sorted_totals[sj]];
      sj := sj - 1;
    }
    
    sorted_starts := sorted_starts[sj + 1 := key_start];
    sorted_counts := sorted_counts[sj + 1 := key_count];
    sorted_totals := sorted_totals[sj + 1 := key_total];
    
    si := si + 1;
  }
  
  // Build result
  result := [];
  var ri := 0;
  while ri < n
    invariant 0 <= ri <= n
    invariant |result| == ri
    invariant forall k :: 0 <= k < ri ==> result[k].0 % window_size == 0
    invariant forall k :: 0 <= k < n ==> sorted_starts[k] % window_size == 0
  {
    result := result + [(sorted_starts[ri], sorted_counts[ri], sorted_totals[ri])];
    ri := ri + 1;
  }
}

method Main() {
  var events := [(0, 10), (1, 20), (5, 30), (10, 40)];
  var result := summarize_windows(events, 5);
  print "Windows: ", result, "\n";
}
