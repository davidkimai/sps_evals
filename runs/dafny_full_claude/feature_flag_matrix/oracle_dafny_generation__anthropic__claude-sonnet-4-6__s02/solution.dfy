method resolve_flags(
    defaults: map<string, bool>,
    segments: map<string, map<string, bool>>,
    user: map<string, seq<string>>,
    user_overrides: map<string, bool>,
    user_segments: seq<string>
) returns (result: map<string, bool>)
    ensures forall k :: k in defaults ==> k in result
{
    result := defaults;
    
    // Apply segment overrides in order
    var i := 0;
    while i < |user_segments|
        invariant 0 <= i <= |user_segments|
        invariant forall k :: k in defaults ==> k in result
    {
        var seg_name := user_segments[i];
        if seg_name in segments {
            var seg := segments[seg_name];
            var merged := result;
            var keys := seg.Keys;
            // Apply all keys from this segment
            var seg_seq := SetToSeq(keys);
            var j := 0;
            while j < |seg_seq|
                invariant 0 <= j <= |seg_seq|
                invariant forall k :: k in defaults ==> k in merged
            {
                var key := seg_seq[j];
                merged := merged[key := seg[key]];
                j := j + 1;
            }
            result := merged;
        }
        i := i + 1;
    }
    
    // Apply user overrides
    var override_keys := user_overrides.Keys;
    var override_seq := SetToSeq(override_keys);
    var k := 0;
    while k < |override_seq|
        invariant 0 <= k <= |override_seq|
        invariant forall key :: key in defaults ==> key in result
    {
        var key := override_seq[k];
        result := result[key := user_overrides[key]];
        k := k + 1;
    }
}

method SetToSeq<T(==)>(s: set<T>) returns (result: seq<T>)
    ensures |result| == |s|
    ensures forall x :: x in result <==> x in s
    ensures forall i, j :: 0 <= i < j < |result| ==> result[i] != result[j]
{
    result := [];
    var remaining := s;
    while remaining != {}
        invariant forall x :: x in result <==> x in s && x !in remaining
        invariant forall i, j :: 0 <= i < j < |result| ==> result[i] != result[j]
        invariant |result| + |remaining| == |s|
        decreases remaining
    {
        var x :| x in remaining;
        result := result + [x];
        remaining := remaining - {x};
    }
}
