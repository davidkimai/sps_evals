module CircuitBreakerModule {

  datatype State = Closed | Open | HalfOpen

  class CircuitBreaker {
    var state: State
    var failureCount: int
    var failureThreshold: int
    var recoveryTimeout: real
    var lastFailureTime: real

    constructor(failure_threshold: int, recovery_timeout: real)
      requires failure_threshold >= 0
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
      requires failureThreshold >= 0
    {
      failureCount := failureCount + 1;
      if failureCount >= failureThreshold {
        state := Open;
        lastFailureTime := currentTime;
      }
    }

    method IsAvailable(currentTime: real) returns (available: bool)
      modifies this
      requires recoveryTimeout >= 0.0
    {
      if state == Closed {
        available := true;
      } else if state == HalfOpen {
        available := true;
      } else {
        // state == Open
        if currentTime - lastFailureTime >= recoveryTimeout {
          state := HalfOpen;
          available := true;
        } else {
          available := false;
        }
      }
    }

    method GetState() returns (s: State)
    {
      s := state;
    }

    method TransitionToOpen(currentTime: real)
      modifies this
      ensures state == Open
    {
      state := Open;
      lastFailureTime := currentTime;
    }
  }
}
