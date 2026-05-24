method assign_round_robin(workers: seq<(string, bool)>, jobs: seq<string>) returns (result: seq<(string, string)>)
  requires exists i :: 0 <= i < |workers| && workers[i].1
  ensures |result| == |jobs|
  ensures forall k :: 0 <= k < |result| ==> result[k].0 == jobs[k]
{
  // Collect enabled workers
  var enabled: seq<string> := [];
  var i := 0;
  while i < |workers|
    invariant 0 <= i <= |workers|
    invariant |enabled| <= i
  {
    if workers[i].1 {
      enabled := enabled + [workers[i].0];
    }
    i := i + 1;
  }
  
  // Build result
  result := [];
  var j := 0;
  while j < |jobs|
    invariant 0 <= j <= |jobs|
    invariant |result| == j
    invariant forall k :: 0 <= k < |result| ==> result[k].0 == jobs[k]
  {
    var workerIdx := j % |enabled|;
    result := result + [(jobs[j], enabled[workerIdx])];
    j := j + 1;
  }
}
