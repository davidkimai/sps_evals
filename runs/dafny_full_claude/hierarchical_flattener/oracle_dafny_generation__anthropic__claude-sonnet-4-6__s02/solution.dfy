method flatten_paths(value: map<string, object>) returns (result: map<string, object>)
{
  result := map[];
  var keys := value.Keys;
  var keySeq := SetToSeq(keys);
  var i := 0;
  while i < |keySeq|
    invariant 0 <= i <= |keySeq|
  {
    var k := keySeq[i];
    var v := value[k];
    if v is map<string, object> {
      var nested := v as map<string, object>;
      var sub := flatten_paths(nested);
      var subKeys := sub.Keys;
      var subKeySeq := SetToSeq(subKeys);
      var j := 0;
      while j < |subKeySeq|
        invariant 0 <= j <= |subKeySeq|
      {
        var sk := subKeySeq[j];
        var sv := sub[sk];
        result := result[k + "." + sk := sv];
        j := j + 1;
      }
    } else {
      result := result[k := v];
    }
    i := i + 1;
  }
}

method SetToSeq(s: set<string>) returns (sq: seq<string>)
  ensures multiset(sq) == multiset(s)
{
  sq := [];
  var remaining := s;
  while remaining != {}
    invariant multiset(sq) + multiset(remaining) == multiset(s)
    decreases remaining
  {
    var x :| x in remaining;
    sq := sq + [x];
    remaining := remaining - {x};
  }
}
