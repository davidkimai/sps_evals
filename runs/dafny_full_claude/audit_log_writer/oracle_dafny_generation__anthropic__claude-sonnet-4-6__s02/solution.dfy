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
  ensures forall i :: 0 <= i < count ==> newSink[i] == sink[i]
{
  var seqNum := count + 1;
  record := (seqNum, actor, action);
  
  if count < sink.Length {
    newSink := sink;
  } else {
    var newLen := if sink.Length == 0 then 4 else sink.Length * 2;
    newSink := new (int, string, string)[newLen];
    var i := 0;
    while i < count
      invariant 0 <= i <= count
      invariant forall j :: 0 <= j < i ==> newSink[j] == sink[j]
    {
      newSink[i] := sink[i];
      i := i + 1;
    }
  }
  
  newSink[count] := record;
  newCount := count + 1;
}

method Main()
{
  var sink := new (int, string, string)[4];
  var count := 0;
  
  var newSink, newCount, rec1 := Write(sink, count, "alice", "login");
  sink := newSink;
  count := newCount;
  
  assert rec1 == (1, "alice", "login");
  
  var newSink2, newCount2, rec2 := Write(sink, count, "bob", "logout");
  sink := newSink2;
  count := newCount2;
  
  assert rec2 == (2, "bob", "logout");
  assert count == 2;
}
