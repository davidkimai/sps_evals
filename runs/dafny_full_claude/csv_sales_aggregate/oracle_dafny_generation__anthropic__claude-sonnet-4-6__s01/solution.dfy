method aggregate_sales(csv_text: string) returns (result: seq<map<string, string>>)
{
  // Parse CSV and aggregate sales data
  // We'll implement this procedurally
  
  var lines := split_lines(csv_text);
  
  if |lines| == 0 {
    result := [];
    return;
  }
  
  // Find header line
  var header := lines[0];
  var headers := split_by_comma(header);
  
  // Find column indices
  var region_idx := -1;
  var product_idx := -1;
  var quantity_idx := -1;
  var cents_idx := -1;
  
  var hi := 0;
  while hi < |headers|
    invariant 0 <= hi <= |headers|
  {
    var h := strip(headers[hi]);
    if h == "region" {
      region_idx := hi;
    } else if h == "product" {
      product_idx := hi;
    } else if h == "quantity" {
      quantity_idx := hi;
    } else if h == "cents" {
      cents_idx := hi;
    }
    hi := hi + 1;
  }
  
  // If any required column is missing, return empty
  if region_idx == -1 || product_idx == -1 || quantity_idx == -1 || cents_idx == -1 {
    result := [];
    return;
  }
  
  // Process data rows
  // We'll store keys as "region|||product" and accumulate sums
  var keys: seq<string> := [];
  var quantities: seq<int> := [];
  var cents_vals: seq<int> := [];
  var regions_list: seq<string> := [];
  var products_list: seq<string> := [];
  
  var li := 1;
  while li < |lines|
    invariant 1 <= li <= |lines|
    invariant |keys| == |quantities|
    invariant |keys| == |cents_vals|
    invariant |keys| == |regions_list|
    invariant |keys| == |products_list|
  {
    var line := lines[li];
    if |line| > 0 {
      var fields := split_by_comma(line);
      
      // Check we have enough fields
      var max_idx := region_idx;
      if product_idx > max_idx { max_idx := product_idx; }
      if quantity_idx > max_idx { max_idx := quantity_idx; }
      if cents_idx > max_idx { max_idx := cents_idx; }
      
      if |fields| > max_idx {
        var region_val := strip(fields[region_idx]);
        var product_val := strip(fields[product_idx]);
        var quantity_str := strip(fields[quantity_idx]);
        var cents_str := strip(fields[cents_idx]);
        
        var qty_ok, qty_val := parse_int(quantity_str);
        var cts_ok, cts_val := parse_int(cents_str);
        
        if qty_ok && cts_ok && |region_val| > 0 && |product_val| > 0 {
          var key := region_val + "|||" + product_val;
          
          // Find existing key
          var found := false;
          var fi := 0;
          while fi < |keys|
            invariant 0 <= fi <= |keys|
          {
            if keys[fi] == key {
              quantities := quantities[fi := quantities[fi] + qty_val];
              cents_vals := cents_vals[fi := cents_vals[fi] + cts_val];
              found := true;
              break;
            }
            fi := fi + 1;
          }
          
          if !found {
            keys := keys + [key];
            quantities := quantities + [qty_val];
            cents_vals := cents_vals + [cts_val];
            regions_list := regions_list + [region_val];
            products_list := products_list + [product_val];
          }
        }
      }
    }
    li := li + 1;
  }
  
  // Sort by region then product (insertion sort)
  var n := |keys|;
  var sorted_indices := seq(n, i => i);
  
  // Bubble sort on sorted_indices
  var si := 0;
  while si < n
    invariant 0 <= si <= n
    invariant |sorted_indices| == n
  {
    var sj := si + 1;
    while sj < n
      invariant si < sj <= n || sj == n
      invariant |sorted_indices| == n
    {
      var ia := sorted_indices[si];
      var ib := sorted_indices[sj];
      var cmp := compare_strings(regions_list[ia], regions_list[ib]);
      if cmp > 0 || (cmp == 0 && compare_strings(products_list[ia], products_list[ib]) > 0) {
        sorted_indices := sorted_indices[si := ib][sj := ia];
      }
      sj := sj + 1;
    }
    si := si + 1;
  }
  
  // Build result
  var res: seq<map<string, string>> := [];
  var ri := 0;
  while ri < n
    invariant 0 <= ri <= n
  {
    var idx := sorted_indices[ri];
    var row := map["region" := regions_list[idx], 
                   "product" := products_list[idx],
                   "quantity" := int_to_string(quantities[idx]),
                   "cents" := int_to_string(cents_vals[idx])];
    res := res + [row];
    ri := ri + 1;
  }
  
  result := res;
}

method split_lines(s: string) returns (lines: seq<string>)
{
  lines := [];
  var current: string := "";
  var i := 0;
  while i < |s|
    invariant 0 <= i <= |s|
  {
    if s[i] == '\n' {
      lines := lines + [current];
      current := "";
    } else if s[i] == '\r' {
      // skip carriage return
    } else {
      current := current + [s[i]];
    }
    i := i + 1;
  }
  if |current| > 0 {
    lines := lines + [current];
  }
}

method split_by_comma(s: string) returns (parts: seq<string>)
{
  parts := [];
  var current: string := "";
  var i := 0;
  while i < |s|
    invariant 0 <= i <= |s|
  {
    if s[i] == ',' {
      parts := parts + [current];
      current := "";
    } else {
      current := current + [s[i]];
    }
    i := i + 1;
  }
  parts := parts + [current];
}

method strip(s: string) returns (result: string)
{
  var start := 0;
  while start < |s| && (s[start] == ' ' || s[start] == '\t')
    invariant 0 <= start <= |s|
  {
    start := start + 1;
  }
  var end := |s|;
  while end > start && (s[end-1] == ' ' || s[end-1] == '\t')
    invariant start <= end <= |s|
  {
    end := end - 1;
  }
  result := s[start..end];
}

method parse_int(s: string) returns (ok: bool, val: int)
{
  ok := false;
  val := 0;
  
  if |s| == 0 {
    return;
  }
  
  var start := 0;
  var negative := false;
  
  if s[0] == '-' {
    negative := true;
    start := 1;
  } else if s[0] == '+' {
    start := 1;
  }
  
  if start >= |s| {
    return;
  }
  
  var i := start;
  var result := 0;
  while i < |s|
    invariant start <= i <= |s|
  {
    var c := s[i];
    if c >= '0' && c <= '9' {
      result := result * 10 + (c as int - '0' as int);
    } else {
      return;
    }
    i := i + 1;
  }
  
  ok := true;
  if negative {
    val := -result;
  } else {
    val := result;
  }
}

function compare_strings(a: string, b: string): int
{
  if a == b then 0
  else if a < b then -1
  else 1
}

method int_to_string(n: int) returns (s: string)
{
  if n == 0 {
    s := "0";
    return;
  }
  
  var negative := n < 0;
  var num := if negative then -n else n;
  var digits: string := "";
  
  while num > 0
    invariant num >= 0
    decreases num
  {
    var d := num % 10;
    var c: char := (d + '0' as int) as char;
    digits := [c] + digits;
    num := num / 10;
  }
  
  if negative {
    s := "-" + digits;
  } else {
    s := digits;
  }
}
