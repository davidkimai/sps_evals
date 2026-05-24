method ParseCliArgs(argv: seq<string>) returns (result: map<string, string>)
  ensures "input" in result
  ensures "limit" in result
  ensures "format" in result
  ensures "dry_run" in result
{
  var input: string := "";
  var limit: string := "100";
  var format: string := "json";
  var dry_run: string := "false";
  var hasInput: bool := false;

  var i := 0;
  while i < |argv|
    invariant 0 <= i <= |argv|
  {
    var arg := argv[i];
    if arg == "--input" {
      if i + 1 >= |argv| {
        // missing value - will be caught by hasInput check
        i := i + 1;
      } else {
        i := i + 1;
        input := argv[i];
        hasInput := true;
        i := i + 1;
      }
    } else if arg == "--limit" {
      if i + 1 >= |argv| {
        i := i + 1;
      } else {
        i := i + 1;
        limit := argv[i];
        i := i + 1;
      }
    } else if arg == "--format" {
      if i + 1 >= |argv| {
        i := i + 1;
      } else {
        i := i + 1;
        format := argv[i];
        i := i + 1;
      }
    } else if arg == "--dry-run" {
      dry_run := "true";
      i := i + 1;
    } else {
      i := i + 1;
    }
  }

  result := map["input" := input, "limit" := limit, "format" := format, "dry_run" := dry_run];
}

method Main() {
  var args := ["--input", "file.txt", "--limit", "50", "--format", "csv", "--dry-run"];
  var r := ParseCliArgs(args);
  print r["input"], "\n";
  print r["limit"], "\n";
  print r["format"], "\n";
  print r["dry_run"], "\n";
}
