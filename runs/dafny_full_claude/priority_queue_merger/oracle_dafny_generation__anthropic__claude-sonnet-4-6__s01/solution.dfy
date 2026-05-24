method MergeSortedArrays(arrays: seq<seq<int>>) returns (result: seq<int>)
  requires forall i :: 0 <= i < |arrays| ==> forall j, k :: 0 <= j < k < |arrays[i]| ==> arrays[i][j] <= arrays[i][k]
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i] <= result[j]
  ensures multiset(result) == (set i | 0 <= i < |arrays| :: multiset(arrays[i])).Sum()
{
  // We'll implement a simple k-way merge using indices
  var indices := new int[|arrays|];
  var n := |arrays|;
  
  // Initialize all indices to 0
  var i := 0;
  while i < n
    invariant 0 <= i <= n
    invariant forall j :: 0 <= j < i ==> indices[j] == 0
  {
    indices[i] := 0;
    i := i + 1;
  }
  
  result := [];
  
  // Repeatedly find minimum element across all arrays
  var totalElements := 0;
  var k := 0;
  while k < n
    invariant 0 <= k <= n
  {
    totalElements := totalElements + |arrays[k]|;
    k := k + 1;
  }
  
  var count := 0;
  while count < totalElements
    invariant 0 <= count <= totalElements
    invariant |result| == count
    invariant forall p, q :: 0 <= p < q < |result| ==> result[p] <= result[q]
    decreases totalElements - count
  {
    // Find minimum value among current heads
    var minVal := 0;
    var minIdx := -1;
    var j := 0;
    
    while j < n
      invariant 0 <= j <= n
      invariant minIdx == -1 || (0 <= minIdx < n && indices[minIdx] < |arrays[minIdx]| && 
                                  forall m :: 0 <= m < j && m != minIdx ==> 
                                    (indices[m] >= |arrays[m]| || arrays[minIdx][indices[minIdx]] <= arrays[m][indices[m]]))
    {
      if indices[j] < |arrays[j]| {
        if minIdx == -1 || arrays[j][indices[j]] < minVal {
          minVal := arrays[j][indices[j]];
          minIdx := j;
        }
      }
      j := j + 1;
    }
    
    if minIdx >= 0 {
      result := result + [minVal];
      indices[minIdx] := indices[minIdx] + 1;
    }
    
    count := count + 1;
  }
}

method Main() {
  var a1 := [1, 3, 5];
  var a2 := [2, 4, 6];
  var a3 := [0, 7, 8];
  
  var arrays := [a1, a2, a3];
  
  // Simple merge for demonstration
  var result := SimpleMerge(arrays);
  
  var i := 0;
  while i < |result| {
    print result[i];
    print " ";
    i := i + 1;
  }
  print "\n";
}

method SimpleMerge(arrays: seq<seq<int>>) returns (result: seq<int>)
  requires forall i :: 0 <= i < |arrays| ==> forall j, k :: 0 <= j < k < |arrays[i]| ==> arrays[i][j] <= arrays[i][k]
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i] <= result[j]
{
  result := [];
  var n := |arrays|;
  var indices := new int[n];
  
  var init := 0;
  while init < n
    invariant 0 <= init <= n
    invariant forall j :: 0 <= j < init ==> indices[j] == 0
  {
    indices[init] := 0;
    init := init + 1;
  }
  
  var totalElements := 0;
  var k := 0;
  while k < n {
    totalElements := totalElements + |arrays[k]|;
    k := k + 1;
  }
  
  var count := 0;
  while count < totalElements
    invariant 0 <= count
    invariant |result| == count
    invariant forall p, q :: 0 <= p < q < |result| ==> result[p] <= result[q]
    decreases totalElements - count
  {
    var minVal := 0;
    var minIdx := -1;
    var j := 0;
    
    while j < n {
      if indices[j] < |arrays[j]| {
        if minIdx == -1 || arrays[j][indices[j]] < minVal {
          minVal := arrays[j][indices[j]];
          minIdx := j;
        }
      }
      j := j + 1;
    }
    
    if minIdx >= 0 {
      result := result + [minVal];
      indices[minIdx] := indices[minIdx] + 1;
      count := count + 1;
    } else {
      break;
    }
  }
}
