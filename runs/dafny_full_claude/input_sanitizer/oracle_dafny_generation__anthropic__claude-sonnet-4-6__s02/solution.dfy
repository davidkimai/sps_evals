method sanitize_fields(fields: seq<string>, allowed: set<string>) returns (result: seq<string>)
  ensures forall s :: s in result ==> s in allowed
  ensures forall i, j :: 0 <= i < j < |result| ==> result[i] != result[j]
{
  result := [];
  var seen: set<string> := {};
  
  var i := 0;
  while i < |fields|
    invariant 0 <= i <= |fields|
    invariant forall s :: s in result ==> s in allowed
    invariant forall x, y :: 0 <= x < y < |result| ==> result[x] != result[y]
    invariant forall s :: s in seen <==> s in result
  {
    var field := fields[i];
    if field in allowed && field !in seen && IsValidField(field) {
      result := result + [field];
      seen := seen + {field};
    }
    i := i + 1;
  }
}

function IsValidField(s: string): bool
{
  forall c :: c in s ==> IsValidChar(c)
}

function IsValidChar(c: char): bool
{
  ('a' <= c <= 'z') || ('A' <= c <= 'Z') || ('0' <= c <= '9') || c == '_'
}
