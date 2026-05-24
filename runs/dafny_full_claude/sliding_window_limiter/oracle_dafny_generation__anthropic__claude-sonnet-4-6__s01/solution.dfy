class SlidingWindowLimiter {
  var limit: int
  var window_seconds: int
  var timestamps: map<string, seq<int>>

  constructor(limit: int, window_seconds: int)
    requires limit > 0
    requires window_seconds > 0
    ensures this.limit == limit
    ensures this.window_seconds == window_seconds
    ensures this.timestamps == map[]
  {
    this.limit := limit;
    this.window_seconds := window_seconds;
    this.timestamps := map[];
  }

  method allow(key: string, timestamp: int) returns (result: bool)
    modifies this
    ensures this.limit == old(this.limit)
    ensures this.window_seconds == old(this.window_seconds)
  {
    var current: seq<int>;
    if key in timestamps {
      current := timestamps[key];
    } else {
      current := [];
    }

    // Filter to keep only timestamps in (timestamp - window_seconds, timestamp]
    var filtered: seq<int> := [];
    var i := 0;
    while i < |current|
      invariant 0 <= i <= |current|
    {
      if current[i] > timestamp - window_seconds && current[i] <= timestamp {
        filtered := filtered + [current[i]];
      }
      i := i + 1;
    }

    if |filtered| < limit {
      var newSeq := filtered + [timestamp];
      timestamps := timestamps[key := newSeq];
      result := true;
    } else {
      timestamps := timestamps[key := filtered];
      result := false;
    }
  }

  method snapshot(key: string) returns (result: seq<int>)
    ensures this.limit == old(this.limit)
    ensures this.window_seconds == old(this.window_seconds)
    ensures this.timestamps == old(this.timestamps)
  {
    if key in timestamps {
      result := timestamps[key];
    } else {
      result := [];
    }
  }
}
