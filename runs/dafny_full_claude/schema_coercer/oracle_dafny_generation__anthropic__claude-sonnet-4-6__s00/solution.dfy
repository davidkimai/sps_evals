method coerce_schema(raw: map<string, string>, schema: map<string, (string, string)>) returns (result: map<string, string>)
  ensures forall k :: k in schema ==> k in result
{
  result := map[];
  
  var schemaKeys := schema.Keys;
  
  while schemaKeys != {}
    invariant forall k :: k in result ==> k in schema
    decreases schemaKeys
  {
    var field :| field in schemaKeys;
    schemaKeys := schemaKeys - {field};
    
    var typeCallable := schema[field].0;
    var defaultVal := schema[field].1;
    
    if field in raw {
      var rawVal := raw[field];
      var coerced := ApplyCoercion(typeCallable, rawVal, field);
      result := result[field := coerced];
    } else {
      result := result[field := defaultVal];
    }
  }
}

method ApplyCoercion(typeCallable: string, value: string, fieldName: string) returns (result: string)
{
  if typeCallable == "int" {
    var ok, v := ParseInt(value);
    if !ok {
      // In the compiled Python, this will raise ValueError
      result := "__ValueError__:" + fieldName;
    } else {
      result := IntToString(v);
    }
  } else if typeCallable == "float" {
    var ok, v := ParseFloat(value);
    if !ok {
      result := "__ValueError__:" + fieldName;
    } else {
      result := v;
    }
  } else if typeCallable == "str" {
    result := value;
  } else if typeCallable == "bool" {
    var ok, v := ParseBool(value);
    if !ok {
      result := "__ValueError__:" + fieldName;
    } else {
      result := v;
    }
  } else {
    result := value;
  }
}

method ParseInt(s: string) returns (ok: bool, value: int)
{
  if |s| == 0 {
    ok := false;
    value := 0;
    return;
  }
  
  var start := 0;
  var negative := false;
  
  if s[0] == '-' {
    negative := true;
    start := 1;
  } else if s[0] == '+' {
    start := 1;
  }
  
  if start >= |s| {
    ok := false;
    value := 0;
    return;
  }
  
  var acc := 0;
  var i := start;
  ok := true;
  
  while i < |s|
    invariant start <= i <= |s|
    decreases |s| - i
  {
    var c := s[i];
    if c >= '0' && c <= '9' {
      acc := acc * 10 + (c as int - '0' as int);
      i := i + 1;
    } else {
      ok := false;
      value := 0;
      return;
    }
  }
  
  if negative {
    value := -acc;
  } else {
    value := acc;
  }
}

method IntToString(n: int) returns (s: string)
{
  if n == 0 {
    s := "0";
    return;
  }
  
  var negative := n < 0;
  var v := if negative then -n else n;
  var digits := "";
  
  while v > 0
    decreases v
  {
    var d := v % 10;
    var c := ('0' as int + d) as char;
    digits := [c] + digits;
    v := v / 10;
  }
  
  if negative {
    s := "-" + digits;
  } else {
    s := digits;
  }
}

method ParseFloat(s: string) returns (ok: bool, value: string)
{
  // Basic float validation: check digits, optional sign, optional dot
  if |s| == 0 {
    ok := false;
    value := "";
    return;
  }
  
  var start := 0;
  if s[0] == '-' || s[0] == '+' {
    start := 1;
  }
  
  if start >= |s| {
    ok := false;
    value := "";
    return;
  }
  
  var hasDot := false;
  var hasDigit := false;
  var i := start;
  
  while i < |s|
    invariant start <= i <= |s|
    decreases |s| - i
  {
    var c := s[i];
    if c >= '0' && c <= '9' {
      hasDigit := true;
      i := i + 1;
    } else if c == '.' && !hasDot {
      hasDot := true;
      i := i + 1;
    } else {
      ok := false;
      value := "";
      return;
    }
  }
  
  ok := hasDigit;
  value := s;
}

method ParseBool(s: string) returns (ok: bool, value: string)
{
  if s == "true" || s == "True" || s == "1" || s == "yes" {
    ok := true;
    value := "True";
  } else if s == "false" || s == "False" || s == "0" || s == "no" {
    ok := true;
    value := "False";
  } else {
    ok := false;
    value := "";
  }
}
