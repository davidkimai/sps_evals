method serialize_record(record: map<string, string>, format: string) returns (result: string)
  requires format == "json" || format == "csv" || format == "toml"
  ensures |result| > 0
{
  if format == "json" {
    result := SerializeJSON(record);
  } else if format == "csv" {
    result := SerializeCSV(record);
  } else {
    result := SerializeTOML(record);
  }
}

method GetSortedKeys(m: map<string, string>) returns (keys: seq<string>)
  ensures forall k :: k in keys <==> k in m
  ensures forall i, j :: 0 <= i < j < |keys| ==> keys[i] < keys[j]
{
  keys := [];
  var remaining := m.Keys;
  while remaining != {}
    decreases |remaining|
    invariant forall k :: k in keys ==> k in m
    invariant forall k :: k in remaining ==> k in m
    invariant forall k :: k in m ==> k in keys || k in remaining
    invariant forall i, j :: 0 <= i < j < |keys| ==> keys[i] < keys[j]
    invariant forall k :: k in keys ==> k !in remaining
  {
    // Pick the lexicographically smallest key
    var minKey: string;
    var first := true;
    var iter := remaining;
    minKey := "";
    // Get an arbitrary element first
    var anyKey :| anyKey in remaining;
    minKey := anyKey;
    // Find minimum
    var toCheck := remaining - {anyKey};
    while toCheck != {}
      decreases |toCheck|
      invariant minKey in remaining
    {
      var k :| k in toCheck;
      if k < minKey {
        minKey := k;
      }
      toCheck := toCheck - {k};
    }
    keys := keys + [minKey];
    remaining := remaining - {minKey};
  }
}

method EscapeJSONString(s: string) returns (result: string)
{
  result := "";
  var i := 0;
  while i < |s|
    decreases |s| - i
  {
    if s[i] == '"' {
      result := result + "\\\"";
    } else if s[i] == '\\' {
      result := result + "\\\\";
    } else {
      result := result + [s[i]];
    }
    i := i + 1;
  }
}

method SerializeJSON(record: map<string, string>) returns (result: string)
  ensures |result| > 0
{
  var keys := GetSortedKeys(record);
  result := "{";
  var i := 0;
  while i < |keys|
    decreases |keys| - i
  {
    var key := keys[i];
    var value := record[key];
    var escapedKey := EscapeJSONString(key);
    var escapedValue := EscapeJSONString(value);
    if i > 0 {
      result := result + ", ";
    }
    result := result + "\"" + escapedKey + "\": \"" + escapedValue + "\"";
    i := i + 1;
  }
  result := result + "}";
}

method SerializeCSV(record: map<string, string>) returns (result: string)
  ensures |result| > 0
{
  var keys := GetSortedKeys(record);
  // Header row
  var header := "";
  var values := "";
  var i := 0;
  while i < |keys|
    decreases |keys| - i
  {
    var key := keys[i];
    if i > 0 {
      header := header + ",";
      values := values + ",";
    }
    header := header + key;
    values := values + record[key];
    i := i + 1;
  }
  if |keys| == 0 {
    result := "\n";
  } else {
    result := header + "\n" + values + "\n";
  }
}

method SerializeTOML(record: map<string, string>) returns (result: string)
  ensures |result| > 0
{
  var keys := GetSortedKeys(record);
  result := "";
  var i := 0;
  while i < |keys|
    decreases |keys| - i
  {
    var key := keys[i];
    var value := record[key];
    result := result + key + " = \"" + value + "\"\n";
    i := i + 1;
  }
  if result == "" {
    result := "\n";
  }
}
