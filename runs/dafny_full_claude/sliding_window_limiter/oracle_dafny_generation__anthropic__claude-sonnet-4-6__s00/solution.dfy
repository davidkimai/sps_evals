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
    var existing: seq<int> := [];
    if key in this.timestamps {
      existing := this.timestamps[key];
    }

    // Filter to only keep timestamps in (timestamp - window_seconds, timestamp]
    var filtered: seq<int> := [];
    var i := 0;
    while i < |existing|
      invariant 0 <= i <= |existing|
    {
      if existing[i] > timestamp - this.window_seconds && existing[i] <= timestamp {
        filtered := filtered + [existing[i]];
      }
      i := i + 1;
    }

    if |filtered| < this.limit {
      var newSeq := filtered + [timestamp];
      this.timestamps := this.timestamps[key := newSeq];
      result := true;
    } else {
      this.timestamps := this.timestamps[key := filtered];
      result := false;
    }
  }

  method snapshot(key: string) returns (result: seq<int>)
    ensures this.limit == old(this.limit)
    ensures this.window_seconds == old(this.window_seconds)
    ensures this.timestamps == old(this.timestamps)
  {
    if key in this.timestamps {
      result := this.timestamps[key];
    } else {
      result := [];
    }
  }
}
