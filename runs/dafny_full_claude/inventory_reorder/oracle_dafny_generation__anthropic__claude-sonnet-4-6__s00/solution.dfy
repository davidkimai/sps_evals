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
  vel_skus: seq<string>,
  vel_vals: seq<int>
) returns (result_skus: seq<string>, result_qtys: seq<int>)
  requires |skus| == |on_hands| == |targets| == |case_packs|
  requires |vel_skus| == |vel_vals|
  ensures |result_skus| == |result_qtys|
{
  var out_skus: seq<string> := [];
  var out_qtys: seq<int> := [];
  
  var i := 0;
  while i < |skus|
    invariant 0 <= i <= |skus|
    invariant |out_skus| == |out_qtys|
  {
    var sku := skus[i];
    var on_hand := on_hands[i];
    var target := targets[i];
    var case_pack := case_packs[i];
    
    if case_pack > 0 {
      // Look up velocity
      var velocity := 0;
      var j := 0;
      while j < |vel_skus|
        invariant 0 <= j <= |vel_skus|
      {
        if vel_skus[j] == sku {
          velocity := vel_vals[j];
          j := |vel_skus|; // break
        } else {
          j := j + 1;
        }
      }
      
      if velocity > 0 {
        if on_hand < target {
          var deficit := target - on_hand;
          var qty := RoundUpToMultiple(deficit, case_pack);
          // Insert in sorted order by sku
          var pos := 0;
          while pos < |out_skus| && out_skus[pos] < sku
            invariant 0 <= pos <= |out_skus|
          {
            pos := pos + 1;
          }
          out_skus := out_skus[..pos] + [sku] + out_skus[pos..];
          out_qtys := out_qtys[..pos] + [qty] + out_qtys[pos..];
        }
      }
    }
    
    i := i + 1;
  }
  
  result_skus := out_skus;
  result_qtys := out_qtys;
}
