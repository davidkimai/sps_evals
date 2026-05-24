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
    
    var typeTag := schema[field].0;
    var defaultVal := schema[field].1;
    
    if field in raw {
      var rawVal := raw[field];
      var castVal := cast_value(typeTag, rawVal);
      if castVal.None? {
        // In the compiled Python, this will raise ValueError
        // For Dafny verification we need to handle this
        result := result[field := "ERROR:" + field];
      } else {
        result := result[field := castVal.value];
      }
    } else {
      result := result[field := defaultVal];
    }
  }
}

datatype Option<T> = None | Some(value: T)

function cast_value(typeTag: string, rawVal: string): Option<string>
{
  if typeTag == "int" then
    if is_valid_int(rawVal) then Some(rawVal)
    else None
  else if typeTag == "float" then
    if is_valid_float(rawVal) then Some(rawVal)
    else None
  else if typeTag == "str" then
    Some(rawVal)
  else if typeTag == "bool" then
    if rawVal == "true" || rawVal == "false" || rawVal == "True" || rawVal == "False" || rawVal == "1" || rawVal == "0" then
      Some(rawVal)
    else None
  else
    Some(rawVal)
}

predicate is_valid_int(s: string)
{
  |s| > 0 &&
  (s[0] == '-' || ('0' <= s[0] <= '9')) &&
  (|s| == 1 || s[0] != '-' || |s| > 1) &&
  forall i :: 1 <= i < |s| ==> '0' <= s[i] <= '9'
}

predicate is_valid_float(s: string)
{
  |s| > 0
}
