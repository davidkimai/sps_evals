class BoundedCounter {
  var counts: map<string, int>
  var maxTotal: int
  var currentTotal: int

  constructor(max_total: int)
    requires max_total > 0
    ensures maxTotal == max_total
    ensures counts == map[]
    ensures currentTotal == 0
  {
    maxTotal := max_total;
    counts := map[];
    currentTotal := 0;
  }

  method increment(name: string) returns (newVal: int)
    requires currentTotal < maxTotal
    modifies this
    ensures currentTotal == old(currentTotal) + 1
    ensures currentTotal <= maxTotal
    ensures name in counts
    ensures newVal == counts[name]
    ensures newVal >= 1
  {
    if name in counts {
      counts := counts[name := counts[name] + 1];
    } else {
      counts := counts[name := 1];
    }
    currentTotal := currentTotal + 1;
    newVal := counts[name];
  }

  method total() returns (t: int)
    ensures t == currentTotal
  {
    t := currentTotal;
  }

  method snapshot() returns (snap: map<string, int>)
    ensures snap == counts
  {
    snap := counts;
  }
}

method Main() {
  var c := new BoundedCounter(10);
  var v1 := c.increment("a");
  assert v1 == 1;
  var v2 := c.increment("a");
  assert v2 == 2;
  var v3 := c.increment("b");
  assert v3 == 1;
  var t := c.total();
  assert t == 3;
  var s := c.snapshot();
  assert "a" in s;
  assert "b" in s;
}
