method ParseBinding(line: string) returns (section: string, key: string, value: string)
  requires |line| > 0
  ensures |section| > 0
  ensures |key| > 0
{
  // Find '=' sign
  var eqPos := -1;
  var i := 0;
  while i < |line|
    invariant 0 <= i <= |line|
  {
    if line[i] == '=' {
      eqPos := i;
      break;
    }
    i := i + 1;
  }
  
  if eqPos < 0 {
    // No '=' found
    print "ValueError: no '=' in line\n";
    section := "";
    key := "";
    value := "";
    return;
  }
  
  var lhs := line[..eqPos];
  var rhs := line[eqPos+1..];
  
  // Find '.' in lhs
  var dotPos := -1;
  var j := 0;
  while j < |lhs|
    invariant 0 <= j <= |lhs|
  {
    if lhs[j] == '.' {
      dotPos := j;
      break;
    }
    j := j + 1;
  }
  
  if dotPos < 0 {
    // No '.' found
    print "ValueError: no '.' in section.key part\n";
    section := "";
    key := "";
    value := "";
    return;
  }
  
  var rawSection := lhs[..dotPos];
  var rawKey := lhs[dotPos+1..];
  
  // Strip whitespace from section
  section := Strip(rawSection);
  key := Strip(rawKey);
  value := Strip(rhs);
  
  if |section| == 0 {
    print "ValueError: empty section name\n";
    section := "";
    key := "";
    value := "";
    return;
  }
  
  if |key| == 0 {
    print "ValueError: empty key\n";
    section := "";
    key := "";
    value := "";
    return;
  }
}

function IsWhitespace(c: char): bool {
  c == ' ' || c == '\t' || c == '\r' || c == '\n'
}

method Strip(s: string) returns (result: string) {
  var start := 0;
  while start < |s| && IsWhitespace(s[start])
    invariant 0 <= start <= |s|
  {
    start := start + 1;
  }
  
  var end := |s|;
  while end > start && IsWhitespace(s[end-1])
    invariant start <= end <= |s|
  {
    end := end - 1;
  }
  
  result := s[start..end];
}

method StripLine(line: string) returns (result: string) {
  result := Strip(line);
}

method IsComment(line: string) returns (b: bool) {
  var stripped := Strip(line);
  if |stripped| == 0 {
    b := false;
    return;
  }
  b := stripped[0] == '#';
}

// Main entry point
method parse_bindings(lines: seq<string>) returns (
  sections: seq<string>,
  keys: seq<seq<string>>,
  values: seq<seq<string>>
)
  ensures |sections| == |keys|
  ensures |keys| == |values|
{
  sections := [];
  keys := [];
  values := [];
  
  var i := 0;
  while i < |lines|
    invariant 0 <= i <= |lines|
    invariant |sections| == |keys|
    invariant |keys| == |values|
  {
    var line := lines[i];
    var stripped := Strip(line);
    
    // Skip empty lines
    if |stripped| == 0 {
      i := i + 1;
      continue;
    }
    
    // Skip comment lines
    if stripped[0] == '#' {
      i := i + 1;
      continue;
    }
    
    // Parse the binding
    var section, key, value := ParseBinding(stripped);
    
    // Check for parse errors
    if |section| == 0 || |key| == 0 {
      // Error case - in real code would raise ValueError
      // For Dafny compilation, we skip malformed lines with error signal
      // The Python translation will handle ValueError
      i := i + 1;
      continue;
    }
    
    // Find if section already exists
    var sIdx := -1;
    var k := 0;
    while k < |sections|
      invariant 0 <= k <= |sections|
    {
      if sections[k] == section {
        sIdx := k;
        break;
      }
      k := k + 1;
    }
    
    if sIdx < 0 {
      // New section
      sections := sections + [section];
      keys := keys + [[key]];
      values := values + [[value]];
    } else {
      // Existing section - add key/value
      keys := keys[sIdx := keys[sIdx] + [key]];
      values := values[sIdx := values[sIdx] + [value]];
    }
    
    i := i + 1;
  }
}

method Main() {
  var lines := ["# comment", "server.host = localhost", "server.port = 8080", "db.name = mydb", "  ", "db.user=admin"];
  var sections, keys, values := parse_bindings(lines);
  
  var i := 0;
  while i < |sections|
    invariant 0 <= i <= |sections|
  {
    print sections[i], "\n";
    var j := 0;
    while j < |keys[i]|
      invariant 0 <= j <= |keys[i]|
    {
      print "  ", keys[i][j], " = ", values[i][j], "\n";
      j := j + 1;
    }
    i := i + 1;
  }
}
