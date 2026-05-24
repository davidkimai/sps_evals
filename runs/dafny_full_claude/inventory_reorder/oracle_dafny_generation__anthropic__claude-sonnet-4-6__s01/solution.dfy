method RoundUpToMultiple(deficit: int, case_pack: int) returns (result: int)
  requires case_pack > 0
  requires deficit > 0
  ensures result > 0
  ensures result % case_pack == 0
  ensures result >= deficit
{
  var q := deficit / case_pack;
  var r := deficit % case_pack;
  if r == 0 {
    result := q * case_pack;
  } else {
    result := (q + 1) * case_pack;
  }
}

method reorder_plan(items: seq<map<string, string>>, sales_velocity: map<string, int>) returns (result: seq<map<string, string>>)
{
  var orders: seq<map<string, string>> := [];
  
  var i := 0;
  while i < |items|
    invariant 0 <= i <= |items|
  {
    var item := items[i];
    i := i + 1;
    
    // Check required fields exist
    if "sku" !in item || "on_hand" !in item || "target" !in item || "case_pack" !in item {
      continue;
    }
    
    var sku := item["sku"];
    var on_hand_str := item["on_hand"];
    var target_str := item["target"];
    var case_pack_str := item["case_pack"];
    
    // Parse integers - we'll use a helper
    var on_hand_opt := ParseInt(on_hand_str);
    var target_opt := ParseInt(target_str);
    var case_pack_opt := ParseInt(case_pack_str);
    
    if on_hand_opt.None? || target_opt.None? || case_pack_opt.None? {
      continue;
    }
    
    var on_hand := on_hand_opt.value;
    var target := target_opt.value;
    var case_pack := case_pack_opt.value;
    
    // Skip non-positive case_pack
    if case_pack <= 0 {
      continue;
    }
    
    // Check sales velocity
    if sku !in sales_velocity {
      continue;
    }
    var velocity := sales_velocity[sku];
    if velocity <= 0 {
      continue;
    }
    
    // Check if reorder needed
    if on_hand >= target {
      continue;
    }
    
    var deficit := target - on_hand;
    var reorder_qty := RoundUpToMultiple(deficit, case_pack);
    
    var reorder_qty_str := IntToString(reorder_qty);
    var order := map["sku" := sku, "reorder_quantity" := reorder_qty_str];
    orders := orders + [order];
  }
  
  // Sort by sku
  result := SortBySku(orders);
}

datatype Option<T> = None | Some(value: T)

function ParseInt(s: string): Option<int>
{
  if |s| == 0 then None
  else if s[0] == '-' then
    var rest := ParseNonNegInt(s[1..]);
    if rest.None? then None
    else if rest.value == 0 then Some(0)
    else Some(-rest.value)
  else
    ParseNonNegInt(s)
}

function ParseNonNegInt(s: string): Option<int>
{
  if |s| == 0 then None
  else ParseNonNegIntHelper(s, 0)
}

function ParseNonNegIntHelper(s: string, acc: int): Option<int>
{
  if |s| == 0 then Some(acc)
  else
    var c := s[0];
    if c < '0' || c > '9' then None
    else ParseNonNegIntHelper(s[1..], acc * 10 + (c as int - '0' as int))
}

function IntToString(n: int): string
  requires n >= 0
{
  if n == 0 then "0"
  else IntToStringHelper(n, "")
}

function IntToStringHelper(n: int, acc: string): string
  requires n >= 0
  decreases n
{
  if n == 0 then acc
  else
    var digit := n % 10;
    var c := ('0' as int + digit) as char;
    IntToStringHelper(n / 10, [c] + acc)
}

method SortBySku(orders: seq<map<string, string>>) returns (result: seq<map<string, string>>)
  ensures |result| == |orders|
{
  var arr := orders;
  var n := |arr|;
  var j := 0;
  while j < n
    invariant 0 <= j <= n
    invariant |arr| == n
  {
    var k := j;
    var min_idx := j;
    while k < n
      invariant j <= k <= n
      invariant j <= min_idx < n
      invariant |arr| == n
    {
      if "sku" in arr[k] && "sku" in arr[min_idx] {
        if arr[k]["sku"] < arr[min_idx]["sku"] {
          min_idx := k;
        }
      }
      k := k + 1;
    }
    if min_idx != j {
      var tmp := arr[j];
      arr := arr[min_idx := arr[j]][j := tmp];
    }
    j := j + 1;
  }
  result := arr;
}
