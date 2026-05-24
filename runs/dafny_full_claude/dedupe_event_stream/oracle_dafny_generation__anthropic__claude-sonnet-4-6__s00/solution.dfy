method dedupe_events(events: seq<map<string, string>>, key_fields: seq<string>, window_seconds: int) returns (result: seq<map<string, string>>)
  requires window_seconds >= 0
  ensures |result| <= |events|
{
  result := [];
  var kept: seq<map<string, string>> := [];
  
  var i := 0;
  while i < |events|
    invariant 0 <= i <= |events|
    invariant |kept| <= i
    invariant result == kept
  {
    var event := events[i];
    
    // Check if event has "timestamp" field
    if "timestamp" !in event {
      i := i + 1;
      continue;
    }
    
    // Check if event has all key fields
    var hasAllKeys := true;
    var k := 0;
    while k < |key_fields|
      invariant 0 <= k <= |key_fields|
    {
      if key_fields[k] !in event {
        hasAllKeys := false;
        break;
      }
      k := k + 1;
    }
    
    if !hasAllKeys {
      i := i + 1;
      continue;
    }
    
    // Parse timestamp (check it's a valid integer string)
    var tsStr := event["timestamp"];
    var tsValid, tsVal := ParseInt(tsStr);
    
    if !tsValid {
      i := i + 1;
      continue;
    }
    
    // Build composite key for this event
    var compositeKey := BuildCompositeKey(event, key_fields);
    
    // Check if this event is a duplicate of any kept event
    var isDuplicate := false;
    var j := 0;
    while j < |kept|
      invariant 0 <= j <= |kept|
    {
      var keptEvent := kept[j];
      var keptTsStr := keptEvent["timestamp"];
      var keptTsValid, keptTsVal := ParseInt(keptTsStr);
      
      if keptTsValid {
        var keptCompositeKey := BuildCompositeKey(keptEvent, key_fields);
        if keptCompositeKey == compositeKey {
          // Same composite key, check time window
          if tsVal >= keptTsVal && tsVal - keptTsVal < window_seconds {
            isDuplicate := true;
            break;
          }
        }
      }
      j := j + 1;
    }
    
    if !isDuplicate {
      kept := kept + [event];
      result := kept;
    }
    
    i := i + 1;
  }
}

method BuildCompositeKey(event: map<string, string>, key_fields: seq<string>) returns (key: string)
{
  key := "";
  var i := 0;
  while i < |key_fields|
    invariant 0 <= i <= |key_fields|
  {
    var field := key_fields[i];
    if field in event {
      key := key + field + "=" + event[field] + ";";
    }
    i := i + 1;
  }
}

method ParseInt(s: string) returns (valid: bool, value: int)
{
  if |s| == 0 {
    valid := false;
    value := 0;
    return;
  }
  
  var start := 0;
  var negative := false;
  
  if s[0] == '-' {
    if |s| == 1 {
      valid := false;
      value := 0;
      return;
    }
    negative := true;
    start := 1;
  }
  
  var result := 0;
  var i := start;
  var ok := true;
  
  while i < |s|
    invariant start <= i <= |s|
  {
    var c := s[i];
    if c < '0' || c > '9' {
      ok := false;
      break;
    }
    result := result * 10 + (c as int - '0' as int);
    i := i + 1;
  }
  
  if !ok || i == start {
    valid := false;
    value := 0;
  } else {
    valid := true;
    if negative {
      value := -result;
    } else {
      value := result;
    }
  }
}
