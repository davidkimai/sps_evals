method coerce_schema(raw: map<string, string>, schema: map<string, (string, string)>) returns (result: map<string, string>)
  ensures forall k :: k in schema ==> k in result
{
  result := map[];
  
  var schemaKeys := schema.Keys;
  
  while schemaKeys != {}
    invariant forall k :: k in result ==> k in schema
    decreases |schemaKeys|
  {
    var field :| field in schemaKeys;
    schemaKeys := schemaKeys - {field};
    
    var typeHint := schema[field].0;
    var defaultVal := schema[field].1;
    
    if field in raw {
      var rawVal := raw[field];
      var coerced := ApplyCoercion(typeHint, rawVal);
      result := result[field := coerced];
    } else {
      result := result[field := defaultVal];
    }
  }
}

method ApplyCoercion(typeHint: string, value: string) returns (result: string)
{
  if typeHint == "int" {
    var ok, n := ParseInt(value);
    if ok {
      result := IntToString(n);
    } else {
      result := value;
    }
  } else if typeHint == "float" {
    result := value;
  } else if typeHint == "str" {
    result := value;
  } else if typeHint == "bool" {
    if value == "true" || value == "True" || value == "1" {
      result := "True";
    } else if value == "false" || value == "False" || value == "0" {
      result := "False";
    } else {
      result := value;
    }
  } else {
    result := value;
  }
}

method ParseInt(s: string) returns (ok: bool, n: int)
{
  if |s| == 0 {
    ok := false;
    n := 0;
    return;
  }
  
  var i := 0;
  var negative := false;
  var result := 0;
  
  if s[0] == '-' {
    negative := true;
    i := 1;
  } else if s[0] == '+' {
    i := 1;
  }
  
  if i >= |s| {
    ok := false;
    n := 0;
    return;
  }
  
  var hasDigit := false;
  while i < |s|
    decreases |s| - i
  {
    var c := s[i];
    if '0' <= c <= '9' {
      result := result * 10 + (c as int - '0' as int);
      hasDigit := true;
    } else {
      ok := false;
      n := 0;
      return;
    }
    i := i + 1;
  }
  
  if !hasDigit {
    ok := false;
    n := 0;
    return;
  }
  
  ok := true;
  if negative {
    n := -result;
  } else {
    n := result;
  }
}

method IntToString(n: int) returns (s: string)
{
  if n == 0 {
    s := "0";
    return;
  }
  
  var negative := n < 0;
  var m := if negative then -n else n;
  var digits := "";
  
  while m > 0
    decreases m
  {
    var d := m % 10;
    var c := ('0' as int + d) as char;
    digits := [c] + digits;
    m := m / 10;
  }
  
  if negative {
    s := "-" + digits;
  } else {
    s := digits;
  }
}
