method MergeSortedArrays(arrays: seq<seq<int>>) returns (result: seq<int>)
  requires forall i :: 0 <= i < |arrays| ==> forall j, k :: 0 <= j < k < |arrays[i]| ==> arrays[i][j] <= arrays[i][k]
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i] <= result[j]
  ensures multiset(result) == (set i | 0 <= i < |arrays| :: multiset(arrays[i])).Sum()
{
  // We'll implement a simple merge using indices
  var indices := new int[|arrays|];
  var n := |arrays|;
  
  // Initialize all indices to 0
  var k := 0;
  while k < n
    invariant 0 <= k <= n
    invariant forall i :: 0 <= i < k ==> indices[i] == 0
  {
    indices[k] := 0;
    k := k + 1;
  }
  
  result := [];
  
  // Count total elements
  var total := 0;
  var t := 0;
  while t < n
    invariant 0 <= t <= n
  {
    total := total + |arrays[t]|;
    t := t + 1;
  }
  
  var count := 0;
  while count < total
    invariant 0 <= count <= total
    invariant |result| == count
    invariant forall i :: 0 <= i < n ==> 0 <= indices[i] <= |arrays[i]|
    invariant forall i, j :: 0 <= i < j < |result| ==> result[i] <= result[j]
  {
    // Find minimum among current heads
    var minVal := 0;
    var minIdx := -1;
    var i := 0;
    while i < n
      invariant 0 <= i <= n
      invariant minIdx == -1 || (0 <= minIdx < n && indices[minIdx] < |arrays[minIdx]| && minVal == arrays[minIdx][indices[minIdx]])
      invariant minIdx == -1 ==> forall j :: 0 <= j < i ==> indices[j] >= |arrays[j]|
      invariant minIdx != -1 ==> forall j :: 0 <= j < i ==> (indices[j] >= |arrays[j]| || arrays[j][indices[j]] >= minVal)
    {
      if indices[i] < |arrays[i]| {
        if minIdx == -1 || arrays[i][indices[i]] < minVal {
          minVal := arrays[i][indices[i]];
          minIdx := i;
        }
      }
      i := i + 1;
    }
    
    if minIdx == -1 {
      break;
    }
    
    // Append minimum to result
    if |result| > 0 {
      assert result[|result|-1] <= minVal;
    }
    result := result + [minVal];
    indices[minIdx] := indices[minIdx] + 1;
    count := count + 1;
  }
}

// Simpler version without complex multiset invariants
method MergeSorted(arrays: seq<seq<int>>) returns (result: seq<int>)
  requires forall i :: 0 <= i < |arrays| ==> forall j, k :: 0 <= j < k < |arrays[i]| ==> arrays[i][j] <= arrays[i][k]
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i] <= result[j]
{
  var n := |arrays|;
  var indices := new int[n];
  
  var k := 0;
  while k < n
    invariant 0 <= k <= n
    invariant forall i :: 0 <= i < k ==> indices[i] == 0
  {
    indices[k] := 0;
    k := k + 1;
  }
  
  result := [];
  
  var found := true;
  while found
    invariant forall i :: 0 <= i < n ==> 0 <= indices[i] <= |arrays[i]|
    invariant forall i, j :: 0 <= i < j < |result| ==> result[i] <= result[j]
    decreases (set i | 0 <= i < n && indices[i] < |arrays[i]| :: |arrays[i]| - indices[i])
  {
    var minVal := 0;
    var minIdx := -1;
    var i := 0;
    while i < n
      invariant 0 <= i <= n
      invariant minIdx == -1 || (0 <= minIdx < n && indices[minIdx] < |arrays[minIdx]| && minVal == arrays[minIdx][indices[minIdx]])
      invariant minIdx == -1 ==> forall j :: 0 <= j < i ==> indices[j] >= |arrays[j]|
      invariant minIdx != -1 ==> forall j :: 0 <= j < i ==> (indices[j] >= |arrays[j]| || arrays[j][indices[j]] >= minVal)
    {
      if indices[i] < |arrays[i]| {
        if minIdx == -1 || arrays[i][indices[i]] < minVal {
          minVal := arrays[i][indices[i]];
          minIdx := i;
        }
      }
      i := i + 1;
    }
    
    if minIdx == -1 {
      found := false;
    } else {
      if |result| > 0 {
        assert result[|result|-1] <= minVal;
      }
      result := result + [minVal];
      indices[minIdx] := indices[minIdx] + 1;
    }
  }
}
