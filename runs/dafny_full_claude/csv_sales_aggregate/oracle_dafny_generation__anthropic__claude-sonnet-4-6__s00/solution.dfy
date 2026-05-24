method aggregate_sales(csv_text: string) returns (result: seq<map<string, string>>)
{
  // Parse CSV and aggregate sales data
  // Split into lines
  var lines := split_lines(csv_text);
  
  if |lines| == 0 {
    result := [];
    return;
  }
  
  // Parse header
  var header := lines[0];
  var headers := split_by_comma(header);
  
  // Find column indices
  var region_idx := find_index(headers, "region");
  var product_idx := find_index(headers, "product");
  var quantity_idx := find_index(headers, "quantity");
  var cents_idx := find_index(headers, "cents");
  
  if region_idx < 0 || product_idx < 0 || quantity_idx < 0 || cents_idx < 0 {
    result := [];
    return;
  }
  
  // Process data rows - collect keys and values
  var keys: seq<(string, string)> := [];
  var quantities: seq<int> := [];
  var cents_vals: seq<int> := [];
  
  var i := 1;
  while i < |lines|
    invariant 1 <= i <= |lines|
    invariant |keys| == |quantities|
    invariant |keys| == |cents_vals|
  {
    var line := lines[i];
    if |line| > 0 {
      var fields := split_by_comma(line);
      var max_idx := max4(region_idx, product_idx, quantity_idx, cents_idx);
      if |fields| > max_idx {
        var region := fields[region_idx];
        var product := fields[product_idx];
        var qty_str := fields[quantity_idx];
        var cents_str := fields[cents_idx];
        
        var qty_ok, qty_val := parse_int(qty_str);
        var cents_ok, cents_val := parse_int(cents_str);
        
        if qty_ok && cents_ok {
          var key := (region, product);
          var existing := find_key(keys, key);
          if existing < 0 {
            keys := keys + [key];
            quantities := quantities + [qty_val];
            cents_vals := cents_vals + [cents_val];
          } else {
            quantities := quantities[existing := quantities[existing] + qty_val];
            cents_vals := cents_vals[existing := cents_vals[existing] + cents_val];
          }
        }
      }
    }
    i := i + 1;
  }
  
  // Sort by region then product (insertion sort)
  var sorted_keys, sorted_qtys, sorted_cents := sort_results(keys, quantities, cents_vals);
  
  // Build result
  var res: seq<map<string, string>> := [];
  var j := 0;
  while j < |sorted_keys|
    invariant 0 <= j <= |sorted_keys|
  {
    var m := map["region" := sorted_keys[j].0, "product" := sorted_keys[j].1, 
                  "quantity" := int_to_string(sorted_qtys[j]), 
                  "cents" := int_to_string(sorted_cents[j])];
    res := res + [m];
    j := j + 1;
  }
  
  result := res;
}

method sort_results(keys: seq<(string,string)>, qtys: seq<int>, cents: seq<int>) 
  returns (sk: seq<(string,string)>, sq: seq<int>, sc: seq<int>)
  requires |keys| == |qtys| && |qtys| == |cents|
  ensures |sk| == |sq| && |sq| == |sc|
  ensures |sk| == |keys|
{
  sk := keys;
  sq := qtys;
  sc := cents;
  
  // Insertion sort
  var i := 1;
  while i < |sk|
    invariant 0 <= i <= |sk|
    invariant |sk| == |sq| && |sq| == |sc|
    invariant |sk| == |keys|
  {
    var j := i;
    while j > 0 && compare_key(sk[j], sk[j-1])
      invariant 0 <= j <= i
      invariant |sk| == |sq| && |sq| == |sc|
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

function method compare_key(a: (string,string), b: (string,string)): bool
{
  if a.0 < b.0 then true
  else if a.0 == b.0 then a.1 < b.1
  else false
}

function method max4(a: int, b: int, c: int, d: int): int
{
  var ab := if a > b then a else b;
  var cd := if c > d then c else d;
  if ab > cd then ab else cd
}

method find_key(keys: seq<(string,string)>, key: (string,string)) returns (idx: int)
  ensures idx < |keys|
  ensures idx >= 0 ==> keys[idx] == key
{
  var i := 0;
  while i < |keys|
    invariant 0 <= i <= |keys|
  {
    if keys[i] == key {
      idx := i;
      return;
    }
    i := i + 1;
  }
  idx := -1;
}

method find_index(fields: seq<string>, name: string) returns (idx: int)
  ensures idx < |fields|
{
  var i := 0;
  while i < |fields|
    invariant 0 <= i <= |fields|
  {
    if fields[i] == name {
      idx := i;
      return;
    }
    i := i + 1;
  }
  idx := -1;
}

method parse_int(s: string) returns (ok: bool, val: int)
{
  if |s| == 0 {
    ok := false;
    val := 0;
    return;
  }
  
  var start := 0;
  var negative := false;
  
  if s[0] == '-' {
    if |s| == 1 {
      ok := false;
      val := 0;
      return;
    }
    negative := true;
    start := 1;
  }
  
  var result := 0;
  var i := start;
  while i < |s|
    invariant start <= i <= |s|
  {
    var c := s[i];
    if c < '0' || c > '9' {
      ok := false;
      val := 0;
      return;
    }
    result := result * 10 + (c as int - '0' as int);
    i := i + 1;
  }
  
  if i == start {
    ok := false;
    val := 0;
    return;
  }
  
  ok := true;
  val := if negative then -result else result;
}

method int_to_string(n: int) returns (s: string)
{
  if n == 0 {
    s := "0";
    return;
  }
  
  var negative := n < 0;
  var m := if negative then -n else n;
  var digits: string := "";
  
  while m > 0
    invariant m >= 0
  {
    var d := m % 10;
    var c := ('0' as int + d) as char;
    digits := [c] + digits;
    m := m / 10;
  }
  
  s := if negative then "-" + digits else digits;
}

method split_lines(text: string) returns (lines: seq<string>)
{
  var result: seq<string> := [];
  var current: string := "";
  var i := 0;
  
  while i < |text|
    invariant 0 <= i <= |text|
  {
    if text[i] == '\n' {
      // Remove trailing \r if present
      var line := current;
      if |line| > 0 && line[|line|-1] == '\r' {
        line := line[..|line|-1];
      }
      result := result + [line];
      current := "";
    } else {
      current := current + [text[i]];
    }
    i := i + 1;
  }
  
  if |current| > 0 {
    var line := current;
    if |line| > 0 && line[|line|-1] == '\r' {
      line := line[..|line|-1];
    }
    result := result + [line];
  }
  
  lines := result;
}

method split_by_comma(text: string) returns (fields: seq<string>)
{
  var result: seq<string> := [];
  var current: string := "";
  var i := 0;
  
  while i < |text|
    invariant 0 <= i <= |text|
  {
    if text[i] == ',' {
      result := result + [current];
      current := "";
    } else {
      current := current + [text[i]];
    }
    i := i + 1;
  }
  
  result := result + [current];
  fields := result;
}
