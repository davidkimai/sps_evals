module ConfigPrecedenceMerge {

  // We'll implement this using Dafny's built-in map type
  // and represent nested settings as a flat structure with path-based keys
  // Since Dafny doesn't have dynamic typing, we'll translate to Python directly

  method Main() {
    // Test basic functionality
    var defaults: map<string, string> := map["debug" := "false", "port" := "8080"];
    var result := MergeFlat(defaults, map["port" := "9090"], map["APP__DEBUG" := "true"]);
    print result, "\n";
  }

  method MergeFlat(defaults: map<string, string>, file_config: map<string, string>, env: map<string, string>) 
    returns (result: map<string, string>)
  {
    result := defaults;
    // Apply file_config over defaults
    var fc_keys := file_config.Keys;
    // merge file_config
    result := MergeMaps(result, file_config);
    // Apply env vars
    result := ApplyEnv(result, env);
  }

  method MergeMaps(base: map<string, string>, overlay: map<string, string>) 
    returns (result: map<string, string>)
  {
    result := base;
    var keys := overlay.Keys;
    // In Dafny we iterate over sets
    while keys != {}
      decreases |keys|
    {
      var k :| k in keys;
      result := result[k := overlay[k]];
      keys := keys - {k};
    }
  }

  method ApplyEnv(base: map<string, string>, env: map<string, string>)
    returns (result: map<string, string>)
  {
    result := base;
    var keys := env.Keys;
    while keys != {}
      decreases |keys|
    {
      var k :| k in keys;
      if |k| > 5 && k[0..5] == "APP__" {
        var rest := k[5..];
        var lower := ToLower(rest);
        result := result[lower := env[k]];
      }
      keys := keys - {k};
    }
  }

  function ToLower(s: string): string {
    if s == "" then ""
    else [ToLowerChar(s[0])] + ToLower(s[1..])
  }

  function ToLowerChar(c: char): char {
    if 'A' <= c <= 'Z' then c + ('a' - 'A') else c
  }
}
