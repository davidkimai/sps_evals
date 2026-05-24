method resolve_flags(
  defaults: map<string, bool>,
  segments: map<string, map<string, bool>>,
  user: map<string, seq<string>>,
  user_overrides: map<string, bool>
) returns (result: map<string, bool>)
{
  result := defaults;

  if "segments" in user {
    var seg_list := user["segments"];
    var i := 0;
    while i < |seg_list|
      invariant 0 <= i <= |seg_list|
    {
      var seg_name := seg_list[i];
      if seg_name in segments {
        var seg_overrides := segments[seg_name];
        var keys := seg_overrides.Keys;
        var ks := set k | k in keys;
        var ks_seq: seq<string> := [];
        // iterate over segment overrides
        var remaining := ks;
        while |remaining| > 0
          invariant remaining <= ks
        {
          var k :| k in remaining;
          result := result[k := seg_overrides[k]];
          remaining := remaining - {k};
        }
      }
      i := i + 1;
    }
  }

  // Apply user overrides
  var override_keys := user_overrides.Keys;
  var remaining2 := set k | k in override_keys;
  while |remaining2| > 0
    invariant remaining2 <= override_keys
  {
    var k :| k in remaining2;
    result := result[k := user_overrides[k]];
    remaining2 := remaining2 - {k};
  }
}
