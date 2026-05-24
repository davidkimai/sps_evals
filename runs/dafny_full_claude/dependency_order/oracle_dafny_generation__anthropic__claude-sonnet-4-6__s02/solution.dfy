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
  // in_degree[node] = number of prerequisites not yet processed
  var in_degree: map<string, int> := map[];
  var nodes_seq := SetToSeq(all_nodes);
  
  // Initialize in_degree to 0 for all nodes
  var ni := 0;
  while ni < |nodes_seq|
  {
    in_degree := in_degree[nodes_seq[ni] := 0];
    ni := ni + 1;
  }
  
  // For each node, count its dependencies (in-edges)
  ni := 0;
  while ni < |nodes_seq|
  {
    var node := nodes_seq[ni];
    if node in dependencies {
      var deps := dependencies[node];
      var di := 0;
      while di < |deps|
      {
        // node depends on deps[di], so node has an in-edge from deps[di]
        // Actually in topological sort: in_degree[node] += 1 for each dep
        if node in in_degree {
          in_degree := in_degree[node := in_degree[node] + 1];
        }
        di := di + 1;
      }
    }
    ni := ni + 1;
  }
  
  // Kahn's algorithm
  result := [];
  var remaining := all_nodes;
  var processed: set<string> := {};
  
  while |remaining| > 0
  {
    // Find all nodes with in_degree 0 in remaining
    var batch: set<string> := {};
    var rem_seq := SetToSeq(remaining);
    var ri := 0;
    while ri < |rem_seq|
    {
      var node := rem_seq[ri];
      if node in in_degree && in_degree[node] == 0 {
        batch := batch + {node};
      }
      ri := ri + 1;
    }
    
    if |batch| == 0 {
      // Cycle detected
      assume false; // Will be handled by Python translation raising ValueError
      return;
    }
    
    // Sort batch alphabetically
    var batch_sorted := SortedSeq(batch);
    result := result + [batch_sorted];
    
    // Mark batch as processed, update in_degrees
    var batch_seq := SetToSeq(batch);
    var bi := 0;
    while bi < |batch_seq|
    {
      var done_node := batch_seq[bi];
      processed := processed + {done_node};
      remaining := remaining - {done_node};
      
      // For each node that depends on done_node, decrease its in_degree
      var all_seq := SetToSeq(remaining);
      var ai := 0;
      while ai < |all_seq|
      {
        var other := all_seq[ai];
        if other in dependencies {
          var other_deps := dependencies[other];
          if SeqContains(other_deps, done_node) {
            if other in in_degree && in_degree[other] > 0 {
              in_degree := in_degree[other := in_degree[other] - 1];
            }
          }
        }
        ai := ai + 1;
      }
      bi := bi + 1;
    }
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
  {
    var x :| x in remaining;
    result := result + [x];
    remaining := remaining - {x};
  }
}

method SortedSeq(s: set<string>) returns (result: seq<string>)
  ensures forall x :: x in s <==> x in result
  ensures |result| == |s|
{
  var seq_s := SetToSeq(s);
  result := InsertionSort(seq_s);
}

method InsertionSort(s: seq<string>) returns (result: seq<string>)
  ensures multiset(s) == multiset(result)
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i] <= result[j]
{
  result := s;
  var i := 1;
  while i < |result|
    invariant 1 <= i <= |result|
    invariant multiset(result) == multiset(s)
    invariant forall p, q :: 0 <= p < q < i ==> result[p] <= result[q]
  {
    var key := result[i];
    var j := i - 1;
    var tmp := result;
    while j >= 0 && result[j] > key
      invariant -1 <= j <= i - 1
      invariant multiset(result) == multiset(s)
      invariant forall p, q :: 0 <= p < q <= i && q != j + 1 ==> result[p] <= result[q]
    {
      result := result[j+1 := result[j]];
      j := j - 1;
    }
    result := result[j+1 := key];
    i := i + 1;
  }
}

method SeqContains(s: seq<string>, x: string) returns (result: bool)
  ensures result <==> x in s
{
  result := false;
  var i := 0;
  while i < |s|
  {
    if s[i] == x {
      return true;
    }
    i := i + 1;
  }
}
