method dedupe_events(events: seq<map<string, int>>, key_fields: seq<string>, window_seconds: int) returns (result: seq<map<string, int>>)
  requires window_seconds >= 0
  ensures |result| <= |events|
{
  result := [];
  var kept: seq<map<string, int>> := [];
  
  var i := 0;
  while i < |events|
    invariant 0 <= i <= |events|
    invariant |kept| <= i
    invariant |result| == |kept|
  {
    var event := events[i];
    
    // Check if event is well-formed: has "timestamp" and all key_fields
    var wellFormed := "timestamp" in event;
    
    if wellFormed {
      var j := 0;
      while j < |key_fields|
        invariant 0 <= j <= |key_fields|
        invariant wellFormed ==> (forall k :: 0 <= k < j ==> key_fields[k] in event)
      {
        if key_fields[j] !in event {
          wellFormed := false;
        }
        j := j + 1;
      }
    }
    
    if wellFormed {
      var ts := event["timestamp"];
      
      // Check if this event is a duplicate of any kept event
      var isDuplicate := false;
      var k := 0;
      while k < |kept|
        invariant 0 <= k <= |kept|
      {
        var prev := kept[k];
        var prevTs := prev["timestamp"];
        
        // Check if all key fields match
        var keysMatch := true;
        var m := 0;
        while m < |key_fields|
          invariant 0 <= m <= |key_fields|
        {
          if key_fields[m] in prev && key_fields[m] in event {
            if prev[key_fields[m]] != event[key_fields[m]] {
              keysMatch := false;
            }
          } else {
            keysMatch := false;
          }
          m := m + 1;
        }
        
        if keysMatch && ts - prevTs < window_seconds && ts >= prevTs {
          isDuplicate := true;
        }
        
        k := k + 1;
      }
      
      if !isDuplicate {
        kept := kept + [event];
        result := result + [event];
      }
    }
    
    i := i + 1;
  }
}
