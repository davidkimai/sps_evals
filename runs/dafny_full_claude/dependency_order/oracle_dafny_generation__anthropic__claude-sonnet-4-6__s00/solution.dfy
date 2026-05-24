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
  while ki < |keys_seq|
  {
    var k := keys_seq[ki];
    if k in dependencies {
      var deps := dependencies[k];
      var di := 0;
      while di < |deps|
      {
        // k depends on deps[di], so k has in_degree increment
        if k in in_degree {
          in_degree := in_degree[k := in_degree[k] + 1];
        } else {
          in_degree := in_degree[k := 1];
        }
        di := di + 1;
      }
    }
    ki := ki + 1;
  }
  
  // Kahn's algorithm
  result := [];
  var remaining_nodes := all_nodes;
  var remaining_in_degree := in_degree;
  
  var total_processed := 0;
  var total_count := |all_nodes|;
  
  while true
    decreases |remaining_nodes|
  {
    // Find all nodes with in_degree 0
    var zero_nodes: set<string> := {};
    var rn_seq := SetToSeq(remaining_nodes);
    var ri := 0;
    while ri < |rn_seq|
    {
      var node := rn_seq[ri];
      if node in remaining_in_degree && remaining_in_degree[node] == 0 {
        zero_nodes := zero_nodes + {node};
      }
      ri := ri + 1;
    }
    
    if |zero_nodes| == 0 {
      if |remaining_nodes| > 0 {
        // Cycle detected
        assume false; // Signal error - in compiled code this raises ValueError
      }
      break;
    }
    
    // Sort zero_nodes alphabetically
    var batch := SortedSeq(zero_nodes);
    result := result + [batch];
    
    // Remove zero_nodes from remaining and update in_degrees
    remaining_nodes := remaining_nodes - zero_nodes;
    
    // For each removed node, decrement in_degree of nodes that depend on it
    var bi := 0;
    while bi < |batch|
    {
      var removed := batch[bi];
      // Find all nodes that have removed as a dependency
      var all_remaining_seq := SetToSeq(remaining_nodes);
      var ai := 0;
      while ai < |all_remaining_seq|
      {
        var candidate := all_remaining_seq[ai];
        if candidate in dependencies {
          var cdeps := dependencies[candidate];
          if removed in SeqToSet(cdeps) {
            if candidate in remaining_in_degree {
              remaining_in_degree := remaining_in_degree[candidate := remaining_in_degree[candidate] - 1];
            }
          }
        }
        ai := ai + 1;
      }
      bi := bi + 1;
    }
  }
}

function SeqToSet(s: seq<string>): set<string>
{
  if |s| == 0 then {}
  else {s[0]} + SeqToSet(s[1..])
}

method SetToSeq(s: set<string>) returns (result: seq<string>)
  ensures |result| == |s|
  ensures forall x :: x in s <==> x in result
{
  result := [];
  var remaining := s;
  while remaining != {}
    decreases remaining
  {
    var x :| x in remaining;
    result := result + [x];
    remaining := remaining - {x};
  }
}

method SortedSeq(s: set<string>) returns (result: seq<string>)
  ensures |result| == |s|
  ensures forall x :: x in s <==> x in result
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i] <= result[j]
{
  var unsorted := SetToSeq(s);
  result := InsertionSort(unsorted);
}

method InsertionSort(s: seq<string>) returns (result: seq<string>)
  ensures |result| == |s|
  ensures forall x :: x in s <==> x in result
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i] <= result[j]
{
  result := s;
  var i := 1;
  while i < |result|
    invariant 1 <= i <= |result|
    invariant |result| == |s|
    invariant forall j, k :: 0 <= j < k < i ==> result[j] <= result[k]
  {
    var key := result[i];
    var j := i - 1;
    while j >= 0 && result[j] > key
      invariant -1 <= j < i
      invariant |result| == |s|
      invariant forall a, b :: 0 <= a < b <= i && !(a == j+1 && b == i) ==> 
        (if b < i then result[a] <= result[b] else true)
    {
      result := result[j+1 := result[j]];
      j := j - 1;
    }
    result := result[j+1 := key];
    i := i + 1;
  }
}
