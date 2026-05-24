class TokenBucketEnforcer {
  var capacity: int
  var tokens: int

  constructor(capacity: int, refill_rate: real)
    requires capacity >= 0
    ensures this.capacity == capacity
    ensures this.tokens == capacity
  {
    this.capacity := capacity;
    this.tokens := capacity;
  }

  method allow(cost: int) returns (result: bool)
    requires cost >= 0
    requires tokens >= 0
    requires tokens <= capacity
    modifies this
    ensures tokens >= 0
    ensures tokens <= capacity
    ensures result ==> tokens == old(tokens) - cost
    ensures !result ==> tokens == old(tokens)
  {
    if cost <= tokens {
      tokens := tokens - cost;
      result := true;
    } else {
      result := false;
    }
  }

  method refill(amount: int)
    requires amount >= 0
    requires tokens >= 0
    requires tokens <= capacity
    modifies this
    ensures tokens >= 0
    ensures tokens <= capacity
  {
    var newTokens := tokens + amount;
    if newTokens > capacity {
      tokens := capacity;
    } else {
      tokens := newTokens;
    }
  }
}
