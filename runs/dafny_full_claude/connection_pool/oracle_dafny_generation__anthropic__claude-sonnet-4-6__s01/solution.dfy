class Connection {
  var closed: bool
  var idle_since: int

  constructor(now: int)
    ensures !closed
    ensures idle_since == now
  {
    closed := false;
    idle_since := now;
  }

  method Close()
    modifies this
    ensures closed
  {
    closed := true;
  }
}

class ConnectionPool {
  var max_size: int
  var idle: seq<Connection>
  var active: seq<Connection>
  var factory: object?
  var current_time: int

  predicate Valid()
    reads this, set c | c in idle, set c | c in active
  {
    max_size >= 0 &&
    |idle| + |active| <= max_size &&
    (forall c :: c in idle ==> !c.closed) &&
    (forall c :: c in active ==> !c.closed)
  }

  constructor(max_size_param: int, now: int)
    requires max_size_param >= 0
    ensures max_size == max_size_param
    ensures idle == []
    ensures active == []
    ensures current_time == now
    ensures Valid()
  {
    max_size := max_size_param;
    idle := [];
    active := [];
    factory := null;
    current_time := now;
  }

  method SetTime(now: int)
    modifies this
    requires Valid()
    ensures Valid()
    ensures current_time == now
    ensures idle == old(idle)
    ensures active == old(active)
    ensures max_size == old(max_size)
  {
    current_time := now;
  }

  method acquire() returns (conn: Connection)
    modifies this
    requires Valid()
    requires |idle| + |active| < max_size || |idle| > 0
    ensures Valid()
    ensures !conn.closed
    ensures conn in active
  {
    if |idle| > 0 {
      conn := idle[0];
      idle := idle[1..];
      active := active + [conn];
    } else {
      conn := new Connection(current_time);
      active := active + [conn];
    }
  }

  method release(conn: Connection)
    modifies this, conn
    requires Valid()
    requires conn in active
    requires !conn.closed
    ensures Valid()
  {
    // Remove from active
    var idx := 0;
    while idx < |active| && active[idx] != conn
      invariant 0 <= idx <= |active|
    {
      idx := idx + 1;
    }
    if idx < |active| {
      active := active[..idx] + active[idx+1..];
    }
    conn.idle_since := current_time;
    if |idle| + |active| < max_size {
      idle := idle + [conn];
    } else {
      conn.Close();
    }
  }

  method evict_idle(max_idle_seconds: int)
    modifies this, set c | c in idle
    requires Valid()
    requires max_idle_seconds >= 0
    ensures Valid()
    ensures |active| == old(|active|)
  {
    var new_idle: seq<Connection> := [];
    var i := 0;
    while i < |idle|
      invariant 0 <= i <= |idle|
      invariant forall c :: c in new_idle ==> !c.closed
      invariant |new_idle| <= i
    {
      var conn := idle[i];
      var age := current_time - conn.idle_since;
      if age > max_idle_seconds {
        conn.Close();
      } else {
        new_idle := new_idle + [conn];
      }
      i := i + 1;
    }
    idle := new_idle;
  }

  method size() returns (s: int)
    reads this
    requires Valid()
    ensures s == |idle| + |active|
  {
    s := |idle| + |active|;
  }

  method idle_count() returns (s: int)
    reads this
    requires Valid()
    ensures s == |idle|
  {
    s := |idle|;
  }

  method active_count() returns (s: int)
    reads this
    requires Valid()
    ensures s == |active|
  {
    s := |active|;
  }
}
