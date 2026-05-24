module ObjectRegistry {

  class Registry {
    var data: map<int, object?>

    constructor()
      ensures data == map[]
    {
      data := map[];
    }

    method register(key: int, obj: object)
      modifies this
      ensures data == old(data)[key := obj]
    {
      data := data[key := obj];
    }

    method get(key: int) returns (result: object?)
      ensures key in data ==> result == data[key]
      ensures key !in data ==> result == null
    {
      if key in data {
        result := data[key];
      } else {
        result := null;
      }
    }

    method cleanup()
      modifies this
    {
      // In Dafny/compiled context, we remove null entries
      var newData: map<int, object?> := map[];
      var keys := data.Keys;
      while keys != {}
        decreases |keys|
      {
        var k :| k in keys;
        keys := keys - {k};
        if data[k] != null {
          newData := newData[k := data[k]];
        }
      }
      data := newData;
    }
  }

}

method ObjectRegistry() returns (r: ObjectRegistry.Registry)
  ensures r.data == map[]
{
  r := new ObjectRegistry.Registry();
}
