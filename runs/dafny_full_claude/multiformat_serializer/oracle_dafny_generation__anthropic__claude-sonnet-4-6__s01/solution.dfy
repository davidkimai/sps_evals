method serialize_record(record: map<string, string>, format: string) returns (result: string)
  requires format == "json" || format == "csv" || format == "toml"
  ensures |result| > 0
{
  if format == "json" {
    result := SerializeJson(record);
  } else if format == "csv" {
    result := SerializeCsv(record);
  } else {
    result := SerializeToml(record);
  }
}

method GetSortedKeys(record: map<string, string>) returns (keys: seq<string>)
  ensures forall k :: k in keys <==> k in record
  ensures forall i, j :: 0 <= i < j < |keys| ==> keys[i] < keys[j]
{
  keys := [];
  var remaining := record.Keys;
  while remaining != {}
    decreases |remaining|
  {
    // Pick the lexicographically smallest key
    var minKey: string;
    var firstPick := true;
    var iter := remaining;
    while iter != {}
      decreases |iter|
    {
      var k :| k in iter;
      if firstPick {
        minKey := k;
        firstPick := false;
      } else if k < minKey {
        minKey := k;
      }
      iter := iter - {k};
    }
    keys := keys + [minKey];
    remaining := remaining - {minKey};
  }
}

method SerializeJson(record: map<string, string>) returns (result: string)
  ensures |result| > 0
{
  var keys := GetSortedKeys(record);
  result := "{";
  var i := 0;
  while i < |keys|
    invariant 0 <= i <= |keys|
    invariant |result| > 0
  {
    var k := keys[i];
    var v := record[k];
    if i > 0 {
      result := result + ", ";
    }
    result := result + "\"" + k + "\": \"" + v + "\"";
    i := i + 1;
  }
  result := result + "}";
}

method SerializeCsv(record: map<string, string>) returns (result: string)
  ensures |result| > 0
{
  var keys := GetSortedKeys(record);
  var header := "";
  var row := "";
  var i := 0;
  while i < |keys|
    invariant 0 <= i <= |keys|
  {
    var k := keys[i];
    var v := record[k];
    if i > 0 {
      header := header + ",";
      row := row + ",";
    }
    header := header + k;
    row := row + v;
    i := i + 1;
  }
  if |keys| == 0 {
    result := "\n";
  } else {
    result := header + "\n" + row;
  }
}

method SerializeToml(record: map<string, string>) returns (result: string)
  ensures |result| > 0
{
  var keys := GetSortedKeys(record);
  result := "";
  var i := 0;
  while i < |keys|
    invariant 0 <= i <= |keys|
  {
    var k := keys[i];
    var v := record[k];
    result := result + k + " = \"" + v + "\"\n";
    i := i + 1;
  }
  if |keys| == 0 {
    result := "\n";
  }
}
