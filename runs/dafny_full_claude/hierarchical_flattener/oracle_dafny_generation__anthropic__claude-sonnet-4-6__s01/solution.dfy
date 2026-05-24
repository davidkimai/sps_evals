method flatten_paths(value: map<string, object>) returns (result: map<string, object>)
{
  result := map[];
  var keys := value.Keys;
  while keys != {}
    decreases keys
  {
    var key :| key in keys;
    keys := keys - {key};
    var val := value[key];
    if val is map<string, object> {
      var nested := val as map<string, object>;
      var sub := flatten_paths(nested);
      var subKeys := sub.Keys;
      while subKeys != {}
        decreases subKeys
      {
        var subKey :| subKey in subKeys;
        subKeys := subKeys - {subKey};
        var newKey := key + "." + subKey;
        result := result[newKey := sub[subKey]];
      }
    } else {
      result := result[key := val];
    }
  }
}
