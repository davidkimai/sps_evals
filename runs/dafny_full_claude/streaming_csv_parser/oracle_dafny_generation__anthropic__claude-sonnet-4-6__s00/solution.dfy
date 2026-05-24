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
        // First non-empty line is the header
        headers := SplitByComma(line);
        headerFound := true;
      } else {
        // Parse as a data row
        var cells := SplitByComma(line);
        var row: map<string, string> := map[];
        var j := 0;
        while j < |headers| && j < |cells|
          invariant 0 <= j <= |headers|
          invariant 0 <= j <= |cells|
        {
          row := row[headers[j] := cells[j]];
          j := j + 1;
        }
        // If fewer cells than headers, fill remaining with empty string
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
  // Example test
  var lines := ["name,age,city", "Alice,30,New York", "Bob,25,Boston", "", "Charlie,35,Chicago"];
  var rows := ParseCSVRows(lines);
  var i := 0;
  while i < |rows|
    invariant 0 <= i <= |rows|
  {
    print rows[i], "\n";
    i := i + 1;
  }
}
