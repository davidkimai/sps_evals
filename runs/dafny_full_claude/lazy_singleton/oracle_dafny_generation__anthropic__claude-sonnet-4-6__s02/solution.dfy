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
    ensures instance != null
  {
    if instance == null {
      instance := factory();
    }
    obj := instance;
  }
}
