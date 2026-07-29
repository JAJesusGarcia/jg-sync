use std::process::Command;

#[tauri::command]
fn check_python_engine() -> Result<String, String> {
    let output = Command::new("python")
        .arg("--version")
        .output()
        .map_err(|error| format!("Failed to start Python: {error}"))?;

    if !output.status.success() {
        return Err(format!(
            "Python exited with status: {}",
            output.status
        ));
    }

    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();

    let version = if !stdout.is_empty() { stdout } else { stderr };

    Ok(version)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![check_python_engine])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}