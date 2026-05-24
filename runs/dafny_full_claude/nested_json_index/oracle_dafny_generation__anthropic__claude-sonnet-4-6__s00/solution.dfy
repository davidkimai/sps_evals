method build_user_purchase_index(events: seq<map<string, string>>) returns (result: map<string, map<string, int>>)
  ensures forall uid :: uid in result ==>
    "count" in result[uid] && "total" in result[uid] &&
    result[uid]["count"] >= 0
{
  result := map[];
  var i := 0;
  while i < |events|
    invariant 0 <= i <= |events|
    invariant forall uid :: uid in result ==>
      "count" in result[uid] && "total" in result[uid] &&
      result[uid]["count"] >= 0
  {
    var event := events[i];
    if "user_id" in event && "kind" in event && "amount" in event {
      var user_id := event["user_id"];
      var kind := event["kind"];
      var amount_str := event["amount"];
      if kind == "purchase" && |user_id| > 0 {
        // Parse amount as integer - we encode amount as string for Dafny's type system
        // In the compiled Python version, the actual dict values will be proper types
        var amount := parse_int(amount_str);
        if amount.Some? {
          if user_id in result {
            var old_entry := result[user_id];
            var new_count := old_entry["count"] + 1;
            var new_total := old_entry["total"] + amount.value;
            result := result[user_id := map["count" := new_count, "total" := new_total]];
          } else {
            result := result[user_id := map["count" := 1, "total" := amount.value]];
          }
        }
      }
    }
    i := i + 1;
  }
}

datatype Option<T> = None | Some(value: T)

function parse_int(s: string): Option<int>
{
  if |s| == 0 then None
  else if s[0] == '-' then
    if |s| == 1 then None
    else
      var rest := parse_nat(s[1..]);
      if rest.Some? then Some(-rest.value) else None
  else
    var n := parse_nat(s);
    if n.Some? then Some(n.value) else None
}

function parse_nat(s: string): Option<int>
{
  if |s| == 0 then None
  else parse_nat_helper(s, 0)
}

function parse_nat_helper(s: string, acc: int): Option<int>
  requires acc >= 0
{
  if |s| == 0 then Some(acc)
  else
    var c := s[0];
    if '0' <= c <= '9' then
      parse_nat_helper(s[1..], acc * 10 + (c as int - '0' as int))
    else
      None
}
