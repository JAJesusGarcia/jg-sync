use serde::{Deserialize, Serialize};
use std::{
    io::{BufRead, BufReader},
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
    thread,
};
use tauri::{AppHandle, Emitter, State};

const ENGINE_SNAPSHOT_EVENT: &str = "engine:snapshot";
const ENGINE_ERROR_EVENT: &str = "engine:error";

struct EngineRuntime {
    running: Arc<AtomicBool>,
    child: Arc<Mutex<Option<Child>>>,
}

impl Default for EngineRuntime {
    fn default() -> Self {
        Self {
            running: Arc::new(AtomicBool::new(false)),
            child: Arc::new(Mutex::new(None)),
        }
    }
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
struct EngineSnapshot {
    bpm: f64,
    confidence: f64,
    audio_level: f64,
    state: String,
    beat_detected: bool,
    connected: bool,
    timestamp: f64,
}

#[derive(Debug, Clone, Serialize)]
struct EngineError {
    message: String,
}

#[derive(Debug, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
enum EngineMessage {
    Snapshot {
        bpm: f64,
        confidence: f64,

        #[serde(rename = "audioLevel")]
        audio_level: f64,

        state: String,

        #[serde(rename = "beatDetected")]
        beat_detected: bool,

        connected: bool,
        timestamp: f64,
    },
    Error {
        code: String,
        message: String,
        timestamp: f64,
    },
}

fn emit_engine_error(app: &AppHandle, message: impl Into<String>) {
    let error = EngineError {
        message: message.into(),
    };

    if let Err(emit_error) = app.emit(ENGINE_ERROR_EVENT, error) {
        eprintln!("Failed to emit engine error event: {emit_error}");
    }
}

fn project_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap_or_else(|_| Path::new(env!("CARGO_MANIFEST_DIR")).join("../.."))
}

fn python_executable(root: &Path) -> PathBuf {
    #[cfg(target_os = "windows")]
    {
        root.join(".venv").join("Scripts").join("python.exe")
    }

    #[cfg(not(target_os = "windows"))]
    {
        root.join(".venv").join("bin").join("python")
    }
}

fn handle_engine_message(app: &AppHandle, line: &str) {
    let message = match serde_json::from_str::<EngineMessage>(line) {
        Ok(message) => message,
        Err(error) => {
            emit_engine_error(app, format!("Invalid JSON received from Python: {error}"));
            return;
        }
    };

    match message {
        EngineMessage::Snapshot {
            bpm,
            confidence,
            audio_level,
            state,
            beat_detected,
            connected,
            timestamp,
        } => {
            let snapshot = EngineSnapshot {
                bpm,
                confidence,
                audio_level,
                state,
                beat_detected,
                connected,
                timestamp,
            };

            if let Err(error) = app.emit(ENGINE_SNAPSHOT_EVENT, snapshot) {
                emit_engine_error(app, format!("Failed to emit engine snapshot: {error}"));
            }
        }

        EngineMessage::Error {
            code,
            message,
            timestamp,
        } => {
            emit_engine_error(app, format!("[{code}] {message} ({timestamp})"));
        }
    }
}

#[tauri::command]
fn start_engine_stream(app: AppHandle, runtime: State<'_, EngineRuntime>) -> Result<(), String> {
    if runtime.running.swap(true, Ordering::SeqCst) {
        return Ok(());
    }

    let root = project_root();
    let python = python_executable(&root);
    let script = root.join("scripts").join("engine_runtime.py");

    if !python.exists() {
        runtime.running.store(false, Ordering::SeqCst);

        return Err(format!("Python executable not found: {}", python.display()));
    }

    if !script.exists() {
        runtime.running.store(false, Ordering::SeqCst);

        return Err(format!(
            "Engine runtime script not found: {}",
            script.display()
        ));
    }

    let mut child = Command::new(&python)
        .arg("-u")
        .arg(&script)
        .current_dir(&root)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|error| {
            runtime.running.store(false, Ordering::SeqCst);

            format!("Failed to start Python engine: {error}")
        })?;

    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| "Failed to capture Python stdout".to_string())?;

    let stderr = child
        .stderr
        .take()
        .ok_or_else(|| "Failed to capture Python stderr".to_string())?;

    {
        let mut child_slot = runtime
            .child
            .lock()
            .map_err(|_| "Engine child lock was poisoned".to_string())?;

        *child_slot = Some(child);
    }

    let stdout_app = app.clone();
    let stdout_running = Arc::clone(&runtime.running);

    thread::spawn(move || {
        let reader = BufReader::new(stdout);

        for line_result in reader.lines() {
            if !stdout_running.load(Ordering::SeqCst) {
                break;
            }

            match line_result {
                Ok(line) => {
                    let trimmed = line.trim();

                    if !trimmed.is_empty() {
                        handle_engine_message(&stdout_app, trimmed);
                    }
                }

                Err(error) => {
                    emit_engine_error(
                        &stdout_app,
                        format!("Failed reading Python stdout: {error}"),
                    );
                    break;
                }
            }
        }

        stdout_running.store(false, Ordering::SeqCst);
    });

    let stderr_app = app;
    let stderr_running = Arc::clone(&runtime.running);

    thread::spawn(move || {
        let reader = BufReader::new(stderr);

        for line_result in reader.lines() {
            if !stderr_running.load(Ordering::SeqCst) {
                break;
            }

            match line_result {
                Ok(line) => {
                    let trimmed = line.trim();

                    if trimmed.is_empty() {
                        continue;
                    }

                    match serde_json::from_str::<EngineMessage>(trimmed) {
                        Ok(EngineMessage::Error {
                            code,
                            message,
                            timestamp,
                        }) => {
                            emit_engine_error(
                                &stderr_app,
                                format!("[{code}] {message} ({timestamp})"),
                            );
                        }

                        _ => {
                            emit_engine_error(&stderr_app, format!("Python stderr: {trimmed}"));
                        }
                    }
                }

                Err(error) => {
                    emit_engine_error(
                        &stderr_app,
                        format!("Failed reading Python stderr: {error}"),
                    );
                    break;
                }
            }
        }
    });

    Ok(())
}

#[tauri::command]
fn stop_engine_stream(runtime: State<'_, EngineRuntime>) -> Result<(), String> {
    runtime.running.store(false, Ordering::SeqCst);

    let mut child_slot = runtime
        .child
        .lock()
        .map_err(|_| "Engine child lock was poisoned".to_string())?;

    if let Some(mut child) = child_slot.take() {
        child
            .kill()
            .map_err(|error| format!("Failed to stop Python engine: {error}"))?;

        child
            .wait()
            .map_err(|error| format!("Failed waiting for Python engine: {error}"))?;
    }

    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(EngineRuntime::default())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            start_engine_stream,
            stop_engine_stream
        ])
        .run(tauri::generate_context!())
        .expect("error while running Tauri application");
}
