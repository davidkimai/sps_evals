class AsyncRateLimiter {
  var rate: int
  var count: int
  var windowStart: real

  constructor(r: int)
    requires r > 0
    ensures this.rate == r
    ensures this.count == 0
  {
    rate := r;
    count := 0;
    windowStart := 0.0;
  }

  method acquire(now: real) returns (result: bool)
    requires rate > 0
    modifies this
    ensures result ==> count <= rate
  {
    if now - windowStart >= 1.0 {
      windowStart := now;
      count := 0;
    }
    if count < rate {
      count := count + 1;
      result := true;
    } else {
      result := false;
    }
  }
}

method Main() {
  var limiter := new AsyncRateLimiter(2);
  var r1 := limiter.acquire(0.0);
  assert r1 == true;
  var r2 := limiter.acquire(0.1);
  assert r2 == true;
  var r3 := limiter.acquire(0.2);
  assert r3 == false;
  var r4 := limiter.acquire(1.0);
  assert r4 == true;
}
