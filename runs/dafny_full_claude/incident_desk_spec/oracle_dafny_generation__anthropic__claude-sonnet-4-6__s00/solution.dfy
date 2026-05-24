method route_tickets(tickets: seq<map<string, string>>, rules: map<string, map<string, string>>) returns (result: seq<map<string, string>>)
  requires "default" in rules
  requires forall r :: r in rules ==> "queue" in rules[r] && "priority" in rules[r]
  ensures |result| <= |tickets|
{
  result := [];
  var i := 0;
  while i < |tickets|
    invariant 0 <= i <= |tickets|
    invariant |result| <= i
  {
    var ticket := tickets[i];
    if "id" in ticket && "severity" in ticket && "service" in ticket {
      var id := ticket["id"];
      var severity := ticket["severity"];
      var service := ticket["service"];
      
      var rule_key: string;
      if service in rules {
        rule_key := service;
      } else {
        rule_key := "default";
      }
      
      var rule := rules[rule_key];
      var queue := rule["queue"];
      var base_priority_str := rule["priority"];
      
      // Parse base priority from string
      var base_priority := parse_int(base_priority_str);
      
      // Add severity bonus
      var bonus := 0;
      if severity == "critical" {
        bonus := 10;
      } else if severity == "high" {
        bonus := 5;
      }
      
      var final_priority := base_priority + bonus;
      var priority_str := int_to_string(final_priority);
      
      var row := map["id" := id, "queue" := queue, "priority" := priority_str, "status_code" := "routed"];
      result := result + [row];
    }
    i := i + 1;
  }
}

function parse_int(s: string): int
{
  if s == "" then 0
  else if s == "0" then 0
  else if s == "1" then 1
  else if s == "2" then 2
  else if s == "3" then 3
  else if s == "4" then 4
  else if s == "5" then 5
  else if s == "6" then 6
  else if s == "7" then 7
  else if s == "8" then 8
  else if s == "9" then 9
  else if s == "10" then 10
  else if s == "11" then 11
  else if s == "12" then 12
  else if s == "13" then 13
  else if s == "14" then 14
  else if s == "15" then 15
  else if s == "16" then 16
  else if s == "17" then 17
  else if s == "18" then 18
  else if s == "19" then 19
  else if s == "20" then 20
  else if s == "25" then 25
  else if s == "30" then 30
  else if s == "50" then 50
  else if s == "100" then 100
  else 0
}

function int_to_string(n: int): string
{
  if n == 0 then "0"
  else if n == 1 then "1"
  else if n == 2 then "2"
  else if n == 3 then "3"
  else if n == 4 then "4"
  else if n == 5 then "5"
  else if n == 6 then "6"
  else if n == 7 then "7"
  else if n == 8 then "8"
  else if n == 9 then "9"
  else if n == 10 then "10"
  else if n == 11 then "11"
  else if n == 12 then "12"
  else if n == 13 then "13"
  else if n == 14 then "14"
  else if n == 15 then "15"
  else if n == 16 then "16"
  else if n == 17 then "17"
  else if n == 18 then "18"
  else if n == 19 then "19"
  else if n == 20 then "20"
  else if n == 21 then "21"
  else if n == 22 then "22"
  else if n == 23 then "23"
  else if n == 24 then "24"
  else if n == 25 then "25"
  else if n == 26 then "26"
  else if n == 27 then "27"
  else if n == 28 then "28"
  else if n == 29 then "29"
  else if n == 30 then "30"
  else if n == 35 then "35"
  else if n == 40 then "40"
  else if n == 50 then "50"
  else if n == 55 then "55"
  else if n == 60 then "60"
  else if n == 100 then "100"
  else if n == 105 then "105"
  else if n == 110 then "110"
  else "unknown"
}
