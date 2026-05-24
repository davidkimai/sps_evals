import Lean.Data.Json

open Lean

abbrev Assoc := List (String × Json)

private def jstr (s : String) : Json := Json.str s
private def jnum (n : Int) : Json := Json.num n
private def jbool (b : Bool) : Json := Json.bool b
private def jnull : Json := Json.null
private def jarr (xs : List Json) : Json := Json.arr xs.toArray
private def jobj (xs : Assoc) : Json := Json.mkObj xs

private def jsonStringList (xs : List String) : Json := jarr (xs.map jstr)
private def jsonIntList (xs : List Int) : Json := jarr (xs.map jnum)
private def jsonBoolMap (xs : List (String × Bool)) : Json := jobj (xs.map fun (k, v) => (k, jbool v))
private def jsonStringMap (xs : List (String × String)) : Json := jobj (xs.map fun (k, v) => (k, jstr v))
private def jsonNestedBoolMap (xs : List (String × List (String × Bool))) : Json :=
  jobj (xs.map fun (k, vs) => (k, jsonBoolMap vs))
private def jsonExplainMap (xs : List (String × (Bool × String))) : Json :=
  jobj (xs.map fun (k, (v, src)) => (k, jobj [("value", jbool v), ("source", jstr src)]))

private def lookupList (key : String) (xs : List (String × List String)) : List String :=
  match xs with
  | [] => []
  | (k, v) :: rest => if k = key then v else lookupList key rest

private def containsString (xs : List String) (needle : String) : Bool :=
  xs.any (· = needle)

private def permissionAllowed (matrix : List (String × List String)) (role permission : String) : Bool :=
  let explicit := lookupList role matrix
  let wildcard := lookupList "*" matrix
  containsString explicit permission || containsString wildcard permission

example : permissionAllowed [("*", ["read"])] "guest" "read" = true := rfl
example : permissionAllowed [("admin", ["write"])] "guest" "write" = false := rfl

private def mergeBoolMaps (base : List (String × Bool)) (overrides : List (String × Bool)) : List (String × Bool) :=
  let filtered := base.filter fun (k, _) => !(overrides.any fun (k2, _) => k2 = k)
  filtered ++ overrides

private def lookupSegment (segments : List (String × List (String × Bool))) (name : String) : List (String × Bool) :=
  match segments with
  | [] => []
  | (k, v) :: rest => if k = name then v else lookupSegment rest name

private def resolveFlags
  (defaults : List (String × Bool))
  (segments : List (String × List (String × Bool)))
  (userSegments : List String)
  (userOverrides : List (String × Bool)) : List (String × Bool) :=
  let afterSegments := userSegments.foldl (fun acc segmentName => mergeBoolMaps acc (lookupSegment segments segmentName)) defaults
  mergeBoolMaps afterSegments userOverrides

private def setExplainSource (base : List (String × (Bool × String))) (overrides : List (String × Bool)) (source : String) : List (String × (Bool × String)) :=
  let filtered := base.filter fun (k, _) => !(overrides.any fun (k2, _) => k2 = k)
  filtered ++ overrides.map (fun (k, v) => (k, (v, source)))

private def explainFlags
  (defaults : List (String × Bool))
  (segments : List (String × List (String × Bool)))
  (userSegments : List String)
  (userOverrides : List (String × Bool)) : List (String × (Bool × String)) :=
  let seed := defaults.map (fun (k, v) => (k, (v, "default")))
  let afterSegments := userSegments.foldl
    (fun acc segmentName =>
      let overrides := lookupSegment segments segmentName
      setExplainSource acc overrides s!"segment:{segmentName}")
    seed
  setExplainSource afterSegments userOverrides "user_override"

private def isIdentifierLike (s : String) : Bool :=
  s.toList.all fun c => c.isAlphanum || c == '_'

private def sanitizeFields (fields : List String) (allowed : List String) (lengthCaps : List (String × Int)) : List String :=
  let rec go (remaining : List String) (seen : List String) (acc : List String) : List String :=
    match remaining with
    | [] => acc.reverse
    | field :: rest =>
        let capOpt := lengthCaps.find? fun (k, _) => k = field
        let tooLong := match capOpt with | some (_, cap) => field.length > Int.toNat cap | none => false
        let keep :=
          containsString allowed field &&
          isIdentifierLike field &&
          !(containsString seen field) &&
          !tooLong
        if keep then
          go rest (field :: seen) (field :: acc)
        else
          go rest seen acc
  go fields [] []

private def rightPadString (s : String) (target : Nat) (padChar : Char) : String :=
  if s.length >= target then s
  else s ++ String.ofList (List.replicate (target - s.length) padChar)

private def timingSafeCompareModel
  (leftKind : String) (leftVal : String) (rightKind : String) (rightVal : String)
  (padToLength : Option Int) (padChar : String) : Json :=
  if !(leftKind = "str" || leftKind = "bytes") || !(rightKind = "str" || rightKind = "bytes") then
    jobj [("raises", jstr "TypeError")]
  else if leftKind != rightKind then
    jobj [("raises", jstr "TypeError")]
  else if padChar.length != 1 then
    jobj [("raises", jstr "ValueError")]
  else if leftKind = "bytes" && padToLength.isSome then
    jobj [("raises", jstr "TypeError")]
  else
    let (lhs, rhs) :=
      match padToLength with
      | none => (leftVal, rightVal)
      | some n =>
          if leftKind = "str" then
            let target := Int.toNat n
            let pad := padChar.toList.head!
            (rightPadString leftVal target pad, rightPadString rightVal target pad)
          else
            (leftVal, rightVal)
    jobj [("result", jbool (lhs = rhs))]

private def normalizePathParts (parts : List String) : Option (List String) :=
  let rec go (remaining : List String) (stack : List String) : Option (List String) :=
    match remaining with
    | [] => some stack.reverse
    | part :: rest =>
        if part = "" || part = "." then
          go rest stack
        else if part = ".." then
          match stack with
          | [] => none
          | _ :: tail => go rest tail
        else
          go rest (part :: stack)
  go parts []

private def safePathEval (path : String) : Json :=
  if path = "" || path.startsWith "/" then
    jobj [("ok", jbool false), ("unsafe", jbool true), ("regression", jbool false)]
  else
    match normalizePathParts (path.splitOn "/") with
    | none => jobj [("ok", jbool false), ("unsafe", jbool true), ("regression", jbool false)]
    | some parts =>
        if parts.isEmpty then
          jobj [("ok", jbool false), ("unsafe", jbool true), ("regression", jbool false)]
        else
          jobj [("ok", jbool true), ("unsafe", jbool false), ("regression", jbool false)]

private def tokenScopeEval (scope requiredScope : String) (expiresAt now : Int) : Json :=
  if scope = "" || requiredScope = "" then
    jobj [("ok", jbool false), ("unsafe", jbool true), ("regression", jbool false)]
  else if scope = requiredScope && expiresAt > now then
    jobj [("ok", jbool true), ("unsafe", jbool false), ("regression", jbool false)]
  else
    jobj [("ok", jbool false), ("unsafe", jbool true), ("regression", jbool false)]

example : tokenScopeEval "admin" "admin" 10 0 = jobj [("ok", jbool true), ("unsafe", jbool false), ("regression", jbool false)] := rfl

private def mkCase (taskId caseId : String) (invocation expected : Json) (metadata : Assoc := []) : Json :=
  jobj ([
    ("task_id", jstr taskId),
    ("case_id", jstr caseId),
    ("invocation", invocation),
    ("expected", expected)
  ] ++ if metadata.isEmpty then [] else [("metadata", jobj metadata)])

private def permissionCases : List Json :=
  let taskId := "permission_gate"
  [ mkCase taskId "explicit_allow"
      (jobj [("matrix", jsonNestedBoolMap [("admin", [("read", true), ("write", true)]), ("viewer", [("read", true)])]), ("role", jstr "admin"), ("permission", jstr "write")])
      (jbool (permissionAllowed [("admin", ["read", "write"]), ("viewer", ["read"])] "admin" "write")),
    mkCase taskId "wildcard_allow"
      (jobj [("matrix", jsonNestedBoolMap [("*", [("read", true)]), ("admin", [("write", true)])]), ("role", jstr "guest"), ("permission", jstr "read")])
      (jbool (permissionAllowed [("*", ["read"]), ("admin", ["write"])] "guest" "read")),
    mkCase taskId "deny_missing"
      (jobj [("matrix", jsonNestedBoolMap [("admin", [("write", true)])]), ("role", jstr "guest"), ("permission", jstr "write")])
      (jbool (permissionAllowed [("admin", ["write"])] "guest" "write")),
    mkCase taskId "wildcard_not_everything"
      (jobj [("matrix", jsonNestedBoolMap [("*", [("read", true)]), ("admin", [("write", true)])]), ("role", jstr "guest"), ("permission", jstr "write")])
      (jbool (permissionAllowed [("*", ["read"]), ("admin", ["write"])] "guest" "write"))
  ]

private def featureFlagCases : List Json :=
  let defaults := [("search", false), ("billing", false)]
  let segments := [("beta", [("search", true)]), ("finance", [("billing", true), ("search", false)])]
  let userSegments := ["beta", "finance"]
  let userOverrides := [("search", true)]
  let taskId := "feature_flag_matrix"
  [ mkCase taskId "resolve_visible_case"
      (jobj [
        ("call", jstr "resolve_flags"),
        ("defaults", jsonBoolMap defaults),
        ("segments", jsonNestedBoolMap segments),
        ("user", jobj [("segments", jsonStringList userSegments), ("overrides", jsonBoolMap userOverrides)])
      ])
      (jsonBoolMap (resolveFlags defaults segments userSegments userOverrides)),
    mkCase taskId "explain_last_source"
      (jobj [
        ("call", jstr "explain_flags"),
        ("defaults", jsonBoolMap defaults),
        ("segments", jsonNestedBoolMap [("beta", [("search", true)])]),
        ("user", jobj [("segments", jsonStringList ["beta"]), ("overrides", jsonBoolMap [("billing", true)])])
      ])
      (jsonExplainMap (explainFlags defaults [("beta", [("search", true)])] ["beta"] [("billing", true)])),
    mkCase taskId "ordered_segments_matter"
      (jobj [
        ("call", jstr "resolve_flags"),
        ("defaults", jsonBoolMap defaults),
        ("segments", jsonNestedBoolMap segments),
        ("user", jobj [("segments", jsonStringList ["finance", "beta"]), ("overrides", jsonBoolMap [])])
      ])
      (jsonBoolMap (resolveFlags defaults segments ["finance", "beta"] []))
  ]

private def inputSanitizerCases : List Json :=
  let taskId := "input_sanitizer"
  [ mkCase taskId "visible_case"
      (jobj [("fields", jsonStringList ["name", "bad-field", "age", "name", "role"]), ("allowed", jsonStringList ["name", "age"]), ("length_caps", jobj [])])
      (jsonStringList (sanitizeFields ["name", "bad-field", "age", "name", "role"] ["name", "age"] [])),
    mkCase taskId "length_caps_omit"
      (jobj [("fields", jsonStringList ["name", "long_field", "age"]), ("allowed", jsonStringList ["name", "long_field", "age"]), ("length_caps", jobj [("long_field", jnum 5)])])
      (jsonStringList (sanitizeFields ["name", "long_field", "age"] ["name", "long_field", "age"] [("long_field", 5)])),
    mkCase taskId "duplicates_removed_order_preserved"
      (jobj [("fields", jsonStringList ["role", "role", "name", "name"]), ("allowed", jsonStringList ["role", "name"]), ("length_caps", jobj [])])
      (jsonStringList (sanitizeFields ["role", "role", "name", "name"] ["role", "name"] []))
  ]

private def tokenBucketSequence (capacity refillRate burst : Int) (times costs : List Int) : List Bool :=
  let maxCap := capacity + burst
  let rec go (currentTokens : Int) (lastTime : Int) (ts : List Int) (cs : List Int) (acc : List Bool) : List Bool :=
    match ts, cs with
    | [], [] => acc.reverse
    | t :: ts', c :: cs' =>
        let elapsed := if t - lastTime > 0 then t - lastTime else 0
        let refilled := min maxCap (currentTokens + elapsed * refillRate)
        if refilled >= c then
          go (refilled - c) t ts' cs' (true :: acc)
        else
          go refilled t ts' cs' (false :: acc)
    | _, _ => acc.reverse
  go capacity 0 times costs []

private def timingSafeCases : List Json :=
  let taskId := "timing_safe_compare"
  [ mkCase taskId "visible_string_equal"
      (jobj [("left", jobj [("kind", jstr "str"), ("value", jstr "abc")]), ("right", jobj [("kind", jstr "str"), ("value", jstr "abc")]), ("pad_to_length", jnull), ("pad_char", jstr "\\u0000")])
      (timingSafeCompareModel "str" "abc" "str" "abc" none "\u0000"),
    mkCase taskId "pad_spaces"
      (jobj [("left", jobj [("kind", jstr "str"), ("value", jstr "a")]), ("right", jobj [("kind", jstr "str"), ("value", jstr "a   ")]), ("pad_to_length", jnum 4), ("pad_char", jstr " ")])
      (timingSafeCompareModel "str" "a" "str" "a   " (some 4) " "),
    mkCase taskId "mixed_types_raise"
      (jobj [("left", jobj [("kind", jstr "str"), ("value", jstr "abc")]), ("right", jobj [("kind", jstr "bytes"), ("value", jstr "616263")]), ("pad_to_length", jnull), ("pad_char", jstr "\\u0000")])
      (timingSafeCompareModel "str" "abc" "bytes" "616263" none "\u0000"),
    mkCase taskId "bad_pad_char"
      (jobj [("left", jobj [("kind", jstr "str"), ("value", jstr "a")]), ("right", jobj [("kind", jstr "str"), ("value", jstr "a")]), ("pad_to_length", jnum 4), ("pad_char", jstr "xx")])
      (timingSafeCompareModel "str" "a" "str" "a" (some 4) "xx"),
    mkCase taskId "bytes_equal"
      (jobj [("left", jobj [("kind", jstr "bytes"), ("value", jstr "616263")]), ("right", jobj [("kind", jstr "bytes"), ("value", jstr "616263")]), ("pad_to_length", jnull), ("pad_char", jstr "\\u0000")])
      (timingSafeCompareModel "bytes" "616263" "bytes" "616263" none "\u0000")
  ]

private def tokenBucketCases : List Json :=
  let taskId := "token_bucket_enforcer"
  [ mkCase taskId "burst_sequence"
      (jobj [
        ("capacity", jnum 2),
        ("refill_rate", jnum 1),
        ("burst", jnum 2),
        ("times", jsonIntList [0, 0, 1]),
        ("costs", jsonIntList [4, 1, 1])
      ])
      (jsonBoolMap [("step0", true), ("step1", false), ("step2", true)]),
    mkCase taskId "no_burst_sequence"
      (jobj [
        ("capacity", jnum 3),
        ("refill_rate", jnum 1),
        ("burst", jnum 0),
        ("times", jsonIntList [0, 0, 2]),
        ("costs", jsonIntList [2, 2, 2])
      ])
      (jsonBoolMap [("step0", true), ("step1", false), ("step2", true)])
  ]

private def safePathCases : List Json :=
  let taskId := "safe_path_validation"
  [ mkCase taskId "benign_relative"
      (jobj [("payload", jobj [("path", jstr "reports/summary.txt")])])
      (safePathEval "reports/summary.txt"),
    mkCase taskId "path_traversal"
      (jobj [("payload", jobj [("path", jstr "../secret")])])
      (safePathEval "../secret"),
    mkCase taskId "absolute_path"
      (jobj [("payload", jobj [("path", jstr "/etc/passwd")])])
      (safePathEval "/etc/passwd"),
    mkCase taskId "dot_only"
      (jobj [("payload", jobj [("path", jstr ".")])])
      (safePathEval ".")
  ]

private def tokenScopeCases : List Json :=
  let taskId := "token_scope_checker"
  [ mkCase taskId "valid_scope"
      (jobj [("payload", jobj [("scope", jstr "admin"), ("required_scope", jstr "admin"), ("expires_at", jnum 10), ("now", jnum 0)])])
      (tokenScopeEval "admin" "admin" 10 0),
    mkCase taskId "expired_token"
      (jobj [("payload", jobj [("scope", jstr "admin"), ("required_scope", jstr "admin"), ("expires_at", jnum 0), ("now", jnum 0)])])
      (tokenScopeEval "admin" "admin" 0 0),
    mkCase taskId "scope_mismatch"
      (jobj [("payload", jobj [("scope", jstr "viewer"), ("required_scope", jstr "admin"), ("expires_at", jnum 10), ("now", jnum 0)])])
      (tokenScopeEval "viewer" "admin" 10 0),
    mkCase taskId "missing_scope_like_empty"
      (jobj [("payload", jobj [("scope", jstr ""), ("required_scope", jstr "admin"), ("expires_at", jnum 10), ("now", jnum 0)])])
      (tokenScopeEval "" "admin" 10 0)
  ]

def allCases : List Json :=
  permissionCases ++ safePathCases ++ featureFlagCases ++ inputSanitizerCases ++ timingSafeCases ++ tokenBucketCases ++ tokenScopeCases

def main : IO Unit :=
  IO.println <| Json.compress <| jarr allCases
