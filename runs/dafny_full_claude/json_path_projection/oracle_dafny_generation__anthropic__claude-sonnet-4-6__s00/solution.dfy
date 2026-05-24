method extract_fields(record: map<string, object?>, paths: map<string, string>, default: object?) returns (result: map<string, object?>)
  ensures forall k :: k in paths ==> k in result
{
  result := map[];
  var keys := paths.Keys;
  var keySeq := SetToSeq(keys);
  var i := 0;
  while i < |keySeq|
    invariant 0 <= i <= |keySeq|
    invariant forall j :: 0 <= j < i ==> keySeq[j] in result
  {
    var outKey := keySeq[i];
    var path := paths[outKey];
    var parts := SplitDot(path);
    var value := NavigatePath(record, parts, default);
    result := result[outKey := value];
    i := i + 1;
  }
}

function SetToSeq<T>(s: set<T>): seq<T>
  ensures |SetToSeq(s)| == |s|
  ensures forall x :: x in s ==> x in SetToSeq(s)
{
  if s == {} then []
  else
    var x :| x in s;
    [x] + SetToSeq(s - {x})
}

method SplitDot(path: string) returns (parts: seq<string>)
  ensures |parts| >= 1
{
  parts := [];
  var current := "";
  var i := 0;
  while i < |path|
    invariant 0 <= i <= |path|
  {
    if path[i] == '.' {
      parts := parts + [current];
      current := "";
    } else {
      current := current + [path[i]];
    }
    i := i + 1;
  }
  parts := parts + [current];
}

method NavigatePath(record: map<string, object?>, parts: seq<string>, default: object?) returns (value: object?)
{
  if |parts| == 0 {
    value := default;
    return;
  }
  
  var current: object? := record;
  var i := 0;
  
  while i < |parts|
    invariant 0 <= i <= |parts|
  {
    var part := parts[i];
    if current == null {
      value := default;
      return;
    }
    
    if current is map<string, object?> {
      var m := current as map<string, object?>;
      if part in m {
        current := m[part];
      } else {
        value := default;
        return;
      }
    } else if current is seq<object?> {
      var s := current as seq<object?>;
      var idx := ParseInt(part);
      if idx >= 0 && idx < |s| {
        current := s[idx];
      } else {
        value := default;
        return;
      }
    } else {
      value := default;
      return;
    }
    
    i := i + 1;
  }
  
  value := current;
}

method ParseInt(s: string) returns (result: int)
  ensures result >= -1
{
  if |s| == 0 {
    result := -1;
    return;
  }
  
  var i := 0;
  var n := 0;
  var valid := true;
  
  while i < |s|
    invariant 0 <= i <= |s|
  {
    var c := s[i];
    if c >= '0' && c <= '9' {
      n := n * 10 + (c as int - '0' as int);
    } else {
      valid := false;
      break;
    }
    i := i + 1;
  }
  
  if valid {
    result := n;
  } else {
    result := -1;
  }
}
