method MergeSortedArrays(arrays: seq<seq<int>>) returns (result: seq<int>)
  requires forall i :: 0 <= i < |arrays| ==> forall j, k :: 0 <= j < k < |arrays[i]| ==> arrays[i][j] <= arrays[i][k]
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i] <= result[j]
{
  // Use indices to track current position in each array
  var indices := new int[|arrays|];
  var n := |arrays|;
  
  // Initialize all indices to 0
  var idx := 0;
  while idx < n
    invariant 0 <= idx <= n
    invariant forall k :: 0 <= k < idx ==> indices[k] == 0
  {
    indices[idx] := 0;
    idx := idx + 1;
  }
  
  result := [];
  
  // Count total elements
  var total := 0;
  var ci := 0;
  while ci < n
    invariant 0 <= ci <= n
    invariant total >= 0
  {
    total := total + |arrays[ci]|;
    ci := ci + 1;
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
    var k := 0;
    
    while k < n
      invariant 0 <= k <= n
      invariant forall i :: 0 <= i < n ==> 0 <= indices[i] <= |arrays[i]|
      invariant minIdx == -1 || (0 <= minIdx < n && indices[minIdx] < |arrays[minIdx]| && minVal == arrays[minIdx][indices[minIdx]])
      invariant minIdx == -1 ==> forall i :: 0 <= i < k ==> indices[i] >= |arrays[i]|
      invariant minIdx >= 0 ==> forall i :: 0 <= i < k && indices[i] < |arrays[i]| ==> minVal <= arrays[i][indices[i]]
    {
      if indices[k] < |arrays[k]| {
        if minIdx == -1 || arrays[k][indices[k]] < minVal {
          minVal := arrays[k][indices[k]];
          minIdx := k;
        }
      }
      k := k + 1;
    }
    
    if minIdx == -1 {
      break;
    }
    
    // Append minVal to result
    // We need to show result[|result|-1] <= minVal before appending
    // This requires knowing minVal >= last element of result
    result := result + [minVal];
    indices[minIdx] := indices[minIdx] + 1;
    count := count + 1;
  }
}
