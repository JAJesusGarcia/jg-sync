use serde::Serialize;
use std::{
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
    thread,
    time::Duration,
};
use tauri::{AppHandle, Emitter, State};

const ENGINE_SNAPSHOT_EVENT: &str = "engine:snapshot";

#[derive(Default)]
struct EngineRuntime {
    running: Arc<AtomicBool>,
}

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct EngineSnapshot {
    bpm: f64,
    confidence: f64,
    audio_level: f64,
    state: String,
    beat_detected: bool,
    connected: bool,
}

#[tauri::command]
fn start_engine_stream(app: AppHandle, runtime: State<'_, EngineRuntime>) -> Result<(), String> {
    if runtime.running.swap(true, Ordering::SeqCst) {
        return Ok(());
    }

    let running = Arc::clone(&runtime.running);

    thread::spawn(move || {
        let mut tick: u64 = 0;

        while running.load(Ordering::SeqCst) {
            let beat_detected = tick % 2 == 0;
            let phase = (tick as f64 * 0.35).sin();

            let snapshot = EngineSnapshot {
                bpm: 128.0 + phase * 0.35,
                confidence: 86.0 + phase * 5.0,
                audio_level: 60.0 + phase * 18.0,
                state: "TRACKING".to_string(),
                beat_detected,
                connected: true,
            };

            if let Err(error) = app.emit(ENGINE_SNAPSHOT_EVENT, snapshot) {
                eprintln!("Failed to emit engine snapshot: {error}");
            }

            tick += 1;
            thread::sleep(Duration::from_millis(460));
        }
    });

    Ok(())
}

#[tauri::command]
fn stop_engine_stream(runtime: State<'_, EngineRuntime>) -> Result<(), String> {
    runtime.running.store(false, Ordering::SeqCst);
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
        .expect("error while running tauri application");
}
