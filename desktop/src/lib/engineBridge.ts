import { invoke } from "@tauri-apps/api/core";

export async function checkPythonEngine(): Promise<string> {
  return invoke<string>("check_python_engine");
}