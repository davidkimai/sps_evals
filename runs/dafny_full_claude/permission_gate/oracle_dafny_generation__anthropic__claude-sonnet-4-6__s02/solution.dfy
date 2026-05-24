method has_permission(matrix: map<string, set<string>>, role: string, permission: string) returns (result: bool)
  ensures result == (role in matrix && permission in matrix[role])
{
  if role in matrix {
    var perms := matrix[role];
    if permission in perms {
      result := true;
    } else {
      result := false;
    }
  } else {
    result := false;
  }
}
