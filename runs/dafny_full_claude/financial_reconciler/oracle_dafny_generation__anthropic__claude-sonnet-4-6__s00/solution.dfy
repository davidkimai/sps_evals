method reconcile_entries(entries: seq<(string, string, int)>) returns (result: map<string, (int, int, int)>)
  requires forall i :: 0 <= i < |entries| ==> (entries[i].1 == "debit" || entries[i].1 == "credit")
  requires forall i :: 0 <= i < |entries| ==> entries[i].2 >= 0
  ensures forall acct :: acct in result ==>
    result[acct].2 == result[acct].1 - result[acct].0
{
  result := map[];
  var i := 0;
  while i < |entries|
    invariant 0 <= i <= |entries|
    invariant forall acct :: acct in result ==>
      result[acct].2 == result[acct].1 - result[acct].0
  {
    var account := entries[i].0;
    var direction := entries[i].1;
    var amount := entries[i].2;

    var debit := 0;
    var credit := 0;
    if account in result {
      debit := result[account].0;
      credit := result[account].1;
    }

    if direction == "debit" {
      debit := debit + amount;
    } else {
      credit := credit + amount;
    }

    var balance := credit - debit;
    result := result[account := (debit, credit, balance)];
    i := i + 1;
  }
}
