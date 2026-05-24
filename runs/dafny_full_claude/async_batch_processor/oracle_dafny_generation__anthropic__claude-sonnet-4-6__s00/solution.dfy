method process_in_batches(items: seq<int>, batch_size: int, concurrency: int) returns (result: seq<int>)
  requires batch_size > 0
  requires concurrency > 0
  ensures |result| == |items|
{
  var batches := split_into_batches(items, batch_size);
  result := flatten_batches(batches);
}

method split_into_batches(items: seq<int>, batch_size: int) returns (batches: seq<seq<int>>)
  requires batch_size > 0
  ensures flatten(batches) == items
  ensures forall i :: 0 <= i < |batches| - 1 ==> |batches[i]| == batch_size
  ensures |batches| == 0 || (|batches| > 0 && |batches[|batches|-1]| > 0)
{
  batches := [];
  var remaining := items;
  
  while |remaining| > 0
    invariant flatten(batches) + remaining == items
    invariant forall i :: 0 <= i < |batches| ==> |batches[i]| == batch_size || i == |batches| - 1
    decreases |remaining|
  {
    if |remaining| >= batch_size {
      var batch := remaining[..batch_size];
      batches := batches + [batch];
      remaining := remaining[batch_size..];
    } else {
      batches := batches + [remaining];
      remaining := [];
    }
  }
}

function flatten(batches: seq<seq<int>>): seq<int>
{
  if |batches| == 0 then []
  else batches[0] + flatten(batches[1..])
}

method flatten_batches(batches: seq<seq<int>>) returns (result: seq<int>)
  ensures result == flatten(batches)
{
  result := [];
  var i := 0;
  while i < |batches|
    invariant 0 <= i <= |batches|
    invariant result == flatten(batches[..i])
  {
    flatten_prefix_lemma(batches, i);
    result := result + batches[i];
    i := i + 1;
  }
  assert batches[..|batches|] == batches;
}

lemma flatten_prefix_lemma(batches: seq<seq<int>>, i: int)
  requires 0 <= i < |batches|
  ensures flatten(batches[..i]) + batches[i] == flatten(batches[..i+1])
{
  var prefix := batches[..i];
  var next := batches[i];
  var prefix_plus := batches[..i+1];
  
  assert prefix_plus == prefix + [next];
  flatten_append_lemma(prefix, [next]);
  assert flatten(prefix + [next]) == flatten(prefix) + flatten([next]);
  assert flatten([next]) == next + flatten([]);
  assert flatten([]) == [];
  assert flatten([next]) == next;
}

lemma flatten_append_lemma(a: seq<seq<int>>, b: seq<seq<int>>)
  ensures flatten(a + b) == flatten(a) + flatten(b)
{
  if |a| == 0 {
    assert a + b == b;
  } else {
    var tail := a[1..];
    assert a + b == [a[0]] + (tail + b);
    flatten_append_lemma(tail, b);
  }
}
