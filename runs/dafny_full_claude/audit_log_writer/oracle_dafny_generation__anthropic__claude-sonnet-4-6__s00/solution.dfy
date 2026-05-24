method AuditLogWriter(sink: array<(int, string, string)>, initialSize: int) returns (log: array<(int, string, string)>)
  requires initialSize >= 0
  ensures log.Length == initialSize
{
  log := new (int, string, string)[initialSize];
}

method Write(sink: array<(int, string, string)>, count: int, actor: string, action: string)
  returns (newSink: array<(int, string, string)>, newCount: int, record: (int, string, string))
  requires 0 <= count <= sink.Length
  ensures newCount == count + 1
  ensures record == (count + 1, actor, action)
  ensures newSink.Length >= newCount
  ensures newSink[count] == record
  ensures newSink != sink
  modifies sink
{
  var seq_num := count + 1;
  record := (seq_num, actor, action);
  
  if count < sink.Length {
    newSink := new (int, string, string)[sink.Length];
    var i := 0;
    while i < count
      invariant 0 <= i <= count
      invariant forall j :: 0 <= j < i ==> newSink[j] == sink[j]
    {
      newSink[i] := sink[i];
      i := i + 1;
    }
    newSink[count] := record;
    newCount := count + 1;
  } else {
    var newSize := if sink.Length == 0 then 4 else sink.Length * 2;
    newSink := new (int, string, string)[newSize];
    var i := 0;
    while i < count
      invariant 0 <= i <= count
      invariant forall j :: 0 <= j < i ==> newSink[j] == sink[j]
    {
      newSink[i] := sink[i];
      i := i + 1;
    }
    newSink[count] := record;
    newCount := count + 1;
  }
}
