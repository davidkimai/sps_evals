method serialize_record(record: map<string, string>, format: string) returns (result: string)
  requires format == "json" || format == "csv" || format == "toml"
  ensures |result| > 0
{
  if format == "json" {
    result := serialize_json(record);
  } else if format == "csv" {
    result := serialize_csv(record);
  } else {
    result := serialize_toml(record);
  }
}

method get_sorted_keys(record: map<string, string>) returns (keys: seq<string>)
  ensures forall k :: k in keys <==> k in record
  ensures forall i, j :: 0 <= i < j < |keys| ==> keys[i] < keys[j]
{
  keys := [];
  var remaining := record.Keys;
  while remaining != {}
    decreases |remaining|
    invariant forall k :: k in keys ==> k in record
    invariant forall k :: k in remaining ==> k in record
    invariant forall k :: k in record ==> k in keys || k in remaining
    invariant forall i, j :: 0 <= i < j < |keys| ==> keys[i] < keys[j]
    invariant forall k :: k in keys ==> k !in remaining
  {
    var min_key := pick_min(remaining);
    keys := keys + [min_key];
    remaining := remaining - {min_key};
  }
}

function pick_min(s: set<string>): string
  requires s != {}
  ensures pick_min(s) in s
  ensures forall k :: k in s ==> pick_min(s) <= k
{
  var x :| x in s;
  if forall k :: k in s ==> x <= k then
    x
  else
    var smaller := set k | k in s && k < x;
    pick_min_helper(s, x)
}

function pick_min_helper(s: set<string>, candidate: string): string
  requires s != {}
  requires candidate in s
  ensures pick_min_helper(s, candidate) in s
  ensures forall k :: k in s ==> pick_min_helper(s, candidate) <= k
  decreases |set k | k in s && k < candidate|
{
  if forall k :: k in s ==> candidate <= k then
    candidate
  else
    var smaller :| smaller in s && smaller < candidate;
    pick_min_helper(s, smaller)
}

method serialize_json(record: map<string, string>) returns (result: string)
  ensures |result| > 0
{
  var keys := get_sorted_keys(record);
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

method serialize_csv(record: map<string, string>) returns (result: string)
  ensures |result| > 0
{
  var keys := get_sorted_keys(record);
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
  result := header + "\n" + row + "\n";
  if |result| == 0 {
    result := "\n\n";
  }
}

method serialize_toml(record: map<string, string>) returns (result: string)
  ensures |result| > 0
{
  var keys := get_sorted_keys(record);
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
  if result == "" {
    result := "\n";
  }
}
