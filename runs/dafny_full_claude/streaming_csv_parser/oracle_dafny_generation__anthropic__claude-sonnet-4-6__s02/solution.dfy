method SplitByComma(s: string) returns (parts: seq<string>)
  ensures |parts| >= 1
{
  var result: seq<string> := [];
  var current: string := "";
  var i := 0;
  while i < |s|
    invariant 0 <= i <= |s|
  {
    if s[i] == ',' {
      result := result + [current];
      current := "";
    } else {
      current := current + [s[i]];
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
    invariant headerFound ==> |headers| >= 1
  {
    var line := lines[i];
    if |line| > 0 {
      if !headerFound {
        headers := SplitByComma(line);
        headerFound := true;
      } else {
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
  var lines := ["name,age,city", "Alice,30,New York", "Bob,25,London", "", "Carol,35,Paris"];
  var rows := ParseCSVRows(lines);
  var i := 0;
  while i < |rows|
    invariant 0 <= i <= |rows|
  {
    print rows[i], "\n";
    i := i + 1;
  }
}
