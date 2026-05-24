method TTLCache(max_size: int, ttl_seconds: real) returns (cache: object)
  requires max_size > 0
  requires ttl_seconds > 0.0
{
  cache := new TTLCacheImpl(max_size, ttl_seconds);
}

class TTLCacheImpl {
  var max_size: int
  var ttl_seconds: real
  var keys: array<int>
  var values: array<int>
  var timestamps: array<real>
  var count: int
  var current_time: real

  constructor(ms: int, ttl: real)
    requires ms > 0
    requires ttl > 0.0
    ensures max_size == ms
    ensures ttl_seconds == ttl
    ensures count == 0
    ensures current_time == 0.0
  {
    max_size := ms;
    ttl_seconds := ttl;
    keys := new int[ms];
    values := new int[ms];
    timestamps := new real[ms];
    count := 0;
    current_time := 0.0;
  }

  method advance_time(delta: real)
    requires delta >= 0.0
    modifies this
  {
    current_time := current_time + delta;
  }

  method set_time(t: real)
    modifies this
  {
    current_time := t;
  }

  method find_key(key: int) returns (idx: int)
    requires 0 <= count <= keys.Length
    reads this, keys
    ensures idx == -1 || (0 <= idx < count && keys[idx] == key)
  {
    idx := -1;
    var i := 0;
    while i < count
      invariant 0 <= i <= count
      invariant idx == -1 || (0 <= idx < count && keys[idx] == key)
    {
      if keys[i] == key {
        idx := i;
        break;
      }
      i := i + 1;
    }
  }

  method remove_at(pos: int)
    requires 0 <= pos < count
    requires count <= keys.Length
    requires count <= values.Length
    requires count <= timestamps.Length
    modifies this, keys, values, timestamps
    ensures count == old(count) - 1
  {
    var i := pos;
    while i < count - 1
      invariant pos <= i <= count - 1
      invariant keys.Length == old(keys.Length)
      invariant values.Length == old(values.Length)
      invariant timestamps.Length == old(timestamps.Length)
    {
      keys[i] := keys[i + 1];
      values[i] := values[i + 1];
      timestamps[i] := timestamps[i + 1];
      i := i + 1;
    }
    count := count - 1;
  }

  method set(key: int, value: int)
    requires 0 < max_size
    requires max_size <= keys.Length
    requires max_size <= values.Length
    requires max_size <= timestamps.Length
    requires 0 <= count <= max_size
    modifies this, keys, values, timestamps
    ensures 0 <= count <= max_size
  {
    // Check if key already exists, remove it (LRU: move to end)
    var idx := find_key(key);
    if idx != -1 {
      remove_at(idx);
    }

    // If at capacity, remove the least recently used (front)
    if count == max_size {
      remove_at(0);
    }

    // Add to end
    keys[count] := key;
    values[count] := value;
    timestamps[count] := current_time;
    count := count + 1;
  }

  method get(key: int) returns (result: int, found: bool)
    requires 0 <= count <= keys.Length
    requires count <= values.Length
    requires count <= timestamps.Length
    modifies this, keys, values, timestamps
    ensures 0 <= count <= old(count)
  {
    var idx := find_key(key);
    if idx == -1 {
      result := 0;
      found := false;
      return;
    }

    // Check TTL
    var age := current_time - timestamps[idx];
    if age > ttl_seconds {
      // Expired, remove it
      remove_at(idx);
      result := 0;
      found := false;
      return;
    }

    // Found and valid - move to end (most recently used)
    var val := values[idx];
    var ts := timestamps[idx];
    remove_at(idx);
    
    // Re-add at end with updated position (keep original timestamp for TTL)
    keys[count] := key;
    values[count] := val;
    timestamps[count] := ts;
    count := count + 1;

    result := val;
    found := true;
  }
}

method Main() {
  var cache := new TTLCacheImpl(3, 10.0);
  
  cache.set(1, 100);
  cache.set(2, 200);
  cache.set(3, 300);
  
  var v1, f1 := cache.get(1);
  assert f1 == true;
  
  // Advance time past TTL
  cache.set_time(15.0);
  var v2, f2 := cache.get(1);
  assert f2 == false;
  
  // Test LRU eviction
  var cache2 := new TTLCacheImpl(2, 100.0);
  cache2.set(1, 10);
  cache2.set(2, 20);
  cache2.set(3, 30); // Should evict key 1
  var v3, f3 := cache2.get(1);
  assert f3 == false; // evicted
  var v4, f4 := cache2.get(2);
  assert f4 == true;
}
