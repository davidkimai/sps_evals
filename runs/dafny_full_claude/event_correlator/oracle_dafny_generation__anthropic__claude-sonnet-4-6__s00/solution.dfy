method correlate_events(events: seq<(int, int, int)>, within: int) returns (result: seq<(int, int, int, int, int, int)>)
  // Each event is (session_id, event_type, timestamp) where event_type 0=A, 1=B
  // Returns pairs (session_id, typeA=0, tsA, session_id, typeB=1, tsB)
  requires within >= 0
  ensures forall i :: 0 <= i < |result| ==>
    result[i].1 == 0 && result[i].4 == 1 &&
    result[i].0 == result[i].3 &&
    result[i].5 >= result[i].2 &&
    result[i].5 - result[i].2 <= within
{
  result := [];
  var i := 0;
  while i < |events|
    invariant 0 <= i <= |events|
    invariant forall k :: 0 <= k < |result| ==>
      result[k].1 == 0 && result[k].4 == 1 &&
      result[k].0 == result[k].3 &&
      result[k].5 >= result[k].2 &&
      result[k].5 - result[k].2 <= within
  {
    var ev := events[i];
    if ev.1 == 0 {
      // This is an A event, find first later B in same session within time limit
      var j := i + 1;
      var found := false;
      while j < |events| && !found
        invariant i + 1 <= j <= |events|
        invariant !found
        invariant forall k :: 0 <= k < |result| ==>
          result[k].1 == 0 && result[k].4 == 1 &&
          result[k].0 == result[k].3 &&
          result[k].5 >= result[k].2 &&
          result[k].5 - result[k].2 <= within
      {
        var ev2 := events[j];
        if ev2.1 == 1 && ev2.0 == ev.0 && ev2.2 >= ev.2 && ev2.2 - ev.2 <= within {
          result := result + [(ev.0, 0, ev.2, ev2.0, 1, ev2.2)];
          found := true;
        }
        j := j + 1;
      }
    }
    i := i + 1;
  }
}
