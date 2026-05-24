method assign_round_robin(workers: seq<(string, bool)>, jobs: seq<string>) returns (result: seq<(string, string)>)
  requires exists i :: 0 <= i < |workers| && workers[i].1
  ensures |result| == |jobs|
  ensures forall i :: 0 <= i < |result| ==> result[i].0 == jobs[i]
{
  // Collect enabled workers
  var enabled: seq<string> := [];
  var k := 0;
  while k < |workers|
    invariant 0 <= k <= |workers|
    invariant forall i :: 0 <= i < |enabled| ==> exists j :: 0 <= j < k && workers[j].1 && workers[j].0 == enabled[i]
  {
    if workers[k].1 {
      enabled := enabled + [workers[k].0];
    }
    k := k + 1;
  }
  
  result := [];
  var idx := 0;
  var j := 0;
  while j < |jobs|
    invariant 0 <= j <= |jobs|
    invariant |result| == j
    invariant forall i :: 0 <= i < |result| ==> result[i].0 == jobs[i]
    invariant 0 <= idx
    invariant |enabled| > 0
  {
    var worker_name := enabled[idx % |enabled|];
    result := result + [(jobs[j], worker_name)];
    idx := idx + 1;
    j := j + 1;
  }
}

method Main() {
  // Test basic functionality
  var workers := [("Alice", true), ("Bob", true), ("Charlie", false)];
  var jobs := ["job1", "job2", "job3", "job4"];
  var result := assign_round_robin(workers, jobs);
  print "Results:\n";
  var i := 0;
  while i < |result| {
    print result[i].0, " -> ", result[i].1, "\n";
    i := i + 1;
  }
}
