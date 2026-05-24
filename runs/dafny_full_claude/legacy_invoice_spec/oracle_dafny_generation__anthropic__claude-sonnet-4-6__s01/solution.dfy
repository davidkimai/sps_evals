datatype InvoiceRow = InvoiceRow(region: string, amount_cents: int)

method summarize_invoices_typed(invoices: seq<InvoiceRow>) returns (result: seq<map<string, string>>)
  ensures |result| >= 0
{
  // Collect unique regions from paid invoices
  var regions: seq<string> := [];
  var i := 0;
  while i < |invoices|
    invariant 0 <= i <= |invoices|
  {
    var inv := invoices[i];
    if inv.region != "" {
      var found := false;
      var j := 0;
      while j < |regions|
        invariant 0 <= j <= |regions|
      {
        if regions[j] == inv.region {
          found := true;
          break;
        }
        j := j + 1;
      }
      if !found {
        regions := regions + [inv.region];
      }
    }
    i := i + 1;
  }

  // Sort regions lexicographically (insertion sort)
  var sortedRegions := regions;
  var k := 1;
  while k < |sortedRegions|
    invariant 0 <= k <= |sortedRegions|
    invariant |sortedRegions| == |regions|
  {
    var key := sortedRegions[k];
    var m := k - 1;
    while m >= 0 && sortedRegions[m] > key
      invariant -1 <= m
    {
      if m + 1 < |sortedRegions| {
        sortedRegions := sortedRegions[0..m+1] + [sortedRegions[m]] + sortedRegions[m+2..];
      }
      m := m - 1;
    }
    if m + 1 < |sortedRegions| {
      sortedRegions := sortedRegions[0..m+1] + [key] + sortedRegions[m+2..];
    }
    k := k + 1;
  }

  result := [];
  var r := 0;
  while r < |sortedRegions|
    invariant 0 <= r <= |sortedRegions|
    invariant |result| == r
  {
    var reg := sortedRegions[r];
    var count := 0;
    var total := 0;
    var n := 0;
    while n < |invoices|
      invariant 0 <= n <= |invoices|
    {
      var inv := invoices[n];
      if inv.region == reg {
        count := count + 1;
        total := total + inv.amount_cents;
      }
      n := n + 1;
    }
    var row: map<string, string> := map["bucket_code" := reg, "item_count" := intToString(count), "cents_total" := intToString(total)];
    result := result + [row];
    r := r + 1;
  }
}

function intToString(n: int): string
{
  if n == 0 then "0"
  else if n < 0 then "-" + natToString(-n)
  else natToString(n)
}

function natToString(n: int): string
  requires n >= 0
{
  if n == 0 then ""
  else natToString(n / 10) + [48 + (n % 10) as char]
}

method Main()
{
  var invoices := [InvoiceRow("west", 100), InvoiceRow("east", 200), InvoiceRow("west", 50)];
  var result := summarize_invoices_typed(invoices);
  print |result|, "\n";
}
