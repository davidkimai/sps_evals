method build_audit_trail(events: seq<map<string, string>>) returns (result: seq<map<string, string>>)
  ensures |result| <= |events|
{
  result := [];
  var seq_num := 1;
  var i := 0;
  while i < |events|
    invariant 0 <= i <= |events|
    invariant seq_num == |result| + 1
  {
    var event := events[i];
    if "source_system" in event && "actor_id" in event {
      var record := map["source_system" := event["source_system"],
                        "actor_id" := event["actor_id"],
                        "sequence" := int_to_string(seq_num)];
      if "action" in event {
        record := record["action" := event["action"]];
      }
      result := result + [record];
      seq_num := seq_num + 1;
    }
    i := i + 1;
  }
}

function int_to_string(n: int): string
  requires n >= 0
{
  if n == 0 then "0"
  else if n == 1 then "1"
  else if n == 2 then "2"
  else if n == 3 then "3"
  else if n == 4 then "4"
  else if n == 5 then "5"
  else if n == 6 then "6"
  else if n == 7 then "7"
  else if n == 8 then "8"
  else if n == 9 then "9"
  else int_to_string(n / 10) + int_to_string(n % 10)
}
