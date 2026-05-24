class AsyncRateLimiter {
  var rate: int
  var count: int
  var windowStart: real

  predicate Valid()
    reads this
  {
    rate > 0 && count >= 0 && count <= rate
  }

  constructor(r: int)
    requires r > 0
    ensures rate == r
    ensures count == 0
    ensures Valid()
  {
    rate := r;
    count := 0;
    windowStart := 0.0;
  }

  method acquire(now: real) returns (result: bool)
    requires Valid()
    requires now >= 0.0
    modifies this
    ensures Valid()
    ensures result ==> count >= 1
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

  method reset(now: real)
    requires Valid()
    requires now >= 0.0
    modifies this
    ensures Valid()
    ensures count == 0
    ensures windowStart == now
  {
    windowStart := now;
    count := 0;
  }
}

method TestRateLimiter()
{
  var limiter := new AsyncRateLimiter(2);
  assert limiter.rate == 2;
  assert limiter.count == 0;

  var r1 := limiter.acquire(0.0);
  assert r1;
  assert limiter.count == 1;

  var r2 := limiter.acquire(0.5);
  assert r2;
  assert limiter.count == 2;

  var r3 := limiter.acquire(0.9);
  assert !r3;
  assert limiter.count == 2;

  var r4 := limiter.acquire(1.1);
  assert r4;
  assert limiter.count == 1;
}

method ValidateRate(r: int) returns (valid: bool)
  ensures valid <==> r > 0
{
  valid := r > 0;
}
