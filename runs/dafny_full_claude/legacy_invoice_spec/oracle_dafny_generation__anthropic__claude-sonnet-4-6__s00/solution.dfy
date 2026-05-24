method summarize_invoices(invoices: seq<map<string, string>>) returns (result: seq<map<string, string>>)
{
  // We'll process invoices where status == "paid" and region is non-empty
  // Since Dafny doesn't have dynamic typing, we model amount_cents as string here
  // but the actual logic will be handled in the compiled output
  
  // Collect paid invoices grouped by region
  var regionMap: map<string, (int, int)> := map[];
  
  var i := 0;
  while i < |invoices|
  {
    var inv := invoices[i];
    if "status" in inv && "region" in inv && "amount_cents" in inv {
      var status := inv["status"];
      var region := inv["region"];
      var amountStr := inv["amount_cents"];
      if status == "paid" && |region| > 0 {
        // Parse amount as integer (simplified - we store as string in map)
        var amount := parse_int(amountStr);
        if amount.0 {
          var amt := amount.1;
          if region in regionMap {
            var existing := regionMap[region];
            regionMap := regionMap[region := (existing.0 + 1, existing.1 + amt)];
          } else {
            regionMap := regionMap[region := (1, amt)];
          }
        }
      }
    }
    i := i + 1;
  }
  
  // Convert map to sequence
  var regions := map_keys_sorted(regionMap);
  result := [];
  var j := 0;
  while j < |regions|
  {
    var region := regions[j];
    var data := regionMap[region];
    var row := map["bucket_code" := region, 
                    "item_count" := int_to_string(data.0),
                    "cents_total" := int_to_string(data.1)];
    result := result + [row];
    j := j + 1;
  }
}

method parse_int(s: string) returns (result: (bool, int))
{
  if |s| == 0 {
    result := (false, 0);
    return;
  }
  
  var negative := false;
  var start := 0;
  
  if s[0] == '-' {
    negative := true;
    start := 1;
    if |s| == 1 {
      result := (false, 0);
      return;
    }
  }
  
  var value := 0;
  var k := start;
  while k < |s|
  {
    var c := s[k];
    if c < '0' || c > '9' {
      result := (false, 0);
      return;
    }
    value := value * 10 + (c as int - '0' as int);
    k := k + 1;
  }
  
  if negative {
    result := (true, -value);
  } else {
    result := (true, value);
  }
}

method int_to_string(n: int) returns (result: string)
{
  if n == 0 {
    result := "0";
    return;
  }
  
  var negative := n < 0;
  var value := if negative then -n else n;
  var s := "";
  
  while value > 0
  {
    var digit := value % 10;
    var c := ('0' as int + digit) as char;
    s := [c] + s;
    value := value / 10;
  }
  
  if negative {
    result := "-" + s;
  } else {
    result := s;
  }
}

method map_keys_sorted(m: map<string, (int, int)>) returns (result: seq<string>)
{
  var keys: seq<string> := [];
  
  // Collect all keys
  var remaining := m;
  // We need to iterate over map keys - use a different approach
  keys := collect_keys(m);
  
  // Sort keys using insertion sort
  result := insertion_sort(keys);
}

method collect_keys(m: map<string, (int, int)>) returns (result: seq<string>)
{
  result := [];
  var seen := m;
  // In Dafny, we iterate by repeatedly finding a key
  while |seen| > 0
  {
    var k :| k in seen;
    result := result + [k];
    seen := map k' | k' in seen && k' != k :: seen[k'];
  }
}

method insertion_sort(keys: seq<string>) returns (result: seq<string>)
{
  result := keys;
  var i := 1;
  while i < |result|
  {
    var key := result[i];
    var j := i;
    while j > 0 && string_less(key, result[j-1])
    {
      result := result[j-1 := result[j]][j := result[j-1]];
      j := j - 1;
    }
    i := i + 1;
  }
}

predicate method string_less(a: string, b: string)
{
  if |a| == 0 then |b| > 0
  else if |b| == 0 then false
  else if a[0] != b[0] then a[0] < b[0]
  else string_less(a[1..], b[1..])
}
