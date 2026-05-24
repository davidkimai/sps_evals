method iter_file_chunks(file_obj: object, chunk_size: int) returns (chunks: seq<seq<int>>)
  requires chunk_size > 0
  ensures forall i :: 0 <= i < |chunks| ==> |chunks[i]| > 0
{
  chunks := [];
}

method ValidateChunkSize(chunk_size: int)
  requires chunk_size > 0
{
}

method ReadChunk(data: seq<int>, offset: int, chunk_size: int) returns (chunk: seq<int>)
  requires 0 <= offset <= |data|
  requires chunk_size > 0
  ensures |chunk| == if offset + chunk_size <= |data| then chunk_size else |data| - offset
  ensures |chunk| >= 0
{
  if offset + chunk_size <= |data| {
    chunk := data[offset..offset + chunk_size];
  } else {
    chunk := data[offset..];
  }
}

method SplitIntoChunks(data: seq<int>, chunk_size: int) returns (chunks: seq<seq<int>>)
  requires chunk_size > 0
  ensures forall i :: 0 <= i < |chunks| ==> |chunks[i]| > 0
  ensures forall i :: 0 <= i < |chunks| ==> |chunks[i]| <= chunk_size
{
  chunks := [];
  var offset := 0;
  while offset < |data|
    invariant 0 <= offset <= |data|
    invariant forall i :: 0 <= i < |chunks| ==> |chunks[i]| > 0
    invariant forall i :: 0 <= i < |chunks| ==> |chunks[i]| <= chunk_size
    decreases |data| - offset
  {
    var end := offset + chunk_size;
    if end > |data| {
      end := |data|;
    }
    var chunk := data[offset..end];
    assert |chunk| == end - offset;
    assert end > offset;
    assert |chunk| > 0;
    chunks := chunks + [chunk];
    offset := end;
  }
}
