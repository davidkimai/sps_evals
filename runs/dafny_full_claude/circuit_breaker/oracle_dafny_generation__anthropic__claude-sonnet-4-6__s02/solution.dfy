module CircuitBreakerModule {

  datatype State = Closed | Open | HalfOpen

  class CircuitBreaker {
    var state: State
    var failureCount: int
    var failureThreshold: int
    var recoveryTimeout: real
    var lastFailureTime: real

    constructor(failure_threshold: int, recovery_timeout: real)
      requires failure_threshold > 0
      requires recovery_timeout >= 0.0
      ensures state == Closed
      ensures failureCount == 0
      ensures failureThreshold == failure_threshold
      ensures recoveryTimeout == recovery_timeout
    {
      state := Closed;
      failureCount := 0;
      failureThreshold := failure_threshold;
      recoveryTimeout := recovery_timeout;
      lastFailureTime := 0.0;
    }

    method RecordSuccess()
      modifies this
      ensures state == Closed
      ensures failureCount == 0
    {
      state := Closed;
      failureCount := 0;
    }

    method RecordFailure(currentTime: real)
      modifies this
      requires failureThreshold > 0
    {
      failureCount := failureCount + 1;
      if failureCount >= failureThreshold {
        state := Open;
        lastFailureTime := currentTime;
      }
    }

    method CanAttempt(currentTime: real) returns (allowed: bool)
      modifies this
    {
      if state == Closed {
        allowed := true;
      } else if state == Open {
        if currentTime - lastFailureTime >= recoveryTimeout {
          state := HalfOpen;
          allowed := true;
        } else {
          allowed := false;
        }
      } else {
        // HalfOpen
        allowed := true;
      }
    }

    method GetState() returns (s: State)
    {
      s := state;
    }
  }
}
