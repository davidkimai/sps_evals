method aggregate_sales(csv_text: string) returns (result: seq<map<string, string>>)
{
  // Parse CSV and aggregate sales data
  // Split by newlines first
  var lines := split_lines(csv_text);
  
  if |lines| == 0 {
    result := [];
    return;
  }
  
  // Parse header
  var header := lines[0];
  var header_fields := split_comma(header);
  
  // Find column indices
  var region_idx := find_field(header_fields, "region");
  var product_idx := find_field(header_fields, "product");
  var quantity_idx := find_field(header_fields, "quantity");
  var cents_idx := find_field(header_fields, "cents");
  
  if region_idx < 0 || product_idx < 0 || quantity_idx < 0 || cents_idx < 0 {
    result := [];
    return;
  }
  
  // Process data rows - collect keys and sums
  var keys: seq<(string, string)> := [];
  var quantities: seq<int> := [];
  var cents_vals: seq<int> := [];
  
  var i := 1;
  while i < |lines|
    invariant |keys| == |quantities|
    invariant |keys| == |cents_vals|
  {
    var line := lines[i];
    if |line| > 0 {
      var fields := split_comma(line);
      var max_idx := if region_idx > product_idx then region_idx else product_idx;
      max_idx := if max_idx > quantity_idx then max_idx else quantity_idx;
      max_idx := if max_idx > cents_idx then max_idx else cents_idx;
      
      if max_idx < |fields| {
        var region := trim(fields[region_idx]);
        var product := trim(fields[product_idx]);
        var qty_str := trim(fields[quantity_idx]);
        var cents_str := trim(fields[cents_idx]);
        
        var qty_ok, qty_val := parse_int(qty_str);
        var cents_ok, cents_val := parse_int(cents_str);
        
        if qty_ok && cents_ok {
          // Find existing key
          var key_idx := find_key(keys, region, product);
          if key_idx < 0 {
            keys := keys + [(region, product)];
            quantities := quantities + [qty_val];
            cents_vals := cents_vals + [cents_val];
          } else {
            quantities := quantities[key_idx := quantities[key_idx] + qty_val];
            cents_vals := cents_vals[key_idx := cents_vals[key_idx] + cents_val];
          }
        }
      }
    }
    i := i + 1;
  }
  
  // Sort by region then product
  var sorted_keys, sorted_quantities, sorted_cents := sort_results(keys, quantities, cents_vals);
  
  // Build result
  result := [];
  var j := 0;
  while j < |sorted_keys|
  {
    var entry := map["region" := sorted_keys[j].0, "product" := sorted_keys[j].1, 
                     "quantity" := int_to_string(sorted_quantities[j]),
                     "cents" := int_to_string(sorted_cents[j])];
    result := result + [entry];
    j := j + 1;
  }
}

method split_lines(s: string) returns (lines: seq<string>)
{
  lines := [];
  var current := "";
  var i := 0;
  while i < |s|
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

method split_comma(s: string) returns (fields: seq<string>)
{
  fields := [];
  var current := "";
  var i := 0;
  while i < |s|
  {
    if s[i] == ',' {
      fields := fields + [current];
      current := "";
    } else {
      current := current + [s[i]];
    }
    i := i + 1;
  }
  fields := fields + [current];
}

method find_field(fields: seq<string>, name: string) returns (idx: int)
{
  idx := -1;
  var i := 0;
  while i < |fields|
  {
    if trim_val(fields[i]) == name {
      idx := i;
      return;
    }
    i := i + 1;
  }
}

function trim_val(s: string): string
{
  trim_right(trim_left(s))
}

function trim_left(s: string): string
{
  if |s| == 0 then s
  else if s[0] == ' ' || s[0] == '\t' then trim_left(s[1..])
  else s
}

function trim_right(s: string): string
{
  if |s| == 0 then s
  else if s[|s|-1] == ' ' || s[|s|-1] == '\t' then trim_right(s[..|s|-1])
  else s
}

method trim(s: string) returns (r: string)
{
  r := trim_val(s);
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
  
  var result := 0;
  var i := start;
  while i < |s|
  {
    var c := s[i];
    if c < '0' || c > '9' {
      return;
    }
    result := result * 10 + (c as int - '0' as int);
    i := i + 1;
  }
  
  ok := true;
  val := if negative then -result else result;
}

method find_key(keys: seq<(string, string)>, region: string, product: string) returns (idx: int)
{
  idx := -1;
  var i := 0;
  while i < |keys|
  {
    if keys[i].0 == region && keys[i].1 == product {
      idx := i;
      return;
    }
    i := i + 1;
  }
}

method sort_results(keys: seq<(string, string)>, quantities: seq<int>, cents: seq<int>) 
  returns (sk: seq<(string, string)>, sq: seq<int>, sc: seq<int>)
  requires |keys| == |quantities|
  requires |keys| == |cents|
  ensures |sk| == |sq|
  ensures |sk| == |sc|
  ensures |sk| == |keys|
{
  // Insertion sort by (region, product)
  sk := keys;
  sq := quantities;
  sc := cents;
  
  var i := 1;
  while i < |sk|
    invariant |sk| == |sq|
    invariant |sk| == |sc|
    invariant |sk| == |keys|
  {
    var j := i;
    while j > 0 && string_pair_gt(sk[j-1], sk[j])
      invariant |sk| == |sq|
      invariant |sk| == |sc|
      invariant |sk| == |keys|
    {
      var tmp_k := sk[j];
      var tmp_q := sq[j];
      var tmp_c := sc[j];
      sk := sk[j := sk[j-1]][j-1 := tmp_k];
      sq := sq[j := sq[j-1]][j-1 := tmp_q];
      sc := sc[j := sc[j-1]][j-1 := tmp_c];
      j := j - 1;
    }
    i := i + 1;
  }
}

predicate string_pair_gt(a: (string, string), b: (string, string))
{
  string_gt(a.0, b.0) || (a.0 == b.0 && string_gt(a.1, b.1))
}

predicate string_gt(a: string, b: string)
{
  exists i :: 0 <= i <= |a| && i <= |b| && 
    (forall j :: 0 <= j < i ==> a[j] == b[j]) &&
    (i == |b| ==> i < |a|) &&
    (i < |a| && i < |b| ==> a[i] > b[i])
}

method int_to_string(n: int) returns (s: string)
{
  if n == 0 {
    s := "0";
    return;
  }
  
  var negative := n < 0;
  var m := if negative then -n else n;
  s := "";
  
  while m > 0
  {
    var digit := m % 10;
    var c := ('0' as int + digit) as char;
    s := [c] + s;
    m := m / 10;
  }
  
  if negative {
    s := "-" + s;
  }
}
