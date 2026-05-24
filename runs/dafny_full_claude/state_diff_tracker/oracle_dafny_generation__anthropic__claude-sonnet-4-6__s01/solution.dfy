method diff_versions(previous: map<string, string>, current: map<string, string>) returns (result: seq<map<string, string>>)
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i]["field"] <= result[j]["field"]
{
  // Collect all keys from both maps
  var allKeys: set<string> := previous.Keys + current.Keys;
  
  // Find changed/added/removed fields
  var changes: seq<map<string, string>> := [];
  
  // Convert set to sequence for iteration
  var keySeq: seq<string> := [];
  var remaining := allKeys;
  while remaining != {}
    decreases |remaining|
  {
    var k :| k in remaining;
    remaining := remaining - {k};
    keySeq := keySeq + [k];
  }
  
  // For each key, check if value changed
  var i := 0;
  while i < |keySeq|
    invariant 0 <= i <= |keySeq|
  {
    var key := keySeq[i];
    var inPrev := key in previous;
    var inCurr := key in current;
    
    if inPrev && inCurr {
      if previous[key] != current[key] {
        var record := map["field" := key, "before" := previous[key], "after" := current[key]];
        changes := changes + [record];
      }
    } else if inPrev && !inCurr {
      var record := map["field" := key, "before" := previous[key], "after" := ""];
      changes := changes + [record];
    } else if !inPrev && inCurr {
      var record := map["field" := key, "before" := "", "after" := current[key]];
      changes := changes + [record];
    }
    
    i := i + 1;
  }
  
  // Sort changes by field name using insertion sort
  result := SortByField(changes);
}

method SortByField(s: seq<map<string, string>>) returns (sorted: seq<map<string, string>>)
  ensures |sorted| == |s|
  ensures forall i, j :: 0 <= i < j < |sorted| ==> sorted[i]["field"] <= sorted[j]["field"]
{
  sorted := s;
  var n := |sorted|;
  var i := 1;
  while i < n
    invariant 0 <= i <= n
    invariant |sorted| == n
    invariant forall a, b :: 0 <= a < b < i ==> sorted[a]["field"] <= sorted[b]["field"]
  {
    var key := sorted[i];
    var j := i - 1;
    while j >= 0 && sorted[j]["field"] > key["field"]
      invariant -1 <= j < i
      invariant |sorted| == n
      invariant forall a, b :: 0 <= a < b <= i && b != j + 1 ==> sorted[a]["field"] <= sorted[b]["field"]
    {
      sorted := sorted[j + 1 := sorted[j]];
      j := j - 1;
    }
    sorted := sorted[j + 1 := key];
    i := i + 1;
  }
}
