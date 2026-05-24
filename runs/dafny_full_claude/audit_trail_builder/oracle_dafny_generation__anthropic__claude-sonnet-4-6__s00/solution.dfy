method build_audit_trail(events: seq<map<string, string>>) returns (result: seq<map<string, string>>)
  ensures |result| <= |events|
{
  var trail: seq<map<string, string>> := [];
  var seq_num := 1;
  
  for i := 0 to |events|
    invariant seq_num == |trail| + 1
    invariant |trail| <= i
  {
    var event := events[i];
    if "source_system" in event && "actor_id" in event {
      var record := map[
        "sequence" := intToString(seq_num),
        "source_system" := event["source_system"],
        "actor_id" := event["actor_id"],
        "action" := if "action" in event then event["action"] else ""
      ];
      trail := trail + [record];
      seq_num := seq_num + 1;
    }
  }
  
  result := trail;
}

function intToString(n: int): string
  requires n >= 0
{
  if n == 0 then "0"
  else if n < 10 then digitToChar(n)
  else intToString(n / 10) + digitToChar(n % 10)
}

function digitToChar(d: int): string
  requires 0 <= d < 10
{
  if d == 0 then "0"
  else if d == 1 then "1"
  else if d == 2 then "2"
  else if d == 3 then "3"
  else if d == 4 then "4"
  else if d == 5 then "5"
  else if d == 6 then "6"
  else if d == 7 then "7"
  else if d == 8 then "8"
  else "9"
}

method Main() {
  var events := [
    map["source_system" := "web", "actor_id" := "user1", "action" := "login"],
    map["source_system" := "api", "actor_id" := "user2", "action" := "read"],
    map["actor_id" := "user3", "action" := "write"],
    map["source_system" := "db", "action" := "delete"],
    map["source_system" := "web", "actor_id" := "user4", "action" := "logout"]
  ];
  
  var trail := build_audit_trail(events);
  
  print "Audit trail has ", |trail|, " records\n";
  for i := 0 to |trail| {
    var record := trail[i];
    print "Record ", i, ": seq=", record["sequence"], 
          " source=", record["source_system"],
          " actor=", record["actor_id"],
          " action=", record["action"], "\n";
  }
}
