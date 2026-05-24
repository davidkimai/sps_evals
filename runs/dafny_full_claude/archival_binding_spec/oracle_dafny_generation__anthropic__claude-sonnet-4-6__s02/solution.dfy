method TrimLeft(s: string) returns (r: string)
  ensures |r| <= |s|
  ensures forall i :: 0 <= i < |r| ==> r[i] == s[|s| - |r| + i]
{
  var i := 0;
  while i < |s| && (s[i] == ' ' || s[i] == '\t' || s[i] == '\r' || s[i] == '\n')
    invariant 0 <= i <= |s|
  {
    i := i + 1;
  }
  r := s[i..];
}

method TrimRight(s: string) returns (r: string)
  ensures |r| <= |s|
{
  var i := |s|;
  while i > 0 && (s[i-1] == ' ' || s[i-1] == '\t' || s[i-1] == '\r' || s[i-1] == '\n')
    invariant 0 <= i <= |s|
  {
    i := i - 1;
  }
  r := s[..i];
}

method Trim(s: string) returns (r: string)
{
  var t := TrimLeft(s);
  r := TrimRight(t);
}

method FindChar(s: string, c: char, start: int) returns (idx: int)
  requires 0 <= start <= |s|
  ensures idx == -1 || (start <= idx < |s| && s[idx] == c)
{
  var i := start;
  while i < |s|
    invariant start <= i <= |s|
  {
    if s[i] == c {
      return i;
    }
    i := i + 1;
  }
  return -1;
}

// We'll represent the result as parallel arrays for sections and their key/value pairs
// Since Dafny doesn't have Python dicts natively, we'll model this carefully
// and rely on the compiled output being translated to Python

method parse_bindings(lines: seq<string>) returns (
  sectionKeys: seq<string>,
  entryKeys: seq<seq<string>>,
  entryVals: seq<seq<string>>,
  error: string
)
  ensures error != "" || |sectionKeys| == |entryKeys| == |entryVals|
{
  var sk: seq<string> := [];
  var ek: seq<seq<string>> := [];
  var ev: seq<seq<string>> := [];
  
  var lineIdx := 0;
  while lineIdx < |lines|
    invariant |sk| == |ek| == |ev|
    invariant 0 <= lineIdx <= |lines|
  {
    var line := lines[lineIdx];
    var trimmed := Trim(line);
    
    if |trimmed| == 0 || trimmed[0] == '#' {
      lineIdx := lineIdx + 1;
      continue;
    }
    
    // Find '=' separator
    var eqIdx := FindChar(trimmed, '=', 0);
    if eqIdx == -1 {
      return [], [], [], "ValueError: malformed line (no '='): " + trimmed;
    }
    
    var lhs := trimmed[..eqIdx];
    var rhs := trimmed[eqIdx+1..];
    
    // Find '.' in lhs
    var dotIdx := FindChar(lhs, '.', 0);
    if dotIdx == -1 {
      return [], [], [], "ValueError: malformed line (no '.' in key): " + trimmed;
    }
    
    var sectionRaw := lhs[..dotIdx];
    var keyRaw := lhs[dotIdx+1..];
    
    var section := Trim(sectionRaw);
    var key := Trim(keyRaw);
    var value := Trim(rhs);
    
    if |section| == 0 {
      return [], [], [], "ValueError: empty section name";
    }
    if |key| == 0 {
      return [], [], [], "ValueError: empty key";
    }
    
    // Find or create section
    var secIdx := -1;
    var si := 0;
    while si < |sk|
      invariant 0 <= si <= |sk|
    {
      if sk[si] == section {
        secIdx := si;
        break;
      }
      si := si + 1;
    }
    
    if secIdx == -1 {
      sk := sk + [section];
      ek := ek + [[key]];
      ev := ev + [[value]];
    } else {
      // Add or update key in existing section
      var existingKeys := ek[secIdx];
      var existingVals := ev[secIdx];
      var ki := 0;
      var found := false;
      while ki < |existingKeys|
        invariant 0 <= ki <= |existingKeys|
      {
        if existingKeys[ki] == key {
          existingVals := existingVals[..ki] + [value] + existingVals[ki+1..];
          found := true;
          break;
        }
        ki := ki + 1;
      }
      if !found {
        existingKeys := existingKeys + [key];
        existingVals := existingVals + [value];
      }
      ek := ek[..secIdx] + [existingKeys] + ek[secIdx+1..];
      ev := ev[..secIdx] + [existingVals] + ev[secIdx+1..];
    }
    
    lineIdx := lineIdx + 1;
  }
  
  return sk, ek, ev, "";
}
