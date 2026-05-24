method TTLCache(max_size: int, ttl_seconds: real) returns (cache: TTLCacheObj)
  requires max_size > 0
  requires ttl_seconds > 0.0
{
  cache := new TTLCacheObj(max_size, ttl_seconds);
}

class TTLCacheObj {
  var max_size: int
  var ttl_seconds: real
  var keys: array<int>
  var values: array<int>
  var timestamps: array<real>
  var size: int
  var current_time: real

  constructor(ms: int, ttl: real)
    requires ms > 0
    requires ttl > 0.0
    ensures max_size == ms
    ensures ttl_seconds == ttl
    ensures size == 0
    ensures current_time == 0.0
  {
    max_size := ms;
    ttl_seconds := ttl;
    keys := new int[ms];
    values := new int[ms];
    timestamps := new real[ms];
    size := 0;
    current_time := 0.0;
  }

  method tick(t: real)
    modifies this
    ensures current_time == t
  {
    current_time := t;
  }

  method findKey(key: int) returns (idx: int)
    requires 0 <= size <= keys.Length
    reads this, keys
    ensures idx == -1 || (0 <= idx < size && keys[idx] == key)
  {
    idx := -1;
    var i := 0;
    while i < size
      invariant 0 <= i <= size
      invariant idx == -1 || (0 <= idx < size && keys[idx] == key)
    {
      if keys[i] == key {
        idx := i;
        return;
      }
      i := i + 1;
    }
  }

  method removeAt(pos: int)
    requires 0 <= pos < size
    requires size <= keys.Length
    requires size <= values.Length
    requires size <= timestamps.Length
    modifies this, keys, values, timestamps
    ensures size == old(size) - 1
  {
    var i := pos;
    while i < size - 1
      invariant pos <= i <= size - 1
      invariant keys.Length == old(keys.Length)
      invariant values.Length == old(values.Length)
      invariant timestamps.Length == old(timestamps.Length)
    {
      keys[i] := keys[i + 1];
      values[i] := values[i + 1];
      timestamps[i] := timestamps[i + 1];
      i := i + 1;
    }
    size := size - 1;
  }

  method set(key: int, value: int)
    requires 0 < max_size
    requires max_size <= keys.Length
    requires max_size <= values.Length
    requires max_size <= timestamps.Length
    requires 0 <= size <= max_size
    modifies this, keys, values, timestamps
    ensures 0 <= size <= max_size
  {
    // Check if key already exists, remove it (LRU: move to end)
    var idx := findKey(key);
    if idx != -1 {
      removeAt(idx);
    }
    
    // If at capacity, remove LRU (first element)
    if size == max_size {
      removeAt(0);
    }
    
    // Add to end
    keys[size] := key;
    values[size] := value;
    timestamps[size] := current_time;
    size := size + 1;
  }

  method get(key: int) returns (result: int, found: bool)
    requires 0 < max_size
    requires max_size <= keys.Length
    requires max_size <= values.Length
    requires max_size <= timestamps.Length
    requires 0 <= size <= max_size
    modifies this, keys, values, timestamps
    ensures 0 <= size <= max_size
  {
    var idx := findKey(key);
    if idx == -1 {
      result := 0;
      found := false;
      return;
    }
    
    // Check TTL
    var age := current_time - timestamps[idx];
    if age > ttl_seconds {
      // Expired, remove it
      removeAt(idx);
      result := 0;
      found := false;
      return;
    }
    
    // Found and valid - move to end (LRU update)
    var v := values[idx];
    var t := timestamps[idx];
    removeAt(idx);
    
    keys[size] := key;
    values[size] := v;
    timestamps[size] := t;
    size := size + 1;
    
    result := v;
    found := true;
  }
}
