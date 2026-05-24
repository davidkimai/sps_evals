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
        // Parse amount - we'll handle this via the string representation
        // In the Dafny model, we treat amount as stored in the map
        // For the compiled Python version, we need actual integer parsing
        // We'll use a helper approach
        var amount := parse_int(amount_str);
        if amount.Some? {
          if user_id in result {
            var old_count := result[user_id]["count"];
            var old_total := result[user_id]["total"];
            result := result[user_id := map["count" := old_count + 1, "total" := old_total + amount.value]];
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
  ensures parse_nat(s).Some? ==> parse_nat(s).value >= 0
{
  if |s| == 0 then None
  else parse_nat_helper(s, 0, 0)
}

function parse_nat_helper(s: string, idx: int, acc: int): Option<int>
  requires 0 <= idx <= |s|
  requires acc >= 0
  ensures parse_nat_helper(s, idx, acc).Some? ==> parse_nat_helper(s, idx, acc).value >= 0
  decreases |s| - idx
{
  if idx == |s| then
    if idx == 0 then None else Some(acc)
  else
    var c := s[idx];
    if '0' <= c <= '9' then
      parse_nat_helper(s, idx + 1, acc * 10 + (c as int - '0' as int))
    else
      None
}
