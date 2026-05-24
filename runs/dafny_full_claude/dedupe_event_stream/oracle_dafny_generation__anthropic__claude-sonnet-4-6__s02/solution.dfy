method dedupe_events(events: seq<map<string, int>>, key_fields: seq<string>, window_seconds: int) returns (result: seq<map<string, int>>)
  requires window_seconds >= 0
  ensures |result| <= |events|
{
  var kept: seq<map<string, int>> := [];
  
  var i := 0;
  while i < |events|
    invariant 0 <= i <= |events|
    invariant |kept| <= i
  {
    var event := events[i];
    
    // Check if event is well-formed: has timestamp and all key fields
    var well_formed := "timestamp" in event;
    var j := 0;
    while j < |key_fields|
      invariant 0 <= j <= |key_fields|
    {
      if !(key_fields[j] in event) {
        well_formed := false;
      }
      j := j + 1;
    }
    
    if well_formed {
      var ts := event["timestamp"];
      
      // Check if this event is a duplicate of any kept event
      var is_dup := false;
      var k := 0;
      while k < |kept|
        invariant 0 <= k <= |kept|
      {
        var kept_event := kept[k];
        var kept_ts := kept_event["timestamp"];
        
        // Check if same composite key
        var same_key := true;
        var m := 0;
        while m < |key_fields|
          invariant 0 <= m <= |key_fields|
        {
          var field := key_fields[m];
          if !(field in kept_event) || !(field in event) || kept_event[field] != event[field] {
            same_key := false;
          }
          m := m + 1;
        }
        
        // Check if within window
        if same_key && ts >= kept_ts && ts - kept_ts < window_seconds {
          is_dup := true;
        }
        
        k := k + 1;
      }
      
      if !is_dup {
        kept := kept + [event];
      }
    }
    
    i := i + 1;
  }
  
  result := kept;
}
