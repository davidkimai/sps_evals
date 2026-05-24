class AsyncRateLimiter {
  var rate: int
  var windowStart: real
  var count: int
  var nowFn: int -> real

  ghost var valid: bool

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
    windowStart := 0.0;
    count := 0;
    nowFn := (x: int) => 0.0;
    valid := true;
  }

  method acquire(currentTime: real) returns (result: bool)
    requires Valid()
    modifies this
    ensures Valid()
    ensures result ==> old(count) < old(rate)
  {
    if currentTime - windowStart >= 1.0 {
      windowStart := currentTime;
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
  var limiter := new AsyncRateLimiter(5);
  assert limiter.Valid();
  
  var r1 := limiter.acquire(0.0);
  assert r1;
  
  var r2 := limiter.acquire(0.1);
  assert r2;
  
  var r3 := limiter.acquire(0.2);
  assert r3;
  
  var r4 := limiter.acquire(0.3);
  assert r4;
  
  var r5 := limiter.acquire(0.4);
  assert r5;
  
  var r6 := limiter.acquire(0.5);
  assert !r6;
  
  var r7 := limiter.acquire(1.1);
  assert r7;
}
