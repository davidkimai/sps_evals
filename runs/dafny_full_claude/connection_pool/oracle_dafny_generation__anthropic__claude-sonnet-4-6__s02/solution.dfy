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
  var idle_pool: array<Connection?>
  var idle_count: int
  var total_count: int
  var current_time: int

  ghost var pool_valid: bool

  constructor(max_size: int, initial_time: int)
    requires max_size > 0
    ensures this.max_size == max_size
    ensures idle_count == 0
    ensures total_count == 0
    ensures current_time == initial_time
  {
    this.max_size := max_size;
    this.idle_pool := new Connection?[max_size];
    this.idle_count := 0;
    this.total_count := 0;
    this.current_time := initial_time;
    this.pool_valid := true;
    var i := 0;
    while i < max_size
      invariant 0 <= i <= max_size
      invariant idle_pool.Length == max_size
    {
      idle_pool[i] := null;
      i := i + 1;
    }
  }

  method SetTime(now: int)
    modifies this
    ensures current_time == now
  {
    current_time := now;
  }

  method Acquire() returns (conn: Connection)
    modifies this, idle_pool
    requires max_size > 0
    requires idle_pool.Length == max_size
    requires 0 <= idle_count <= max_size
    requires 0 <= total_count
    ensures conn != null
    ensures !conn.closed
    ensures 0 <= idle_count <= max_size
  {
    if idle_count > 0 {
      idle_count := idle_count - 1;
      conn := idle_pool[idle_count] as Connection;
      idle_pool[idle_count] := null;
      conn.idle_since := current_time;
    } else {
      conn := new Connection(current_time);
      total_count := total_count + 1;
    }
  }

  method Release(conn: Connection)
    modifies this, idle_pool, conn
    requires conn != null
    requires !conn.closed
    requires idle_pool.Length == max_size
    requires 0 <= idle_count <= max_size
    ensures 0 <= idle_count <= max_size
  {
    if idle_count < max_size {
      conn.idle_since := current_time;
      idle_pool[idle_count] := conn;
      idle_count := idle_count + 1;
    } else {
      conn.Close();
      if total_count > 0 {
        total_count := total_count - 1;
      }
    }
  }

  method EvictIdle(max_idle_seconds: int)
    modifies this, idle_pool
    requires idle_pool.Length == max_size
    requires 0 <= idle_count <= max_size
    requires max_idle_seconds >= 0
    ensures 0 <= idle_count <= max_size
  {
    var new_idle: array<Connection?> := new Connection?[max_size];
    var j := 0;
    var i := 0;
    while i < idle_count
      invariant 0 <= i <= idle_count
      invariant 0 <= j <= i
      invariant j <= max_size
      invariant new_idle.Length == max_size
    {
      var c := idle_pool[i];
      if c != null {
        var idle_time := current_time - c.idle_since;
        if idle_time > max_idle_seconds {
          c.closed := true;
          if total_count > 0 {
            total_count := total_count - 1;
          }
        } else {
          new_idle[j] := c;
          j := j + 1;
        }
      }
      i := i + 1;
    }
    var k := j;
    while k < max_size
      invariant j <= k <= max_size
      invariant new_idle.Length == max_size
    {
      new_idle[k] := null;
      k := k + 1;
    }
    idle_count := j;
    var m := 0;
    while m < max_size
      invariant 0 <= m <= max_size
      invariant idle_pool.Length == max_size
      invariant new_idle.Length == max_size
    {
      idle_pool[m] := new_idle[m];
      m := m + 1;
    }
  }
}

method Main() {
  var pool := new ConnectionPool(3, 0);
  
  var c1 := pool.Acquire();
  assert c1 != null;
  assert !c1.closed;
  
  var c2 := pool.Acquire();
  assert c2 != null;
  assert !c2.closed;
  
  pool.Release(c1);
  pool.Release(c2);
  
  pool.SetTime(100);
  pool.EvictIdle(50);
  
  var c3 := pool.Acquire();
  assert c3 != null;
  assert !c3.closed;
}
