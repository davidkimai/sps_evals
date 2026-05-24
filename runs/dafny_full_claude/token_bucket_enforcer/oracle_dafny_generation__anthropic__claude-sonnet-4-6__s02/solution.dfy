class TokenBucketEnforcer {
  var capacity: int
  var tokens: real
  var lastTime: real

  constructor(cap: int, refill_rate: real)
    requires cap >= 0
    requires refill_rate >= 0.0
    ensures this.capacity == cap
    ensures this.tokens == cap as real
    ensures this.lastTime == 0.0
  {
    capacity := cap;
    tokens := cap as real;
    lastTime := 0.0;
  }

  method allow(cost: int, now: real) returns (result: bool)
    requires cost >= 0
    requires now >= 0.0
    modifies this
    ensures tokens >= 0.0
    ensures tokens <= capacity as real
  {
    // We store refill_rate as a field would be needed, but for simplicity
    // we handle it differently - actually we need refill_rate stored
    result := false;
    if cost as real <= tokens {
      tokens := tokens - cost as real;
      result := true;
    }
  }
}

class TokenBucket {
  var capacity: int
  var refillRate: real
  var tokens: real
  var lastTime: real

  constructor(cap: int, rate: real)
    requires cap >= 0
    requires rate >= 0.0
    ensures capacity == cap
    ensures refillRate == rate
    ensures tokens == cap as real
    ensures lastTime == 0.0
  {
    capacity := cap;
    refillRate := rate;
    tokens := cap as real;
    lastTime := 0.0;
  }

  method refill(now: real)
    requires now >= 0.0
    modifies this
    ensures tokens >= 0.0
    ensures tokens <= capacity as real
    ensures lastTime == (if now > lastTime then now else lastTime)
  {
    if now > lastTime {
      var elapsed := now - lastTime;
      var added := elapsed * refillRate;
      tokens := tokens + added;
      if tokens > capacity as real {
        tokens := capacity as real;
      }
      lastTime := now;
    }
  }

  method allow(cost: int, now: real) returns (result: bool)
    requires cost >= 0
    requires now >= 0.0
    modifies this
    ensures tokens >= 0.0
    ensures tokens <= capacity as real
  {
    refill(now);
    if cost as real <= tokens {
      tokens := tokens - cost as real;
      result := true;
    } else {
      result := false;
    }
  }
}

method TokenBucketEnforcer(capacity: int, refillRate: real) returns (bucket: TokenBucket)
  requires capacity >= 0
  requires refillRate >= 0.0
  ensures bucket.capacity == capacity
  ensures bucket.refillRate == refillRate
  ensures bucket.tokens == capacity as real
  ensures bucket.lastTime == 0.0
{
  bucket := new TokenBucket(capacity, refillRate);
}

method Main() {
  var b := new TokenBucket(10, 1.0);
  var r1 := b.allow(3, 0.0);
  assert r1 == true;
  var r2 := b.allow(5, 1.0);
  assert r2 == true;
  var r3 := b.allow(20, 2.0);
  // tokens after r2: 10-3-5+1=3, after refill at t=2: 3+1=4, cost=20 > 4, so false
  assert r3 == false;
}
