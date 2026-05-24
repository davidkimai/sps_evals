method extract_fields(record: map<string, object?>, paths: map<string, string>, default: object?) returns (result: map<string, object?>)
  ensures forall k :: k in paths ==> k in result
{
  result := map[];
  var keys := paths.Keys;
  while keys != {}
    decreases |keys|
  {
    var k :| k in keys;
    keys := keys - {k};
    var path := paths[k];
    var value := resolve_path(record, path, default);
    result := result[k := value];
  }
}

method resolve_path(record: map<string, object?>, path: string, default: object?) returns (result: object?)
{
  var parts := split_dots(path);
  if |parts| == 0 {
    result := default;
    return;
  }
  
  var current: object? := record;
  var i := 0;
  while i < |parts|
    decreases |parts| - i
  {
    var part := parts[i];
    if current == null {
      result := default;
      return;
    }
    // Try to navigate into the current object using the part
    var next := navigate(current, part);
    if next == null && !can_be_null(current, part) {
      result := default;
      return;
    }
    current := next;
    i := i + 1;
  }
  result := current;
}

// Placeholder navigation - in compiled Python this will use actual dict/list access
method navigate(obj: object?, key: string) returns (result: object?)
{
  result := null;
}

predicate can_be_null(obj: object?, key: string)
{
  true
}

method split_dots(s: string) returns (parts: seq<string>)
  ensures |parts| >= 0
{
  parts := [];
  var current := "";
  var i := 0;
  while i < |s|
    decreases |s| - i
  {
    if s[i] == '.' {
      parts := parts + [current];
      current := "";
    } else {
      current := current + [s[i]];
    }
    i := i + 1;
  }
  if |s| > 0 || current != "" {
    parts := parts + [current];
  }
}

method Main()
{
  // Basic test
  var record: map<string, object?> := map[];
  var paths: map<string, string> := map["x" := "a.b"];
  var result := extract_fields(record, paths, null);
  assert "x" in result;
}
