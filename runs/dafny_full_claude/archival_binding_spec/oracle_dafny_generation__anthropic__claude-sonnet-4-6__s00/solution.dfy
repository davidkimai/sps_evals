method ParseBinding(line: string) returns (section: string, key: string, value: string)
  requires |line| > 0
  ensures |section| > 0
  ensures |key| > 0
{
  // Find '='
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
  if eqPos == -1 {
    // No '=' found
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
  if dotPos == -1 {
    section := "";
    key := "";
    value := "";
    return;
  }
  
  var rawSection := lhs[..dotPos];
  var rawKey := lhs[dotPos+1..];
  
  section := Strip(rawSection);
  key := Strip(rawKey);
  value := Strip(rhs);
  
  if |section| == 0 || |key| == 0 {
    section := "";
    key := "";
    value := "";
  }
}

function method IsWhitespace(c: char): bool
{
  c == ' ' || c == '\t' || c == '\r' || c == '\n'
}

method Strip(s: string) returns (result: string)
{
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

method IsCommentOrEmpty(line: string) returns (result: bool)
{
  var stripped := Strip(line);
  if |stripped| == 0 {
    result := true;
    return;
  }
  if stripped[0] == '#' {
    result := true;
    return;
  }
  result := false;
}

method ParseBindings(lines: seq<string>) returns (
  sections: seq<string>,
  keys: seq<seq<string>>,
  values: seq<seq<string>>,
  success: bool,
  errorMsg: string
)
  ensures success ==> |sections| == |keys| == |values|
{
  sections := [];
  keys := [];
  values := [];
  success := true;
  errorMsg := "";
  
  var sectionOrder: seq<string> := [];
  var sectionKeys: seq<seq<string>> := [];
  var sectionValues: seq<seq<string>> := [];
  
  var i := 0;
  while i < |lines|
    invariant 0 <= i <= |lines|
    invariant |sectionOrder| == |sectionKeys| == |sectionValues|
  {
    var line := lines[i];
    var skip := IsCommentOrEmpty(line);
    if !skip {
      var sec, k, v := ParseBinding(line);
      if |sec| == 0 || |k| == 0 {
        success := false;
        errorMsg := "Malformed line or empty section/key";
        return;
      }
      
      // Find section index
      var secIdx := -1;
      var si := 0;
      while si < |sectionOrder|
        invariant 0 <= si <= |sectionOrder|
      {
        if sectionOrder[si] == sec {
          secIdx := si;
          break;
        }
        si := si + 1;
      }
      
      if secIdx == -1 {
        sectionOrder := sectionOrder + [sec];
        sectionKeys := sectionKeys + [[k]];
        sectionValues := sectionValues + [[v]];
      } else {
        sectionKeys := sectionKeys[secIdx := sectionKeys[secIdx] + [k]];
        sectionValues := sectionValues[secIdx := sectionValues[secIdx] + [v]];
      }
    }
    i := i + 1;
  }
  
  sections := sectionOrder;
  keys := sectionKeys;
  values := sectionValues;
  success := true;
}

method Main()
{
  var lines := ["[header]", "# comment", "sec1.key1 = val1", "sec1.key2=val2", "sec2.keyA = valA"];
  var sections, keys, values, ok, err := ParseBindings(lines);
  if ok {
    print "Success\n";
    var i := 0;
    while i < |sections| {
      print "Section: ", sections[i], "\n";
      var j := 0;
      while j < |keys[i]| {
        print "  ", keys[i][j], " = ", values[i][j], "\n";
        j := j + 1;
      }
      i := i + 1;
    }
  } else {
    print "Error: ", err, "\n";
  }
}
