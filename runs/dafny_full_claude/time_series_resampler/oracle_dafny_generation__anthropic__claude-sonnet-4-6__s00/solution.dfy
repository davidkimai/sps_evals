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
    decreases end - ts + 1
  {
    // Find the latest point at or before ts
    var best_val: real := 0.0;
    var found := false;
    var i := 0;
    while i < |points|
      invariant 0 <= i <= |points|
    {
      var pt_time := points[i].0;
      var pt_val := points[i].1;
      if pt_time <= ts {
        if !found {
          best_val := pt_val;
          found := true;
        } else {
          // Check if this point is more recent than current best
          // We need to track the best timestamp too
          best_val := pt_val; // will fix below
        }
      }
      i := i + 1;
    }
    
    // Redo with proper tracking of best timestamp
    var best_time: int := 0;
    best_val := 0.0;
    found := false;
    i := 0;
    while i < |points|
      invariant 0 <= i <= |points|
    {
      var pt_time := points[i].0;
      var pt_val := points[i].1;
      if pt_time <= ts {
        if !found || pt_time >= best_time {
          best_time := pt_time;
          best_val := pt_val;
          found := true;
        }
      }
      i := i + 1;
    }
    
    if found {
      result := result + [(ts, best_val)];
    } else {
      // No value known - we represent None as a sentinel
      // In Dafny we can't have None for real, so we use a flag
      // We'll handle this by not adding or using a sentinel
      // For translation purposes, we add a special marker
      // Use 0.0 as placeholder but mark somehow
      // Since Dafny doesn't support Option easily here,
      // we'll use a separate output sequence for the "has value" flags
      result := result + [(ts, 0.0)]; // placeholder, handled in wrapper
    }
    
    ts := ts + interval;
  }
}

// We need a version that tracks which values are valid
method resample_series_with_flags(
  points: seq<(int, real)>,
  start: int,
  end: int,
  interval: int
) returns (result: seq<(int, real)>, valid: seq<bool>)
  requires interval > 0
  requires start <= end
  ensures |result| == |valid|
{
  result := [];
  valid := [];
  var ts := start;
  while ts <= end
    invariant interval > 0
    invariant |result| == |valid|
    decreases end - ts + 1
  {
    var best_time: int := 0;
    var best_val: real := 0.0;
    var found := false;
    var i := 0;
    while i < |points|
      invariant 0 <= i <= |points|
    {
      var pt_time := points[i].0;
      var pt_val := points[i].1;
      if pt_time <= ts {
        if !found || pt_time >= best_time {
          best_time := pt_time;
          best_val := pt_val;
          found := true;
        }
      }
      i := i + 1;
    }
    
    result := result + [(ts, best_val)];
    valid := valid + [found];
    
    ts := ts + interval;
  }
}
