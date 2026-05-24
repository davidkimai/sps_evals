method correlate_events(events: seq<(int, string, string)>, within: int) 
    returns (result: seq<(int, int)>)
    requires within >= 0
    ensures forall k :: 0 <= k < |result| ==> 
        result[k].0 < |events| && result[k].1 < |events|
    ensures forall k :: 0 <= k < |result| ==>
        events[result[k].0].2 == "A" && events[result[k].1].2 == "B"
    ensures forall k :: 0 <= k < |result| ==>
        events[result[k].0].1 == events[result[k].1].1
    ensures forall k :: 0 <= k < |result| ==>
        events[result[k].1].0 - events[result[k].0].0 >= 0 &&
        events[result[k].1].0 - events[result[k].0].0 <= within
{
    result := [];
    var usedB: set<int> := {};
    var i := 0;
    while i < |events|
        invariant 0 <= i <= |events|
        invariant forall k :: 0 <= k < |result| ==> 
            result[k].0 < |events| && result[k].1 < |events|
        invariant forall k :: 0 <= k < |result| ==>
            events[result[k].0].2 == "A" && events[result[k].1].2 == "B"
        invariant forall k :: 0 <= k < |result| ==>
            events[result[k].0].1 == events[result[k].1].1
        invariant forall k :: 0 <= k < |result| ==>
            events[result[k].1].0 - events[result[k].0].0 >= 0 &&
            events[result[k].1].0 - events[result[k].0].0 <= within
    {
        var ev := events[i];
        if ev.2 == "A" {
            // Find first later B in same session within time limit
            var j := i + 1;
            var found := false;
            while j < |events| && !found
                invariant i < j <= |events|
                invariant forall k :: 0 <= k < |result| ==> 
                    result[k].0 < |events| && result[k].1 < |events|
                invariant forall k :: 0 <= k < |result| ==>
                    events[result[k].0].2 == "A" && events[result[k].1].2 == "B"
                invariant forall k :: 0 <= k < |result| ==>
                    events[result[k].0].1 == events[result[k].1].1
                invariant forall k :: 0 <= k < |result| ==>
                    events[result[k].1].0 - events[result[k].0].0 >= 0 &&
                    events[result[k].1].0 - events[result[k].0].0 <= within
            {
                var evj := events[j];
                if evj.2 == "B" && evj.1 == ev.1 && !(j in usedB) {
                    var delta := evj.0 - ev.0;
                    if delta >= 0 && delta <= within {
                        result := result + [(i, j)];
                        usedB := usedB + {j};
                        found := true;
                    } else {
                        j := j + 1;
                    }
                } else {
                    j := j + 1;
                }
            }
        }
        i := i + 1;
    }
}
