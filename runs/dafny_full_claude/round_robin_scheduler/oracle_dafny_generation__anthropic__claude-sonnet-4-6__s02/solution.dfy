method assign_round_robin(workers: seq<(string, bool)>, jobs: seq<string>) returns (result: seq<(string, string)>)
  requires |workers| > 0
  requires exists i :: 0 <= i < |workers| && workers[i].1
  ensures |result| == |jobs|
{
  var enabled := [];
  for i := 0 to |workers|
  {
    if workers[i].1 {
      enabled := enabled + [workers[i].0];
    }
  }
  
  result := [];
  for j := 0 to |jobs|
    invariant |result| == j
  {
    var workerName := enabled[j % |enabled|];
    result := result + [(jobs[j], workerName)];
  }
}
