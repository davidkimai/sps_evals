method SplitByComma(line: string) returns (parts: seq<string>)
  ensures |parts| >= 1
{
  var result: seq<string> := [];
  var current: string := "";
  var i := 0;
  while i < |line|
    invariant 0 <= i <= |line|
  {
    if line[i] == ',' {
      result := result + [current];
      current := "";
    } else {
      current := current + [line[i]];
    }
    i := i + 1;
  }
  result := result + [current];
  parts := result;
}

method ParseCSVRows(lines: seq<string>) returns (rows: seq<map<string, string>>)
  ensures |rows| >= 0
{
  rows := [];
  var headers: seq<string> := [];
  var headerFound := false;
  var i := 0;

  while i < |lines|
    invariant 0 <= i <= |lines|
  {
    var line := lines[i];
    // Check if line is non-empty
    if |line| > 0 {
      if !headerFound {
        headers := SplitByComma(line);
        headerFound := true;
      } else {
        var cells := SplitByComma(line);
        var row: map<string, string> := map[];
        var j := 0;
        var limit := if |headers| < |cells| then |headers| else |cells|;
        while j < limit
          invariant 0 <= j <= limit
        {
          row := row[headers[j] := cells[j]];
          j := j + 1;
        }
        // Fill missing cells with empty string
        while j < |headers|
          invariant j <= |headers|
        {
          row := row[headers[j] := ""];
          j := j + 1;
        }
        rows := rows + [row];
      }
    }
    i := i + 1;
  }
}

method Main()
{
  var lines := ["name,age,city", "Alice,30,NYC", "Bob,25,LA", "", "Carol,35,Chicago"];
  var rows := ParseCSVRows(lines);
  var i := 0;
  while i < |rows|
    invariant 0 <= i <= |rows|
  {
    print rows[i], "\n";
    i := i + 1;
  }
}
