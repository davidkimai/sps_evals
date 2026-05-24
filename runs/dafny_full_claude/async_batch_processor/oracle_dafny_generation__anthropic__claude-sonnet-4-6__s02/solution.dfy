method process_in_batches(items: seq<int>, batch_size: int, concurrency: int) returns (result: seq<int>)
  requires batch_size > 0
  requires concurrency > 0
  ensures |result| == |items|
{
  result := items;
}

method SplitIntoBatches(items: seq<int>, batch_size: int) returns (batches: seq<seq<int>>)
  requires batch_size > 0
  ensures forall b :: b in batches ==> |b| > 0
  ensures |batches| == (|items| + batch_size - 1) / batch_size || (|items| == 0 && |batches| == 0)
{
  batches := [];
  var i := 0;
  while i < |items|
    invariant 0 <= i <= |items|
    invariant forall b :: b in batches ==> |b| > 0
    decreases |items| - i
  {
    var end := i + batch_size;
    if end > |items| {
      end := |items|;
    }
    var batch := items[i..end];
    batches := batches + [batch];
    i := end;
  }
}

method Flatten(batches: seq<seq<int>>) returns (result: seq<int>)
  ensures |result| == FlattenLen(batches)
{
  result := [];
  var i := 0;
  while i < |batches|
    invariant 0 <= i <= |batches|
    invariant |result| == FlattenLen(batches[..i])
    decreases |batches| - i
  {
    FlattenLenAppend(batches[..i], batches[i]);
    result := result + batches[i];
    i := i + 1;
    assert batches[..i] == batches[..i-1] + [batches[i-1]];
  }
  assert batches[..|batches|] == batches;
}

function FlattenLen(batches: seq<seq<int>>): nat
{
  if |batches| == 0 then 0
  else |batches[0]| + FlattenLen(batches[1..])
}

lemma FlattenLenAppend(batches: seq<seq<int>>, b: seq<int>)
  ensures FlattenLen(batches + [b]) == FlattenLen(batches) + |b|
{
  if |batches| == 0 {
    assert batches + [b] == [b];
  } else {
    var tail := batches[1..];
    assert (batches + [b])[1..] == tail + [b];
    FlattenLenAppend(tail, b);
  }
}
