module TTLCacheModule {

  class TTLCache {
    var max_size: int
    var ttl_seconds: real
    var keys: array<int>
    var values: array<int>
    var timestamps: array<real>
    var count: int
    var now_time: real

    constructor(max_size: int, ttl_seconds: real)
      requires max_size > 0
      requires ttl_seconds > 0.0
      ensures this.max_size == max_size
      ensures this.ttl_seconds == ttl_seconds
      ensures this.count == 0
    {
      this.max_size := max_size;
      this.ttl_seconds := ttl_seconds;
      this.keys := new int[max_size];
      this.values := new int[max_size];
      this.timestamps := new real[max_size];
      this.count := 0;
      this.now_time := 0.0;
    }

    method SetNow(t: real)
      modifies this
    {
      now_time := t;
    }

    method GetCurrentTime() returns (t: real)
    {
      t := now_time;
    }

    method FindKey(key: int) returns (idx: int)
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
          return;
        }
        i := i + 1;
      }
    }

    method EvictExpired()
      modifies this, keys, values, timestamps
      requires 0 <= count <= keys.Length
      ensures 0 <= count <= keys.Length
    {
      var t := now_time;
      var i := 0;
      var new_count := 0;
      var temp_keys := new int[keys.Length];
      var temp_values := new int[values.Length];
      var temp_timestamps := new real[timestamps.Length];
      
      while i < count
        invariant 0 <= i <= count
        invariant 0 <= new_count <= i
        invariant new_count <= keys.Length
      {
        if t - timestamps[i] <= ttl_seconds {
          temp_keys[new_count] := keys[i];
          temp_values[new_count] := values[i];
          temp_timestamps[new_count] := timestamps[i];
          new_count := new_count + 1;
        }
        i := i + 1;
      }
      
      i := 0;
      while i < new_count
        invariant 0 <= i <= new_count
      {
        keys[i] := temp_keys[i];
        values[i] := temp_values[i];
        timestamps[i] := temp_timestamps[i];
        i := i + 1;
      }
      count := new_count;
    }

    method EvictLRU()
      modifies this, keys, values, timestamps
      requires 0 < count <= keys.Length
      ensures count == old(count) - 1
      ensures 0 <= count <= keys.Length
    {
      // Remove the entry at index 0 (least recently used = oldest timestamp)
      // Find minimum timestamp index
      var min_idx := 0;
      var i := 1;
      while i < count
        invariant 1 <= i <= count
        invariant 0 <= min_idx < count
      {
        if timestamps[i] < timestamps[min_idx] {
          min_idx := i;
        }
        i := i + 1;
      }
      
      // Shift elements left from min_idx
      i := min_idx;
      while i < count - 1
        invariant min_idx <= i <= count - 1
      {
        keys[i] := keys[i + 1];
        values[i] := values[i + 1];
        timestamps[i] := timestamps[i + 1];
        i := i + 1;
      }
      count := count - 1;
    }

    method Set(key: int, value: int)
      modifies this, keys, values, timestamps
      requires 0 <= count <= keys.Length
      requires max_size == keys.Length
      ensures 0 <= count <= keys.Length
    {
      var t := now_time;
      
      // Check if key already exists
      var idx := FindKey(key);
      if idx != -1 {
        // Update existing entry and move to end (most recently used)
        values[idx] := value;
        timestamps[idx] := t;
        // Move to end
        var i := idx;
        while i < count - 1
          invariant idx <= i <= count - 1
        {
          keys[i] := keys[i + 1];
          values[i] := values[i + 1];
          timestamps[i] := timestamps[i + 1];
          i := i + 1;
        }
        keys[count - 1] := key;
        values[count - 1] := value;
        timestamps[count - 1] := t;
        return;
      }
      
      // Evict expired entries first
      EvictExpired();
      
      // If still at max capacity, evict LRU
      if count == max_size {
        EvictLRU();
      }
      
      // Add new entry at end
      keys[count] := key;
      values[count] := value;
      timestamps[count] := t;
      count := count + 1;
    }

    method Get(key: int) returns (found: bool, value: int)
      modifies this, timestamps
      requires 0 <= count <= keys.Length
      ensures 0 <= count <= keys.Length
    {
      var t := now_time;
      var idx := FindKey(key);
      
      if idx == -1 {
        found := false;
        value := 0;
        return;
      }
      
      // Check if expired
      if t - timestamps[idx] > ttl_seconds {
        found := false;
        value := 0;
        return;
      }
      
      // Update access time (move to end for LRU)
      value := values[idx];
      timestamps[idx] := t;
      
      // Move to end (most recently used)
      var i := idx;
      while i < count - 1
        invariant idx <= i <= count - 1
      {
        keys[i] := keys[i + 1];
        values[i] := values[i + 1];
        timestamps[i] := timestamps[i + 1];
        i := i + 1;
      }
      keys[count - 1] := key;
      values[count - 1] := value;
      timestamps[count - 1] := t;
      
      found := true;
    }
  }

  method Main()
  {
    var cache := new TTLCache(3, 10.0);
    cache.SetNow(0.0);
    cache.Set(1, 100);
    cache.Set(2, 200);
    cache.Set(3, 300);
    
    var found, val := cache.Get(1);
    assert found;
    
    // Test expiry
    cache.SetNow(15.0);
    found, val := cache.Get(1);
    assert !found;
    
    // Test LRU eviction
    var cache2 := new TTLCache(2, 100.0);
    cache2.SetNow(0.0);
    cache2.Set(1, 10);
    cache2.Set(2, 20);
    cache2.SetNow(1.0);
    found, val := cache2.Get(1); // access key 1, making key 2 LRU
    cache2.SetNow(2.0);
    cache2.Set(3, 30); // should evict key 2
    found, val := cache2.Get(2);
    assert !found;
  }
}
