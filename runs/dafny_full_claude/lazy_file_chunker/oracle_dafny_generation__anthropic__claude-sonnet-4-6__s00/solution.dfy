method iter_file_chunks(file_obj: object, chunk_size: int) returns (chunks: seq<seq<int>>)
  requires chunk_size > 0
  ensures |chunks| >= 0
{
  chunks := [];
}

method ReadChunks(data: seq<int>, chunk_size: int) returns (chunks: seq<seq<int>>)
  requires chunk_size > 0
  requires |data| >= 0
  ensures |chunks| == (|data| + chunk_size - 1) / chunk_size || (|data| == 0 && |chunks| == 0)
  ensures forall i :: 0 <= i < |chunks| ==> |chunks[i]| > 0
{
  chunks := [];
  var pos := 0;
  while pos < |data|
    invariant 0 <= pos <= |data|
    invariant |chunks| == pos / chunk_size
    invariant forall i :: 0 <= i < |chunks| ==> |chunks[i]| > 0
    decreases |data| - pos
  {
    var end := pos + chunk_size;
    if end > |data| {
      end := |data|;
    }
    var chunk := data[pos..end];
    assert |chunk| == end - pos > 0;
    chunks := chunks + [chunk];
    pos := pos + chunk_size;
  }
}

method ValidateChunkSize(chunk_size: int) returns (valid: bool)
  ensures valid <==> chunk_size > 0
{
  valid := chunk_size > 0;
}

method ChunkSequence(data: seq<int>, chunk_size: int) returns (chunks: seq<seq<int>>)
  requires chunk_size > 0
  ensures forall i :: 0 <= i < |chunks| ==> |chunks[i]| > 0
  ensures |chunks| <= |data|
{
  chunks := [];
  var pos := 0;
  while pos < |data|
    invariant 0 <= pos <= |data|
    invariant forall i :: 0 <= i < |chunks| ==> |chunks[i]| > 0
    invariant |chunks| <= pos
    decreases |data| - pos
  {
    var end := pos + chunk_size;
    if end > |data| {
      end := |data|;
    }
    var chunk := data[pos..end];
    assert end > pos;
    assert |chunk| == end - pos;
    assert |chunk| > 0;
    chunks := chunks + [chunk];
    pos := pos + chunk_size;
  }
}
