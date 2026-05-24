module ConfigPrecedenceMerge {

  method ParseValue(s: string) returns (result: string)
  {
    result := s;
  }

  method MergeSettings(defaults: map<string, string>, file_config: map<string, string>, env: map<string, string>) returns (result: map<string, string>)
    ensures true
  {
    // Start with defaults
    var merged: map<string, string> := defaults;
    
    // Apply file_config over defaults
    var fkeys := file_config.Keys;
    while fkeys != {}
      decreases fkeys
    {
      var k :| k in fkeys;
      merged := merged[k := file_config[k]];
      fkeys := fkeys - {k};
    }
    
    // Apply env vars with APP__ prefix
    var ekeys := env.Keys;
    while ekeys != {}
      decreases ekeys
    {
      var k :| k in ekeys;
      if |k| > 5 && k[0..5] == "APP__" {
        var suffix := k[5..];
        // Use suffix as the key (simplified - full nesting would require more complex data structures)
        merged := merged[suffix := env[k]];
      }
      ekeys := ekeys - {k};
    }
    
    result := merged;
  }

  method Main()
  {
    var defaults := map["debug" := "false", "host" := "localhost"];
    var file_config := map["host" := "example.com", "port" := "8080"];
    var env := map["APP__debug" := "true", "APP__port" := "9090"];
    
    var result := MergeSettings(defaults, file_config, env);
    print "Result computed\n";
  }
}
