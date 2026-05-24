class LazySingleton {
  var instance: object?
  var factory: () -> object

  constructor(f: () -> object)
    ensures instance == null
  {
    instance := null;
    factory := f;
  }

  method get() returns (obj: object)
    modifies this
    ensures obj == instance
    ensures old(instance) != null ==> instance == old(instance)
  {
    if instance == null {
      instance := factory();
    }
    obj := instance;
  }
}
