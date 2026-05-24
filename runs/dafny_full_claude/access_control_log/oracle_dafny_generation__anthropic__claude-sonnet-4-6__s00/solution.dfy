method check_access(role: string, permission: string, matrix: map<string, set<string>>, log: seq<map<string, string>>) returns (allowed: bool, newLog: seq<map<string, string>>)
  ensures |newLog| == |log| + 1
{
  // Deny by default
  allowed := false;
  
  // Check if role exists in matrix and has the permission
  if role in matrix {
    var perms := matrix[role];
    if permission in perms {
      allowed := true;
    }
  }
  
  // Log the attempt
  var allowedStr := if allowed then "true" else "false";
  var entry := map["role" := role, "permission" := permission, "allowed" := allowedStr];
  newLog := log + [entry];
}
