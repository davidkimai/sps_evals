method collect_cursor_items(pages: seq<seq<int>>) returns (result: seq<int>)
  requires |pages| >= 0
  ensures |result| >= 0
{
  result := [];
  var i := 0;
  while i < |pages|
    invariant 0 <= i <= |pages|
    invariant |result| >= 0
  {
    result := result + pages[i];
    i := i + 1;
  }
}
