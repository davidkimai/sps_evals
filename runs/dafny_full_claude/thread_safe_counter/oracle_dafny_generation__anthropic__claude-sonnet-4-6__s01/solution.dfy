class BoundedCounter {
  var maxTotal: int
  var counts: map<string, int>
  var totalCount: int

  constructor(max_total: int)
    requires max_total > 0
    ensures maxTotal == max_total
    ensures counts == map[]
    ensures totalCount == 0
  {
    maxTotal := max_total;
    counts := map[];
    totalCount := 0;
  }

  method increment(name: string) returns (newVal: int)
    requires totalCount < maxTotal
    modifies this
    ensures totalCount == old(totalCount) + 1
    ensures totalCount <= maxTotal
    ensures name in counts
    ensures counts[name] == newVal
    ensures newVal >= 1
  {
    if name in counts {
      counts := counts[name := counts[name] + 1];
    } else {
      counts := counts[name := 1];
    }
    totalCount := totalCount + 1;
    newVal := counts[name];
  }

  method total() returns (t: int)
    ensures t == totalCount
  {
    t := totalCount;
  }

  method snapshot() returns (snap: map<string, int>)
    ensures snap == counts
  {
    snap := counts;
  }
}

method Main() {
  var bc := new BoundedCounter(10);
  var v1 := bc.increment("a");
  assert v1 == 1;
  var v2 := bc.increment("a");
  assert v2 == 2;
  var v3 := bc.increment("b");
  assert v3 == 1;
  var t := bc.total();
  assert t == 3;
  var snap := bc.snapshot();
  assert snap["a"] == 2;
  assert snap["b"] == 1;
}
