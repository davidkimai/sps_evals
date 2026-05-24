method flatten_paths(value: map<string, object>) returns (result: map<string, object>)
{
  result := map[];
  var keys := value.Keys;
  var keySeq := SetToSeq(keys);
  var i := 0;
  while i < |keySeq|
    invariant 0 <= i <= |keySeq|
    decreases |keySeq| - i
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
        decreases |subKeySeq| - j
      {
        var sk := subKeySeq[j];
        var newKey := k + "." + sk;
        result := result[newKey := sub[sk]];
        j := j + 1;
      }
    } else {
      result := result[k := v];
    }
    i := i + 1;
  }
}

method SetToSeq<T>(s: set<T>) returns (sq: seq<T>)
  ensures |sq| == |s|
  ensures forall x :: x in s ==> x in sq
  ensures forall x :: x in sq ==> x in s
{
  sq := [];
  var remaining := s;
  while remaining != {}
    invariant forall x :: x in sq ==> x in s
    invariant forall x :: x in remaining ==> x in s
    invariant forall x :: x in s ==> x in sq || x in remaining
    invariant |sq| + |remaining| == |s|
    decreases |remaining|
  {
    var x :| x in remaining;
    sq := sq + [x];
    remaining := remaining - {x};
  }
}
