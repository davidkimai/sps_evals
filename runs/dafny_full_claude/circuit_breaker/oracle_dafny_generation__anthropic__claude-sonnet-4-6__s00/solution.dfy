module CircuitBreakerModule {

  datatype State = Closed | Open | HalfOpen

  class CircuitBreaker {
    var state: State
    var failure_count: int
    var failure_threshold: int
    var recovery_timeout: real
    var last_failure_time: real

    constructor(threshold: int, timeout: real)
      requires threshold >= 0
      requires timeout >= 0.0
      ensures state == Closed
      ensures failure_count == 0
      ensures failure_threshold == threshold
      ensures recovery_timeout == timeout
    {
      state := Closed;
      failure_count := 0;
      failure_threshold := threshold;
      recovery_timeout := timeout;
      last_failure_time := 0.0;
    }

    method RecordSuccess()
      modifies this
      ensures state == Closed
      ensures failure_count == 0
    {
      state := Closed;
      failure_count := 0;
    }

    method RecordFailure(current_time: real)
      modifies this
      requires failure_threshold >= 0
    {
      failure_count := failure_count + 1;
      if failure_count >= failure_threshold {
        state := Open;
        last_failure_time := current_time;
      }
    }

    method TryCall(current_time: real) returns (allowed: bool)
      modifies this
      requires recovery_timeout >= 0.0
    {
      if state == Closed {
        allowed := true;
      } else if state == Open {
        if current_time - last_failure_time >= recovery_timeout {
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

    method HandleResult(success: bool, current_time: real)
      modifies this
      requires failure_threshold >= 0
      requires recovery_timeout >= 0.0
    {
      if success {
        RecordSuccess();
      } else {
        if state == HalfOpen {
          state := Open;
          last_failure_time := current_time;
        } else {
          RecordFailure(current_time);
        }
      }
    }

    method GetState() returns (s: State)
    {
      s := state;
    }

    method GetFailureCount() returns (c: int)
    {
      c := failure_count;
    }
  }

}
