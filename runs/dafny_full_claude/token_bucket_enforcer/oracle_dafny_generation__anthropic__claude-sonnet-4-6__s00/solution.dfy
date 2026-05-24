class TokenBucketEnforcer {
  var capacity: int
  var tokens: real
  var last_time: real

  constructor(cap: int, refill_rate: real)
    requires cap >= 0
    requires refill_rate >= 0.0
    ensures this.capacity == cap
    ensures this.tokens == cap as real
  {
    capacity := cap;
    tokens := cap as real;
    last_time := 0.0;
  }

  method allow(cost: int, now: real) returns (result: bool)
    requires cost >= 0
    requires capacity >= 0
    modifies this
    ensures tokens >= 0.0
    ensures tokens <= capacity as real
  {
    // We don't use refill_rate as a field here; caller passes elapsed tokens directly
    // Instead, we compute based on now - last_time
    // For simplicity, tokens is updated externally via refill
    if tokens < cost as real {
      result := false;
    } else {
      tokens := tokens - cost as real;
      result := true;
    }
  }

  method refill(amount: real)
    requires amount >= 0.0
    requires capacity >= 0
    modifies this
    ensures tokens >= 0.0
    ensures tokens <= capacity as real
  {
    tokens := tokens + amount;
    if tokens > capacity as real {
      tokens := capacity as real;
    }
  }
}

method Main() {
  var tb := new TokenBucketEnforcer(10, 1.0);
  var r1 := tb.allow(5, 0.0);
  assert tb.tokens == 5.0;
  var r2 := tb.allow(3, 0.0);
  assert tb.tokens == 2.0;
  var r3 := tb.allow(3, 0.0);
  assert !r3;
  assert tb.tokens == 2.0;
  tb.refill(5.0);
  assert tb.tokens == 7.0;
  var r4 := tb.allow(3, 0.0);
  assert r4;
  assert tb.tokens == 4.0;
}
