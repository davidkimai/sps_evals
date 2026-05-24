method process_in_batches(items: seq<int>, batch_size: int, concurrency: int) returns (result: seq<int>)
  requires batch_size > 0
  requires concurrency > 0
  ensures |result| == |items|
{
  result := [];
  var i := 0;
  while i < |items|
    invariant 0 <= i <= |items|
    invariant |result| == i
    decreases |items| - i
  {
    var end := i + batch_size;
    if end > |items| {
      end := |items|;
    }
    var batch := items[i..end];
    result := result + batch;
    i := end;
  }
}
