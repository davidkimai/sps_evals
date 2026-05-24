method diff_versions(previous: map<string, string>, current: map<string, string>) returns (result: seq<map<string, string>>)
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i]["field"] < result[j]["field"]
{
  // Collect all keys that changed (added, removed, or modified)
  var changedFields: seq<string> := [];
  
  // Find keys in previous that are different or removed in current
  var prevKeys := previous.Keys;
  var prevSeq := setToSeq(prevKeys);
  
  var i := 0;
  while i < |prevSeq|
    invariant 0 <= i <= |prevSeq|
  {
    var k := prevSeq[i];
    if k in current {
      if previous[k] != current[k] {
        changedFields := changedFields + [k];
      }
    } else {
      changedFields := changedFields + [k];
    }
    i := i + 1;
  }
  
  // Find keys in current that are not in previous (added)
  var currKeys := current.Keys;
  var currSeq := setToSeq(currKeys);
  
  var j := 0;
  while j < |currSeq|
    invariant 0 <= j <= |currSeq|
  {
    var k := currSeq[j];
    if k !in previous {
      changedFields := changedFields + [k];
    }
    j := j + 1;
  }
  
  // Sort the changed fields
  changedFields := sortStrings(changedFields);
  
  // Build result
  result := [];
  var k := 0;
  while k < |changedFields|
    invariant 0 <= k <= |changedFields|
    invariant |result| == k
  {
    var field := changedFields[k];
    var before := if field in previous then previous[field] else "";
    var after := if field in current then current[field] else "";
    var record := map["field" := field, "before" := before, "after" := after];
    result := result + [record];
    k := k + 1;
  }
}

method setToSeq(s: set<string>) returns (result: seq<string>)
  ensures forall x :: x in s <==> x in result
  ensures |result| == |s|
{
  result := [];
  var remaining := s;
  while remaining != {}
    invariant forall x :: x in remaining ==> x !in result
    invariant forall x :: x in result ==> x in s
    invariant forall x :: x in s <==> (x in remaining || x in result)
    invariant |result| + |remaining| == |s|
    decreases remaining
  {
    var x :| x in remaining;
    result := result + [x];
    remaining := remaining - {x};
  }
}

method sortStrings(s: seq<string>) returns (result: seq<string>)
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i] <= result[j]
  ensures |result| == |s|
  ensures multiset(result) == multiset(s)
{
  result := s;
  var n := |result|;
  var i := 0;
  while i < n
    invariant 0 <= i <= n
    invariant |result| == n
    invariant multiset(result) == multiset(s)
    invariant forall a, b :: 0 <= a < b < i ==> result[a] <= result[b]
    invariant forall a, b :: 0 <= a < i <= b < n ==> result[a] <= result[b]
  {
    var j := i + 1;
    while j < n
      invariant i < j <= n
      invariant |result| == n
      invariant multiset(result) == multiset(s)
      invariant forall a, b :: 0 <= a < b < i ==> result[a] <= result[b]
      invariant forall a, b :: 0 <= a < i <= b < n ==> result[a] <= result[b]
      invariant forall b :: i <= b < j ==> result[i] <= result[b]
    {
      if result[j] < result[i] {
        result := result[i := result[j]][j := result[i]];
      }
      j := j + 1;
    }
    i := i + 1;
  }
}
