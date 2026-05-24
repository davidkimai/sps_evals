method correlate_events(events: seq<(int, int, int)>, within: int) returns (result: seq<(int, int, int, int, int, int)>)
  // Each event is (session_id, event_type, timestamp) where event_type 0=A, 1=B
  // Result pairs are (session_idA, typeA=0, timestampA, session_idB, typeB=1, timestampB)
  requires within >= 0
  ensures forall i :: 0 <= i < |result| ==>
    result[i].0 == result[i].3 &&  // same session
    result[i].1 == 0 &&             // first is type A
    result[i].4 == 1 &&             // second is type B
    result[i].5 - result[i].2 >= 0 &&  // B is later
    result[i].5 - result[i].2 <= within  // within time window
{
  result := [];
  var usedB: seq<int> := [];
  
  var i := 0;
  while i < |events|
    invariant 0 <= i <= |events|
    invariant forall k :: 0 <= k < |result| ==>
      result[k].0 == result[k].3 &&
      result[k].1 == 0 &&
      result[k].4 == 1 &&
      result[k].5 - result[k].2 >= 0 &&
      result[k].5 - result[k].2 <= within
  {
    if events[i].1 == 0 {  // event type A
      var sessionA := events[i].0;
      var timeA := events[i].2;
      
      // Find first later B in same session within time window
      var j := 0;
      var found := false;
      while j < |events| && !found
        invariant 0 <= j <= |events|
        invariant !found
      {
        if events[j].1 == 1 &&           // type B
           events[j].0 == sessionA &&     // same session
           events[j].2 >= timeA &&        // B is later or equal
           events[j].2 - timeA <= within && // within window
           events[j].2 > timeA            // strictly later
        {
          // Check if this B index is already used
          var alreadyUsed := false;
          var k := 0;
          while k < |usedB|
            invariant 0 <= k <= |usedB|
          {
            if usedB[k] == j {
              alreadyUsed := true;
            }
            k := k + 1;
          }
          if !alreadyUsed {
            result := result + [(sessionA, 0, timeA, events[j].0, 1, events[j].2)];
            usedB := usedB + [j];
            found := true;
          }
        }
        if !found {
          j := j + 1;
        }
      }
    }
    i := i + 1;
  }
}
