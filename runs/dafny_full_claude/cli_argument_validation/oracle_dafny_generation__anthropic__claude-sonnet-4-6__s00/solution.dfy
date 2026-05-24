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

  var i: int := 0;
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
        var val := argv[i];
        if |val| >= 2 && val[0] == '-' && val[1] == '-' {
          // next arg is a flag, not a value
          hasInput := false;
        } else {
          input := val;
          hasInput := true;
          i := i + 1;
        }
      }
    } else if arg == "--limit" {
      if i + 1 >= |argv| {
        limit := "";
        i := i + 1;
      } else {
        i := i + 1;
        var val := argv[i];
        if |val| >= 2 && val[0] == '-' && val[1] == '-' {
          limit := "";
        } else {
          limit := val;
          i := i + 1;
        }
      }
    } else if arg == "--format" {
      if i + 1 >= |argv| {
        format := "";
        i := i + 1;
      } else {
        i := i + 1;
        var val := argv[i];
        if |val| >= 2 && val[0] == '-' && val[1] == '-' {
          format := "";
        } else {
          format := val;
          i := i + 1;
        }
      }
    } else if arg == "--dry-run" {
      dry_run := "true";
      i := i + 1;
    } else {
      // unknown flag - signal error
      result := map["input" := "", "limit" := "", "format" := "", "dry_run" := "error_unknown:" + arg];
      return;
    }
  }

  if !hasInput {
    result := map["input" := "", "limit" := "", "format" := "", "dry_run" := "error_missing_input"];
    return;
  }

  result := map["input" := input, "limit" := limit, "format" := format, "dry_run" := dry_run];
}

method Main() {
  // Test basic functionality
  var argv1 := ["--input", "file.txt"];
  var r1 := ParseCliArgs(argv1);
  print r1["input"], "\n";
  print r1["limit"], "\n";
  print r1["format"], "\n";
  print r1["dry_run"], "\n";
}
