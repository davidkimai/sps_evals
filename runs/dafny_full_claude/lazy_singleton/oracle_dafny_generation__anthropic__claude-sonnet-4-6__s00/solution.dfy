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
    ensures instance != null
    ensures obj == instance
  {
    if instance == null {
      instance := factory();
    }
    obj := instance;
  }
}
