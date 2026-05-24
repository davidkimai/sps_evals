method iter_file_chunks(data: seq<byte>, chunk_size: int) returns (chunks: seq<seq<byte>>)
  requires chunk_size > 0
  requires |data| >= 0
  ensures forall i :: 0 <= i < |chunks| ==> |chunks[i]| > 0
  ensures forall i :: 0 <= i < |chunks| ==> |chunks[i]| <= chunk_size
{
  chunks := [];
  var pos := 0;
  while pos < |data|
    invariant 0 <= pos <= |data|
    invariant forall i :: 0 <= i < |chunks| ==> |chunks[i]| > 0
    invariant forall i :: 0 <= i < |chunks| ==> |chunks[i]| <= chunk_size
  {
    var end := pos + chunk_size;
    if end > |data| {
      end := |data|;
    }
    var chunk := data[pos..end];
    chunks := chunks + [chunk];
    pos := end;
  }
}
