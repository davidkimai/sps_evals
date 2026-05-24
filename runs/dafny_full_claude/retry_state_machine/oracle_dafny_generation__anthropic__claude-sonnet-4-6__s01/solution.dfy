class RetryGate {
  var max_attempts: int
  var failures: int

  constructor(max_att: int)
    requires max_att > 0
    ensures max_attempts == max_att
    ensures failures == 0
  {
    max_attempts := max_att;
    failures := 0;
  }

  method allow() returns (result: bool)
    requires failures >= 0
    requires max_attempts > 0
    ensures result == (failures < max_attempts)
  {
    result := failures < max_attempts;
  }

  method record_success()
    requires failures >= 0
    ensures failures == 0
  {
    failures := 0;
  }

  method record_failure()
    requires failures >= 0
    ensures failures == old(failures) + 1
  {
    failures := failures + 1;
  }

  method remaining() returns (result: int)
    requires failures >= 0
    requires max_attempts > 0
    ensures result == max_attempts - failures
  {
    result := max_attempts - failures;
  }
}

method Main() {
  var gate := new RetryGate(3);
  var a := gate.allow();
  assert a == true;
  gate.record_failure();
  gate.record_failure();
  gate.record_failure();
  var b := gate.allow();
  assert b == false;
  gate.record_success();
  var c := gate.allow();
  assert c == true;
  var r := gate.remaining();
  assert r == 3;
}
