method merge_policy(defaults: map<string, string>, override: map<string, string>) returns (result: map<string, string>)
  ensures forall k :: k in override && override[k] != "None" ==> k in result && result[k] == override[k]
  ensures forall k :: k in override && override[k] == "None" ==> k !in result
  ensures forall k :: k in defaults && k !in override ==> k in result && result[k] == defaults[k]
  ensures forall k :: k in result ==> (k in override && override[k] != "None") || (k in defaults && k !in override)
{
  result := defaults;
  
  // Apply overrides
  var overrideKeys := override.Keys;
  while overrideKeys != {}
    invariant overrideKeys <= override.Keys
    invariant forall k :: k in (override.Keys - overrideKeys) && override[k] != "None" ==> k in result && result[k] == override[k]
    invariant forall k :: k in (override.Keys - overrideKeys) && override[k] == "None" ==> k !in result
    invariant forall k :: k in defaults && k !in override ==> k in result && result[k] == defaults[k]
    invariant forall k :: k in result ==> 
      (k in override && k !in overrideKeys && override[k] != "None") || 
      (k in defaults && (k !in override || k in overrideKeys))
  {
    var k :| k in overrideKeys;
    overrideKeys := overrideKeys - {k};
    
    if override[k] == "None" {
      if k in result {
        result := result - {k};
      }
    } else {
      result := result[k := override[k]];
    }
  }
}
