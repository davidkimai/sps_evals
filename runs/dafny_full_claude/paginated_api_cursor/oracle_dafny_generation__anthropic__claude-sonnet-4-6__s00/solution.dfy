method collect_cursor_items<T>(
  pages: seq<(seq<T>, bool)>
) returns (result: seq<T>)
  requires |pages| >= 1
  requires pages[|pages|-1].1 == false
  requires forall i :: 0 <= i < |pages|-1 ==> pages[i].1 == true
  ensures result == seq_concat_all(pages)
{
  result := [];
  var i := 0;
  while i < |pages|
    invariant 0 <= i <= |pages|
    invariant result == seq_concat_all(pages[..i])
  {
    result := result + pages[i].0;
    i := i + 1;
  }
}

function seq_concat_all<T>(pages: seq<(seq<T>, bool)>): seq<T>
{
  if |pages| == 0 then []
  else pages[0].0 + seq_concat_all(pages[1..])
}
