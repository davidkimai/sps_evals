method MergeLogs(streams: seq<seq<(int, int, int)>>) returns (result: seq<(int, int, int)>)
  // Each record is (ts, source, seq_num)
  // Merge all streams, deduplicate by (source, seq_num), sort by ts
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i].0 <= result[j].0
{
  // Collect all records into one sequence
  var all: seq<(int, int, int)> := [];
  var si := 0;
  while si < |streams|
    invariant 0 <= si <= |streams|
  {
    var stream := streams[si];
    var ri := 0;
    while ri < |stream|
      invariant 0 <= ri <= |stream|
    {
      all := all + [stream[ri]];
      ri := ri + 1;
    }
    si := si + 1;
  }

  // Deduplicate by (source, seq_num) - keep first occurrence
  var deduped: seq<(int, int, int)> := [];
  var seen: seq<(int, int)> := [];
  var di := 0;
  while di < |all|
    invariant 0 <= di <= |all|
    invariant |seen| == |deduped|
  {
    var rec := all[di];
    var key := (rec.1, rec.2);
    var found := false;
    var ki := 0;
    while ki < |seen|
      invariant 0 <= ki <= |seen|
    {
      if seen[ki] == key {
        found := true;
        break;
      }
      ki := ki + 1;
    }
    if !found {
      deduped := deduped + [rec];
      seen := seen + [key];
    }
    di := di + 1;
  }

  // Sort by ts using insertion sort
  result := deduped;
  var n := |result|;
  var i := 1;
  while i < n
    invariant 1 <= i <= n
    invariant |result| == n
    invariant forall p, q :: 0 <= p < q < i ==> result[p].0 <= result[q].0
  {
    var key := result[i];
    var j := i - 1;
    while j >= 0 && result[j].0 > key.0
      invariant -1 <= j < i
      invariant |result| == n
      invariant forall p, q :: 0 <= p < q <= i && p != j + 1 && q != j + 1 ==>
        (p < q < i ==> result[p].0 <= result[q].0)
    {
      result := result[j := result[j+1]][j+1 := result[j]];
      j := j - 1;
    }
    i := i + 1;
  }
}

method Main() {
  // Test basic functionality
  var stream1: seq<(int, int, int)> := [(1, 0, 1), (3, 0, 2)];
  var stream2: seq<(int, int, int)> := [(2, 1, 1), (1, 0, 1)]; // duplicate (source=0, seq=1)
  var streams: seq<seq<(int, int, int)>> := [stream1, stream2];
  var result := MergeLogs(streams);
  // Expected: 3 records sorted by ts, deduplicated
  print "Result length: ", |result|, "\n";
  var i := 0;
  while i < |result| {
    print "  ts=", result[i].0, " source=", result[i].1, " seq=", result[i].2, "\n";
    i := i + 1;
  }
}
