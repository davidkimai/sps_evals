method merge_policy(defaults: map<string, int>, override: map<string, int>) returns (result: map<string, int>)
  ensures forall k :: k in override && override[k] != -999999 ==> k in result && result[k] == override[k]
  ensures forall k :: k in defaults && k !in override ==> k in result && result[k] == defaults[k]
  ensures forall k :: k in override && override[k] == -999999 ==> k !in result
{
  result := defaults;
  var keys := override.Keys;
  var keySeq: seq<string> := [];
  
  // Convert keys to sequence
  var remaining := keys;
  while remaining != {}
    decreases |remaining|
  {
    var k :| k in remaining;
    keySeq := keySeq + [k];
    remaining := remaining - {k};
  }
  
  var i := 0;
  while i < |keySeq|
    invariant 0 <= i <= |keySeq|
    invariant forall k :: k in result ==> (k in defaults || k in override)
  {
    var k := keySeq[i];
    if override[k] == -999999 {
      // Remove key (None represented as -999999)
      if k in result {
        result := result - {k};
      }
    } else {
      result := result[k := override[k]];
    }
    i := i + 1;
  }
}

method Main() {
  // Test basic merge
  var defaults := map["a" := 1, "b" := 2, "c" := 3];
  var override := map["b" := 20, "d" := 4];
  var result := merge_policy(defaults, override);
  
  assert "a" in result;
  assert "b" in result;
  assert "d" in result;
  
  print "merge_policy basic test done\n";
  
  // Test removal with sentinel -999999
  var defaults2 := map["a" := 1, "b" := 2];
  var override2 := map["b" := -999999];
  var result2 := merge_policy(defaults2, override2);
  
  assert "a" in result2;
  assert "b" !in result2;
  
  print "merge_policy removal test done\n";
}
