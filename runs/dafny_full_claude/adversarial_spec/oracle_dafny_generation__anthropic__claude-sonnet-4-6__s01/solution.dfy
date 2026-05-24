method transition_state(state: string, event: string) returns (result: string)
{
  if state == "idle" && event == "start" {
    result := "running";
  } else if state == "running" && event == "stop" {
    result := "idle";
  } else if state == "running" && event == "fail" {
    result := "failed";
  } else if state == "failed" && event == "reset" {
    result := "idle";
  } else {
    result := state;
  }
}
