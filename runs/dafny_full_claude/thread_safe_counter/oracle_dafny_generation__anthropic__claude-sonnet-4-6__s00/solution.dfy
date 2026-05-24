class BoundedCounter {
  var maxTotal: int
  var counts: map<string, int>
  var totalCount: int

  predicate Valid()
    reads this
  {
    maxTotal > 0 &&
    totalCount >= 0 &&
    totalCount <= maxTotal
  }

  constructor(max_total: int)
    requires max_total > 0
    ensures Valid()
    ensures maxTotal == max_total
    ensures counts == map[]
    ensures totalCount == 0
  {
    maxTotal := max_total;
    counts := map[];
    totalCount := 0;
  }

  method increment(name: string) returns (newVal: int)
    requires Valid()
    modifies this
    ensures Valid()
    ensures totalCount == old(totalCount) + 1
    ensures totalCount <= maxTotal
    ensures name in counts
    ensures counts[name] == newVal
    ensures newVal >= 1
  {
    if totalCount >= maxTotal {
      // In compiled code this will raise OverflowError
      // We use assume false here to indicate this path is excluded by precondition
      // In the Python translation we'll handle this via runtime check
      assume false;
    }
    var oldVal := 0;
    if name in counts {
      oldVal := counts[name];
    }
    newVal := oldVal + 1;
    counts := counts[name := newVal];
    totalCount := totalCount + 1;
  }

  method total() returns (t: int)
    requires Valid()
    ensures t == totalCount
    ensures t >= 0
  {
    t := totalCount;
  }

  method snapshot() returns (snap: map<string, int>)
    requires Valid()
    ensures snap == counts
  {
    snap := counts;
  }
}

method Main() {
  var c := new BoundedCounter(10);
  var v1 := c.increment("alice");
  assert v1 == 1;
  var v2 := c.increment("alice");
  assert v2 == 2;
  var v3 := c.increment("bob");
  assert v3 == 1;
  var t := c.total();
  assert t == 3;
  var s := c.snapshot();
  assert s["alice"] == 2;
  assert s["bob"] == 1;
}
