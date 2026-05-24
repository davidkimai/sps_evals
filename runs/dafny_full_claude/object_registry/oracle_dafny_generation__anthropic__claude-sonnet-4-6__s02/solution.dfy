module ObjectRegistry {

  class Registry {
    var data: map<string, object?>

    constructor()
      ensures data == map[]
    {
      data := map[];
    }

    method register(key: string, obj: object)
      modifies this
      ensures data == old(data)[key := obj]
    {
      data := data[key := obj];
    }

    method get(key: string) returns (result: object?)
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
      // In Dafny's model, all references are live; no-op cleanup
      // In the compiled Python, weak references handle actual GC
    }
  }
}
