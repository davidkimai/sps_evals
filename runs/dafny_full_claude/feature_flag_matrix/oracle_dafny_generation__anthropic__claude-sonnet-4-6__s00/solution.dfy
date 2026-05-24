method resolve_flags(
    defaults: map<string, bool>,
    segments: map<string, map<string, bool>>,
    user: map<string, seq<string>>,
    user_overrides: map<string, bool>,
    user_segments: seq<string>
) returns (result: map<string, bool>)
    ensures true
{
    // Start from defaults
    result := defaults;
    
    // Apply segment overrides in order
    var i := 0;
    while i < |user_segments|
        invariant 0 <= i <= |user_segments|
        decreases |user_segments| - i
    {
        var seg_name := user_segments[i];
        if seg_name in segments {
            var seg_flags := segments[seg_name];
            // Apply all flags from this segment
            var keys := seg_flags.Keys;
            result := result + seg_flags;
        }
        i := i + 1;
    }
    
    // Apply user overrides
    result := result + user_overrides;
}
