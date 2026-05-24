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
  ensures record.0 == count + 1
  ensures record.1 == actor
  ensures record.2 == action
  ensures newSink.Length >= newCount
{
  var seq_num := count + 1;
  record := (seq_num, actor, action);
  
  if count < sink.Length {
    newSink := sink;
    newSink[count] := (seq_num, actor, action);
  } else {
    var newLen := if sink.Length == 0 then 4 else sink.Length * 2;
    newSink := new (int, string, string)[newLen];
    var i := 0;
    while i < count
      invariant 0 <= i <= count
    {
      newSink[i] := sink[i];
      i := i + 1;
    }
    newSink[count] := (seq_num, actor, action);
  }
  
  newCount := count + 1;
}
