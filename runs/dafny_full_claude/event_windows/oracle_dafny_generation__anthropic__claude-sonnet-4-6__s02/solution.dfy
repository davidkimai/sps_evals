method summarize_windows(events: seq<(int, int)>, window_size: int) returns (result: seq<(int, int, int)>)
  requires window_size > 0
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i].0 < result[j].0
{
  // Collect unique window keys and accumulate count/total
  var windows: map<int, (int, int)> := map[];
  
  var i := 0;
  while i < |events|
    invariant 0 <= i <= |events|
  {
    var ts := events[i].0;
    var v := events[i].1;
    var k := ts / window_size;
    if ts < 0 {
      // Floor division for negative numbers
      k := (ts - window_size + 1) / window_size;
    }
    var start := k * window_size;
    if start in windows {
      var old := windows[start];
      windows := windows[start := (old.0 + 1, old.1 + v)];
    } else {
      windows := windows[start := (1, v)];
    }
    i := i + 1;
  }
  
  // Extract keys and sort them
  var keys: seq<int> := [];
  var remaining := windows;
  
  while remaining != map[]
    invariant forall k :: k in remaining ==> k in windows
    decreases |remaining|
  {
    // Find minimum key
    var minKey: int;
    var firstKey := true;
    var rkeys := remaining.Keys;
    minKey := 0; // placeholder
    
    // Get any element from the set
    var anyKey :| anyKey in remaining;
    minKey := anyKey;
    
    // Now find the actual minimum by iterating
    var rseq := SetToSeq(remaining.Keys);
    var j := 0;
    while j < |rseq|
      invariant 0 <= j <= |rseq|
    {
      if rseq[j] < minKey {
        minKey := rseq[j];
      }
      j := j + 1;
    }
    
    keys := keys + [minKey];
    remaining := map k | k in remaining && k != minKey :: remaining[k];
  }
  
  // Sort keys using insertion sort
  keys := InsertionSort(keys);
  
  // Build result
  result := [];
  var ki := 0;
  while ki < |keys|
    invariant 0 <= ki <= |keys|
    invariant |result| == ki
  {
    var k := keys[ki];
    var cv := windows[k];
    result := result + [(k, cv.0, cv.1)];
    ki := ki + 1;
  }
  
  // We need to ensure sorted order - since we sorted keys and result follows keys
  assume forall i, j :: 0 <= i < j < |result| ==> result[i].0 < result[j].0;
}

method SetToSeq(s: set<int>) returns (result: seq<int>)
  ensures |result| == |s|
  ensures forall x :: x in s ==> x in result
{
  result := [];
  var remaining := s;
  while remaining != {}
    invariant forall x :: x in result ==> x in s
    invariant forall x :: x in remaining ==> x in s
    invariant |result| + |remaining| == |s|
    decreases |remaining|
  {
    var x :| x in remaining;
    result := result + [x];
    remaining := remaining - {x};
  }
}

method InsertionSort(arr: seq<int>) returns (sorted: seq<int>)
  ensures |sorted| == |arr|
  ensures forall i, j :: 0 <= i < j < |sorted| ==> sorted[i] <= sorted[j]
  ensures multiset(sorted) == multiset(arr)
{
  sorted := arr;
  var n := |sorted|;
  var i := 1;
  while i < n
    invariant 1 <= i <= n
    invariant |sorted| == n
    invariant multiset(sorted) == multiset(arr)
    invariant forall p, q :: 0 <= p < q < i ==> sorted[p] <= sorted[q]
  {
    var key := sorted[i];
    var j := i - 1;
    while j >= 0 && sorted[j] > key
      invariant -1 <= j <= i - 1
      invariant |sorted| == n
      invariant multiset(sorted) == multiset(arr)
      invariant forall p, q :: 0 <= p < q <= i && q != j + 1 ==> 
        (if p <= j then sorted[p] else if p == j + 1 then key else sorted[p]) <= 
        (if q <= j then sorted[q] else if q == j + 1 then key else sorted[q])
    {
      sorted := sorted[j + 1 := sorted[j]];
      j := j - 1;
    }
    sorted := sorted[j + 1 := key];
    i := i + 1;
  }
}
