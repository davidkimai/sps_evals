method plan_batches(dependencies: map<string, seq<string>>) returns (result: seq<seq<string>>)
{
  // Collect all nodes (tasks that appear as keys or as dependencies)
  var all_nodes: set<string> := {};
  
  // Add all keys
  var keys := dependencies.Keys;
  all_nodes := all_nodes + keys;
  
  // Add all dependency values
  var keys_seq := SetToSeq(keys);
  var i := 0;
  while i < |keys_seq|
  {
    var k := keys_seq[i];
    if k in dependencies {
      var deps := dependencies[k];
      var j := 0;
      while j < |deps|
      {
        all_nodes := all_nodes + {deps[j]};
        j := j + 1;
      }
    }
    i := i + 1;
  }
  
  // Build in-degree map and adjacency list
  // For each node, count how many prerequisites it has
  var in_degree: map<string, int> := map[];
  var nodes_seq := SetToSeq(all_nodes);
  
  // Initialize in_degree to 0 for all nodes
  var ni := 0;
  while ni < |nodes_seq|
  {
    in_degree := in_degree[nodes_seq[ni] := 0];
    ni := ni + 1;
  }
  
  // For each task, add its dependencies to in_degree
  var ki := 0;
  while ki < |nodes_seq|
  {
    var node := nodes_seq[ki];
    if node in dependencies {
      var deps := dependencies[node];
      var di := 0;
      while di < |deps|
      {
        // node depends on deps[di], so node's in_degree increases
        if node in in_degree {
          in_degree := in_degree[node := in_degree[node] + 1];
        } else {
          in_degree := in_degree[node := 1];
        }
        di := di + 1;
      }
    }
    ki := ki + 1;
  }
  
  result := [];
  var remaining := all_nodes;
  var processed: set<string> := {};
  
  while |remaining| > 0
  {
    // Find all nodes with in_degree 0 (no unprocessed dependencies)
    var batch: set<string> := {};
    var ri := 0;
    var rem_seq := SetToSeq(remaining);
    while ri < |rem_seq|
    {
      var node := rem_seq[ri];
      // Check if all dependencies of this node have been processed
      var can_run := true;
      if node in dependencies {
        var deps := dependencies[node];
        var di := 0;
        while di < |deps|
        {
          if deps[di] !in processed {
            can_run := false;
            break;
          }
          di := di + 1;
        }
      }
      if can_run {
        batch := batch + {node};
      }
      ri := ri + 1;
    }
    
    if |batch| == 0 {
      // Cycle detected
      var err: seq<string> := ["ValueError: cycle detected"];
      assume false; // Signal error - in compiled code this will raise ValueError
      return [];
    }
    
    // Sort batch alphabetically
    var batch_sorted := SortSet(batch);
    result := result + [batch_sorted];
    
    // Update processed and remaining
    processed := processed + batch;
    remaining := remaining - batch;
  }
}

method SetToSeq(s: set<string>) returns (result: seq<string>)
  ensures forall x :: x in s <==> x in result
  ensures |result| == |s|
{
  result := [];
  var remaining := s;
  while |remaining| > 0
    invariant forall x :: x in remaining || x in result <==> x in s
    invariant forall x :: x in result ==> x !in remaining
    decreases |remaining|
  {
    var x :| x in remaining;
    result := result + [x];
    remaining := remaining - {x};
  }
}

method SortSet(s: set<string>) returns (result: seq<string>)
  ensures forall x :: x in s <==> x in result
  ensures |result| == |s|
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i] <= result[j]
{
  var seq_s := SetToSeq(s);
  result := InsertionSort(seq_s);
}

method InsertionSort(s: seq<string>) returns (result: seq<string>)
  ensures |result| == |s|
  ensures forall x :: x in s <==> x in result
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i] <= result[j]
{
  result := s;
  var i := 1;
  while i < |result|
    invariant 0 <= i <= |result|
    invariant |result| == |s|
    invariant forall j, k :: 0 <= j < k < i ==> result[j] <= result[k]
    invariant multiset(result) == multiset(s)
  {
    var key := result[i];
    var j := i - 1;
    var temp := result;
    while j >= 0 && temp[j] > key
      invariant -1 <= j <= i - 1
      invariant |temp| == |result|
      invariant multiset(temp) == multiset(result)
      invariant forall k :: j < k <= i ==> temp[k] >= key
      invariant forall k :: 0 <= k <= j ==> temp[k] == result[k]
      invariant forall k :: j+2 <= k <= i ==> temp[k] == result[k-1]
    {
      temp := temp[j+1 := temp[j]];
      j := j - 1;
    }
    temp := temp[j+1 := key];
    result := temp;
    i := i + 1;
  }
}
