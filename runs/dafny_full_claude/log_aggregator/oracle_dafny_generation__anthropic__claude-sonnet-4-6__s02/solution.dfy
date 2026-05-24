method MergeLogs(streams: seq<seq<(int, int, int)>>) returns (result: seq<(int, int, int)>)
  // Each record is (ts, source, seq_num)
  // Merge, deduplicate by (source, seq_num), sort by ts
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i].0 <= result[j].0
{
  // Collect all records
  var all: seq<(int, int, int)> := [];
  
  for i := 0 to |streams|
    invariant true
  {
    var stream := streams[i];
    for j := 0 to |stream|
      invariant true
    {
      all := all + [stream[j]];
    }
  }
  
  // Deduplicate by (source, seq_num)
  var deduped: seq<(int, int, int)> := [];
  for i := 0 to |all|
    invariant true
  {
    var record := all[i];
    var found := false;
    for j := 0 to |deduped|
      invariant true
    {
      if deduped[j].1 == record.1 && deduped[j].2 == record.2 {
        found := true;
      }
    }
    if !found {
      deduped := deduped + [record];
    }
  }
  
  // Sort by ts (insertion sort)
  var sorted := deduped;
  var n := |sorted|;
  var i := 1;
  while i < n
    invariant 0 <= i <= n
    invariant |sorted| == n
    invariant forall p, q :: 0 <= p < q < i ==> sorted[p].0 <= sorted[q].0
  {
    var key := sorted[i];
    var j := i - 1;
    while j >= 0 && sorted[j].0 > key.0
      invariant -1 <= j < i
      invariant |sorted| == n
      invariant forall p, q :: 0 <= p < q <= i && q != j + 1 ==> 
        (if p == j + 1 then key.0 else sorted[p].0) <= sorted[q].0 || p > j
    {
      sorted := sorted[j + 1 := sorted[j]];
      j := j - 1;
    }
    sorted := sorted[j + 1 := key];
    i := i + 1;
  }
  
  result := sorted;
}

method Main() {
  // Test basic functionality
  var stream1: seq<(int, int, int)> := [(1, 1, 1), (3, 1, 2)];
  var stream2: seq<(int, int, int)> := [(2, 2, 1), (1, 1, 1)]; // duplicate (1,1,1)
  var streams: seq<seq<(int, int, int)>> := [stream1, stream2];
  
  var result := MergeLogs(streams);
  
  // Verify sorted
  assert forall i, j :: 0 <= i < j < |result| ==> result[i].0 <= result[j].0;
  
  print "Result length: ", |result|, "\n";
  for i := 0 to |result| {
    print "Record: ts=", result[i].0, " source=", result[i].1, " seq=", result[i].2, "\n";
  }
}
