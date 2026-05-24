method resample_series(
  points: seq<(int, real)>,
  start: int,
  end: int,
  interval: int
) returns (result: seq<(int, real)>)
  requires interval > 0
  requires start <= end
{
  result := [];
  var ts := start;
  while ts <= end
    invariant interval > 0
    decreases end - ts + interval
  {
    // Find the latest point at or before ts
    var bestVal: real := 0.0;
    var found := false;
    var i := 0;
    while i < |points|
      invariant 0 <= i <= |points|
    {
      var pt := points[i];
      if pt.0 <= ts {
        if !found || pt.0 >= bestVal as int {
          // We want the latest point, track by timestamp
          bestVal := pt.1;
          found := true;
          // We need to track the best timestamp too
        }
      }
      i := i + 1;
    }
    // Redo with proper tracking
    var bestTs: int := -1;
    var bestValue: real := 0.0;
    var j := 0;
    while j < |points|
      invariant 0 <= j <= |points|
    {
      var pt := points[j];
      if pt.0 <= ts {
        if bestTs == -1 || pt.0 >= bestTs {
          bestTs := pt.0;
          bestValue := pt.1;
        }
      }
      j := j + 1;
    }
    if bestTs != -1 {
      result := result + [(ts, bestValue)];
    }
    // If not found, we skip (will be None in Python)
    ts := ts + interval;
  }
}
