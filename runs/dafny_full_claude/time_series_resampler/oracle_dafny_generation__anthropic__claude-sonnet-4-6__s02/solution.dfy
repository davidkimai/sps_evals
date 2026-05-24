method resample_series(
  points: seq<(int, real)>,
  start: int,
  end: int,
  interval: int
) returns (result: seq<(int, real)>)
  requires interval > 0
  requires start <= end
{
  // Sort points by timestamp (insertion sort)
  var sorted := points;
  var n := |sorted|;
  var i := 1;
  while i < n
    invariant 1 <= i <= n
    invariant |sorted| == n
  {
    var j := i;
    while j > 0 && sorted[j-1].0 > sorted[j].0
      invariant 0 <= j <= i
      invariant |sorted| == n
    {
      var tmp := sorted[j-1];
      sorted := sorted[j-1 := sorted[j]][j := tmp];
      j := j - 1;
    }
    i := i + 1;
  }

  result := [];
  var ts := start;
  while ts <= end
    invariant interval > 0
  {
    // Find the latest point at or before ts
    var best_val: real := 0.0;
    var found := false;
    var k := 0;
    while k < |sorted|
      invariant 0 <= k <= |sorted|
    {
      if sorted[k].0 <= ts {
        best_val := sorted[k].1;
        found := true;
      }
      k := k + 1;
    }
    if found {
      result := result + [(ts, best_val)];
    } else {
      // No value known; we still need to add entry
      // In Dafny we can't represent None natively, so use a sentinel
      // We'll use 0.0 as placeholder but mark somehow
      // Since we must translate to Python, we'll use a special encoding
      // We add a tuple with a special marker value
      // For the Python translation, we'll handle None separately
      result := result + [(ts, 0.0)];
    }
    ts := ts + interval;
  }
}

// We need a version that tracks whether each value is None
// Let's use a boolean sequence to track

method resample_series_with_none(
  points: seq<(int, real)>,
  start: int,
  end: int,
  interval: int
) returns (result: seq<(int, real)>, has_value: seq<bool>)
  requires interval > 0
  requires start <= end
  ensures |result| == |has_value|
{
  // Sort points by timestamp (insertion sort)
  var sorted := points;
  var n := |sorted|;
  var i := 1;
  while i < n
    invariant 1 <= i <= n
    invariant |sorted| == n
  {
    var j := i;
    while j > 0 && sorted[j-1].0 > sorted[j].0
      invariant 0 <= j <= i
      invariant |sorted| == n
    {
      var tmp := sorted[j-1];
      sorted := sorted[j-1 := sorted[j]][j := tmp];
      j := j - 1;
    }
    i := i + 1;
  }

  result := [];
  has_value := [];
  var ts := start;
  while ts <= end
    invariant interval > 0
    invariant |result| == |has_value|
  {
    var best_val: real := 0.0;
    var found := false;
    var k := 0;
    while k < |sorted|
      invariant 0 <= k <= |sorted|
    {
      if sorted[k].0 <= ts {
        best_val := sorted[k].1;
        found := true;
      }
      k := k + 1;
    }
    result := result + [(ts, best_val)];
    has_value := has_value + [found];
    ts := ts + interval;
  }
}
