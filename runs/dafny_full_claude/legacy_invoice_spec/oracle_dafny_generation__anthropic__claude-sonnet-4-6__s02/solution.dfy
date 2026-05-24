method summarize_invoices(invoices: seq<map<string, string>>) returns (result: seq<map<string, string>>)
{
    // We model invoices as seq<map<string,string>> where amount_cents is stored as string
    // Filter paid invoices with non-empty region
    var filtered: seq<(string, int)> := [];
    
    var i := 0;
    while i < |invoices|
    {
        var inv := invoices[i];
        if "status" in inv && "region" in inv && "amount_cents" in inv {
            var status := inv["status"];
            var region := inv["region"];
            var amount_str := inv["amount_cents"];
            if status == "paid" && |region| > 0 {
                var amount := parse_int(amount_str);
                if amount.Some? {
                    filtered := filtered + [(region, amount.value)];
                }
            }
        }
        i := i + 1;
    }
    
    // Group by region: collect unique regions
    var regions: seq<string> := [];
    var j := 0;
    while j < |filtered|
    {
        var region := filtered[j].0;
        if !contains_string(regions, region) {
            regions := regions + [region];
        }
        j := j + 1;
    }
    
    // Sort regions lexicographically
    regions := sort_strings(regions);
    
    // Build result
    result := [];
    var k := 0;
    while k < |regions|
    {
        var region := regions[k];
        var count := 0;
        var total := 0;
        var m := 0;
        while m < |filtered|
        {
            if filtered[m].0 == region {
                count := count + 1;
                total := total + filtered[m].1;
            }
            m := m + 1;
        }
        var row := map["bucket_code" := region, "item_count" := int_to_string(count), "cents_total" := int_to_string(total)];
        result := result + [row];
        k := k + 1;
    }
}

function parse_int(s: string): Option<int>
{
    if |s| == 0 then None
    else if s[0] == '-' then
        if |s| == 1 then None
        else
            var mag := parse_nat(s[1..]);
            if mag.Some? then Some(-mag.value) else None
    else
        var mag := parse_nat(s);
        if mag.Some? then Some(mag.value) else None
}

function parse_nat(s: string): Option<int>
{
    if |s| == 0 then None
    else parse_nat_helper(s, 0, 0)
}

function parse_nat_helper(s: string, idx: int, acc: int): Option<int>
    requires 0 <= idx <= |s|
    decreases |s| - idx
{
    if idx == |s| then Some(acc)
    else
        var c := s[idx];
        if '0' <= c <= '9' then
            parse_nat_helper(s, idx + 1, acc * 10 + (c as int - '0' as int))
        else
            None
}

function contains_string(ss: seq<string>, s: string): bool
{
    exists i :: 0 <= i < |ss| && ss[i] == s
}

method sort_strings(ss: seq<string>) returns (sorted: seq<string>)
    ensures |sorted| == |ss|
    ensures forall i, j :: 0 <= i < j < |sorted| ==> string_le(sorted[i], sorted[j])
{
    sorted := ss;
    var n := |sorted|;
    var i := 0;
    while i < n
        invariant 0 <= i <= n
        invariant |sorted| == n
    {
        var j := i + 1;
        while j < n
            invariant i < j <= n
            invariant |sorted| == n
        {
            if !string_le(sorted[i], sorted[j]) {
                var tmp := sorted[i];
                sorted := sorted[i := sorted[j]][j := tmp];
            }
            j := j + 1;
        }
        i := i + 1;
    }
}

function string_le(a: string, b: string): bool
{
    if |a| == 0 then true
    else if |b| == 0 then false
    else if a[0] < b[0] then true
    else if a[0] > b[0] then false
    else string_le(a[1..], b[1..])
}

function int_to_string(n: int): string
    decreases if n < 0 then -n + 1 else n + 1
{
    if n < 0 then "-" + int_to_string(-n)
    else if n < 10 then [('0' as int + n) as char]
    else int_to_string(n / 10) + [('0' as int + n % 10) as char]
}

datatype Option<T> = None | Some(value: T)
