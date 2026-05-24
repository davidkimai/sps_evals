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

  ghost predicate Valid()
    reads this, set c | c in idle, set c | c in active
  {
    max_size >= 0 &&
    |idle| + |active| <= max_size &&
    (forall c | c in idle :: !c.closed) &&
    (forall c | c in active :: !c.closed)
  }

  constructor(max_size: int)
    requires max_size >= 0
    ensures this.max_size == max_size
    ensures idle == []
    ensures active == []
    ensures Valid()
  {
    this.max_size := max_size;
    this.idle := [];
    this.active := [];
    this.factory := null;
  }

  method acquire(now: int) returns (conn: Connection)
    requires Valid()
    modifies this
    ensures Valid()
    ensures !conn.closed
    ensures conn in active
  {
    if |idle| > 0 {
      conn := idle[0];
      idle := idle[1..];
      active := active + [conn];
    } else {
      conn := new Connection(now);
      active := active + [conn];
    }
  }

  method release(conn: Connection, now: int)
    requires Valid()
    requires conn in active
    modifies this, conn
    ensures Valid()
  {
    // Remove from active
    var idx := find_in_active(conn);
    active := active[..idx] + active[idx+1..];

    if |idle| + |active| < max_size {
      conn.idle_since := now;
      idle := idle + [conn];
    } else {
      conn.Close();
    }
  }

  method find_in_active(conn: Connection) returns (idx: int)
    requires conn in active
    ensures 0 <= idx < |active|
    ensures active[idx] == conn
  {
    idx := 0;
    while idx < |active|
      invariant 0 <= idx <= |active|
      invariant forall k | 0 <= k < idx :: active[k] != conn
    {
      if active[idx] == conn {
        return idx;
      }
      idx := idx + 1;
    }
  }

  method evict_idle(max_idle_seconds: int, now: int)
    requires Valid()
    modifies this, set c | c in idle
    ensures Valid()
  {
    var new_idle: seq<Connection> := [];
    var i := 0;
    while i < |idle|
      invariant 0 <= i <= |idle|
      invariant forall c | c in new_idle :: !c.closed
      invariant |new_idle| + |active| <= max_size
    {
      var conn := idle[i];
      var age := now - conn.idle_since;
      if age > max_idle_seconds {
        conn.Close();
      } else {
        new_idle := new_idle + [conn];
      }
      i := i + 1;
    }
    idle := new_idle;
  }
}

method ConnectionPool_main()
{
  var pool := new ConnectionPool(3);
  var now := 1000;

  var c1 := pool.acquire(now);
  var c2 := pool.acquire(now);

  pool.release(c1, now + 10);
  pool.release(c2, now + 20);

  pool.evict_idle(5, now + 16);

  var c3 := pool.acquire(now + 30);
}
