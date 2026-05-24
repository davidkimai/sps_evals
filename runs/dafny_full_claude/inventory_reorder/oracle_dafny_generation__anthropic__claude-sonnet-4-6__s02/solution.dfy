method RoundUpToMultiple(deficit: int, case_pack: int) returns (result: int)
  requires case_pack > 0
  requires deficit > 0
  ensures result > 0
  ensures result % case_pack == 0
  ensures result >= deficit
{
  result := ((deficit + case_pack - 1) / case_pack) * case_pack;
}

method reorder_plan(
  skus: seq<string>,
  on_hands: seq<int>,
  targets: seq<int>,
  case_packs: seq<int>,
  valid: seq<bool>,
  velocities: map<string, int>
) returns (result_skus: seq<string>, result_qtys: seq<int>)
  requires |skus| == |on_hands| == |targets| == |case_packs| == |valid|
  ensures |result_skus| == |result_qtys|
{
  var n := |skus|;
  var r_skus: seq<string> := [];
  var r_qtys: seq<int> := [];

  var i := 0;
  while i < n
    invariant 0 <= i <= n
    invariant |r_skus| == |r_qtys|
  {
    if valid[i] && case_packs[i] > 0 {
      var sku := skus[i];
      var on_hand := on_hands[i];
      var target := targets[i];
      var case_pack := case_packs[i];

      var velocity := 0;
      if sku in velocities {
        velocity := velocities[sku];
      }

      if velocity > 0 && on_hand < target {
        var deficit := target - on_hand;
        var qty := RoundUpToMultiple(deficit, case_pack);
        r_skus := r_skus + [sku];
        r_qtys := r_qtys + [qty];
      }
    }
    i := i + 1;
  }

  // Sort by sku (insertion sort)
  var rs := r_skus;
  var rq := r_qtys;
  var m := |rs|;
  var j := 1;
  while j < m
    invariant 0 <= j <= m
    invariant |rs| == |rq| == m
  {
    var key_s := rs[j];
    var key_q := rq[j];
    var k := j;
    while k > 0 && rs[k-1] > key_s
      invariant 0 <= k <= j
      invariant |rs| == |rq| == m
    {
      rs := rs[k-1 := rs[k]][k := rs[k-1]];
      rq := rq[k-1 := rq[k]][k := rq[k-1]];
      k := k - 1;
    }
    rs := rs[k := key_s];
    rq := rq[k := key_q];
    j := j + 1;
  }

  result_skus := rs;
  result_qtys := rq;
}
