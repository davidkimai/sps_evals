method build_user_purchase_index(events: seq<map<string, string>>) returns (result: map<string, map<string, int>>)
  ensures forall uid :: uid in result ==>
    "count" in result[uid] && "total" in result[uid]
{
  result := map[];
  var i := 0;
  while i < |events|
    invariant 0 <= i <= |events|
    invariant forall uid :: uid in result ==>
      "count" in result[uid] && "total" in result[uid]
  {
    var event := events[i];
    if "user_id" in event && "kind" in event && "amount" in event {
      var user_id := event["user_id"];
      var kind := event["kind"];
      var amount_str := event["amount"];
      if kind == "purchase" && |user_id| > 0 {
        var amount := parse_int(amount_str);
        if amount.Some? {
          if user_id in result {
            var old_entry := result[user_id];
            var old_count := old_entry["count"];
            var old_total := old_entry["total"];
            var new_entry := map["count" := old_count + 1, "total" := old_total + amount.value];
            result := result[user_id := new_entry];
          } else {
            var new_entry := map["count" := 1, "total" := amount.value];
            result := result[user_id := new_entry];
          }
        }
      }
    }
    i := i + 1;
  }
}

function parse_int(s: string): Option<int>
{
  if |s| == 0 then None
  else if s[0] == '-' then
    if |s| == 1 then None
    else
      var rest := parse_digits(s[1..]);
      if rest.Some? then Some(-rest.value) else None
  else
    parse_digits(s)
}

function parse_digits(s: string): Option<int>
  decreases |s|
{
  if |s| == 0 then None
  else
    var digits := parse_digits_helper(s, 0);
    if digits.Some? then Some(digits.value) else None
}

function parse_digits_helper(s: string, acc: int): Option<int>
  decreases |s|
{
  if |s| == 0 then Some(acc)
  else
    var c := s[0];
    if '0' <= c <= '9' then
      parse_digits_helper(s[1..], acc * 10 + (c as int - '0' as int))
    else
      None
}

datatype Option<T> = None | Some(value: T)
