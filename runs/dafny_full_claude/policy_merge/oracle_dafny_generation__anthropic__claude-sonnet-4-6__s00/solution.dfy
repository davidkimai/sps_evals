method merge_policy(defaults: map<string, string>, override: map<string, string>) returns (result: map<string, string>)
  ensures forall k :: k in override && override[k] != "None" ==> k in result && result[k] == override[k]
  ensures forall k :: k in override && override[k] == "None" ==> k !in result
  ensures forall k :: k in defaults && k !in override ==> k in result && result[k] == defaults[k]
  ensures forall k :: k in result ==> k in defaults || (k in override && override[k] != "None")
{
  result := defaults;
  
  // Apply overrides
  var keys := override.Keys;
  while keys != {}
    invariant keys <= override.Keys
    invariant forall k :: k in result ==> k in defaults || (k in (override.Keys - keys) && override[k] != "None")
    invariant forall k :: k in (override.Keys - keys) && override[k] != "None" ==> k in result && result[k] == override[k]
    invariant forall k :: k in (override.Keys - keys) && override[k] == "None" ==> k !in result
    invariant forall k :: k in defaults && k !in (override.Keys - keys) ==> k in result && result[k] == defaults[k]
  {
    var k :| k in keys;
    keys := keys - {k};
    
    if override[k] == "None" {
      if k in result {
        result := result - {k};
      }
    } else {
      result := result[k := override[k]];
    }
  }
}
