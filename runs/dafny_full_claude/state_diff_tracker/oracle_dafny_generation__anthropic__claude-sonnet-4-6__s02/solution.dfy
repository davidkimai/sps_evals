method diff_versions(previous: map<string, string>, current: map<string, string>) returns (result: seq<map<string, string>>)
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i]["field"] < result[j]["field"]
{
  // Collect all keys from both maps
  var allKeys: set<string> := previous.Keys + current.Keys;
  
  // Find changed/added/removed fields
  var changes: seq<map<string, string>> := [];
  
  // Convert set to sorted sequence
  var keySeq := SetToSortedSeq(allKeys);
  
  var i := 0;
  while i < |keySeq|
    invariant 0 <= i <= |keySeq|
    invariant forall a, b :: 0 <= a < b < |changes| ==> changes[a]["field"] < changes[b]["field"]
  {
    var k := keySeq[i];
    if k in previous && k in current {
      if previous[k] != current[k] {
        var record := map["field" := k, "before" := previous[k], "after" := current[k]];
        changes := changes + [record];
      }
    } else if k in previous && k !in current {
      var record := map["field" := k, "before" := previous[k], "after" := ""];
      changes := changes + [record];
    } else if k !in previous && k in current {
      var record := map["field" := k, "before" := "", "after" := current[k]];
      changes := changes + [record];
    }
    i := i + 1;
  }
  
  result := changes;
}

method SetToSortedSeq(s: set<string>) returns (result: seq<string>)
  ensures forall x :: x in s <==> x in result
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i] < result[j]
  ensures |result| == |s|
{
  if s == {} {
    result := [];
    return;
  }
  
  var remaining := s;
  var sorted: seq<string> := [];
  
  while remaining != {}
    invariant forall x :: x in remaining ==> x in s
    invariant forall x :: x in sorted ==> x in s
    invariant forall x :: x in s <==> (x in remaining || x in sorted)
    invariant forall i, j :: 0 <= i < j < |sorted| ==> sorted[i] < sorted[j]
    invariant forall x, y :: x in remaining && y in sorted ==> y < x
    decreases |remaining|
  {
    // Find minimum element
    var minElem: string :| minElem in remaining;
    var iter := remaining;
    
    while iter != {}
      invariant minElem in remaining
      invariant forall x :: x in (remaining - iter) ==> minElem <= x
      decreases |iter|
    {
      var elem :| elem in iter;
      if elem < minElem {
        minElem := elem;
      }
      iter := iter - {elem};
    }
    
    sorted := sorted + [minElem];
    remaining := remaining - {minElem};
  }
  
  result := sorted;
}
