method extract_fields(record: map<string, object?>, paths: map<string, string>, default_val: object?) returns (result: map<string, object?>)
  ensures forall k :: k in paths ==> k in result
{
  result := map[];
  
  var keys := paths.Keys;
  
  while keys != {}
    decreases |keys|
  {
    var key :| key in keys;
    keys := keys - {key};
    
    var path := paths[key];
    var value := resolve_path(record, path, default_val);
    result := result[key := value];
  }
}

method resolve_path(record: map<string, object?>, path: string, default_val: object?) returns (result: object?)
{
  var parts := split_dots(path);
  
  if |parts| == 0 {
    result := default_val;
    return;
  }
  
  var current: object? := record;
  var i := 0;
  
  while i < |parts|
    decreases |parts| - i
  {
    var part := parts[i];
    
    if current == null {
      result := default_val;
      return;
    }
    
    if current is map<string, object?> {
      var m := current as map<string, object?>;
      if part in m {
        current := m[part];
      } else {
        result := default_val;
        return;
      }
    } else if current is seq<object?> {
      var s := current as seq<object?>;
      var idx := parse_int(part);
      if idx >= 0 && idx < |s| {
        current := s[idx];
      } else {
        result := default_val;
        return;
      }
    } else {
      result := default_val;
      return;
    }
    
    i := i + 1;
  }
  
  result := current;
}

function parse_int(s: string): int
{
  if |s| == 0 then -1
  else parse_int_helper(s, 0, 0)
}

function parse_int_helper(s: string, idx: int, acc: int): int
  decreases |s| - idx
{
  if idx >= |s| then acc
  else if s[idx] >= '0' && s[idx] <= '9' then
    parse_int_helper(s, idx + 1, acc * 10 + (s[idx] as int - '0' as int))
  else -1
}

method split_dots(s: string) returns (parts: seq<string>)
  ensures forall p :: p in parts ==> |p| >= 0
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
  
  parts := parts + [current];
}
