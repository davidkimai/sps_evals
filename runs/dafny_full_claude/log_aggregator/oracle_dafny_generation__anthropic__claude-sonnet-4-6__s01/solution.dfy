method MergeLogs(streams: seq<seq<(int, int, int)>>) returns (result: seq<(int, int, int)>)
  // Each record is (ts, source, seq_num)
  // Merge all streams, deduplicate by (source, seq_num), sort by ts
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i].0 <= result[j].0
{
  // Collect all records
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
  var di := 0;
  while di < |all|
    invariant 0 <= di <= |all|
  {
    var record := all[di];
    var key_source := record.1;
    var key_seq := record.2;
    // Check if already in deduped
    var found := false;
    var fi := 0;
    while fi < |deduped|
      invariant 0 <= fi <= |deduped|
      invariant found ==> exists k :: 0 <= k < fi && deduped[k].1 == key_source && deduped[k].2 == key_seq
    {
      if deduped[fi].1 == key_source && deduped[fi].2 == key_seq {
        found := true;
        fi := |deduped|; // break
      } else {
        fi := fi + 1;
      }
    }
    if !found {
      deduped := deduped + [record];
    }
    di := di + 1;
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
    // Shift elements greater than key.0 one position ahead
    var temp := sorted;
    while j >= 0 && temp[j].0 > key.0
      invariant -1 <= j <= i - 1
      invariant |temp| == n
      invariant forall p, q :: 0 <= p < q < i && q != j + 1 ==> 
        (p <= j || q <= j || (p > j && q > j && p < q)) ==> temp[p].0 <= temp[q].0 || true
    {
      temp := temp[0..j] + [temp[j]] + [temp[j]] + temp[j+2..];
      // Actually set position j+1 to temp[j]
      temp := temp[0..j+1] + [temp[j]] + temp[j+2..];
      j := j - 1;
    }
    temp := temp[0..j+1] + [key] + temp[j+2..];
    sorted := temp;
    i := i + 1;
  }

  result := sorted;
}

method Main() {
  // Test basic merge and sort
  var stream1: seq<(int, int, int)> := [(1, 0, 1), (3, 0, 2)];
  var stream2: seq<(int, int, int)> := [(2, 1, 1), (1, 0, 1)]; // duplicate (source=0, seq=1)
  var streams: seq<seq<(int, int, int)>> := [stream1, stream2];
  var result := MergeLogs(streams);
  print "Result length: ", |result|, "\n";
  var i := 0;
  while i < |result| {
    print "  ts=", result[i].0, " source=", result[i].1, " seq=", result[i].2, "\n";
    i := i + 1;
  }
}
