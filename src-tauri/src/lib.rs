use serde_json::Value;
use std::{
    env,
    fs,
    io::{BufRead, BufReader, Write},
    path::PathBuf,
    process::{Child, ChildStdin, ChildStdout, Command, Stdio},
    sync::Mutex,
};
use tauri::State;

const WORKER_SOURCE: &str = include_str!("../../native_voice_worker.py");

struct VoiceWorker {
    child: Child,
    stdin: ChildStdin,
    stdout: BufReader<ChildStdout>,
}

#[derive(Default)]
struct VoiceState(Mutex<Option<VoiceWorker>>);

fn app_home() -> PathBuf {
    if let Ok(v) = env::var("ASHEN_VOICE_HOME") {
        return PathBuf::from(v);
    }
    let home = env::var("HOME").unwrap_or_else(|_| ".".into());
    PathBuf::from(home)
        .join(".local")
        .join("share")
        .join("ashen-voice-studio")
}

fn python_path() -> PathBuf {
    if let Ok(v) = env::var("ASHEN_VOICE_PYTHON") {
        return PathBuf::from(v);
    }
    let candidate = app_home().join("venv").join("bin").join("python");
    if candidate.exists() {
        candidate
    } else {
        PathBuf::from("python3")
    }
}

fn worker_script_path() -> Result<PathBuf, String> {
    let dir = app_home();
    fs::create_dir_all(&dir).map_err(|e| format!("Could not create native voice folder: {e}"))?;
    let path = dir.join("native_voice_worker.py");
    let needs_write = fs::read_to_string(&path)
        .map(|s| s != WORKER_SOURCE)
        .unwrap_or(true);
    if needs_write {
        fs::write(&path, WORKER_SOURCE)
            .map_err(|e| format!("Could not install native voice worker: {e}"))?;
    }
    Ok(path)
}

fn start_worker() -> Result<VoiceWorker, String> {
    let python = python_path();
    let script = worker_script_path()?;
    let mut child = Command::new(&python)
        .arg("-u")
        .arg(&script)
        .env("ASHEN_VOICE_HOME", app_home())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit())
        .spawn()
        .map_err(|e| {
            format!(
                "Could not start the native voice worker with {}: {e}. Run scripts/install-native-engines.sh first.",
                python.display()
            )
        })?;

    let stdin = child
        .stdin
        .take()
        .ok_or_else(|| "Native voice worker stdin was unavailable".to_string())?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| "Native voice worker stdout was unavailable".to_string())?;

    Ok(VoiceWorker {
        child,
        stdin,
        stdout: BufReader::new(stdout),
    })
}

fn call_worker(worker: &mut VoiceWorker, request: &Value) -> Result<Value, String> {
    let line = serde_json::to_string(request).map_err(|e| e.to_string())?;
    writeln!(worker.stdin, "{line}")
        .and_then(|_| worker.stdin.flush())
        .map_err(|e| format!("Could not send request to native voice worker: {e}"))?;

    let mut response = String::new();
    let n = worker
        .stdout
        .read_line(&mut response)
        .map_err(|e| format!("Could not read native voice worker response: {e}"))?;
    if n == 0 {
        return Err("Native voice worker exited unexpectedly".into());
    }
    serde_json::from_str(response.trim())
        .map_err(|e| format!("Native voice worker returned invalid JSON: {e}"))
}

#[tauri::command]
fn native_tts(request: Value, state: State<'_, VoiceState>) -> Result<Value, String> {
    let mut guard = state
        .0
        .lock()
        .map_err(|_| "Native voice worker lock was poisoned".to_string())?;

    if guard.is_none() {
        *guard = Some(start_worker()?);
    }

    let first = call_worker(guard.as_mut().unwrap(), &request);
    match first {
        Ok(v) => Ok(v),
        Err(first_err) => {
            // One automatic restart covers a worker that crashed while a model was loading.
            if let Some(mut old) = guard.take() {
                let _ = old.child.kill();
                let _ = old.child.wait();
            }
            let mut fresh = start_worker()?;
            let second = call_worker(&mut fresh, &request)
                .map_err(|e| format!("{first_err}; retry also failed: {e}"))?;
            *guard = Some(fresh);
            Ok(second)
        }
    }
}

#[tauri::command]
fn reset_native_tts(state: State<'_, VoiceState>) -> Result<(), String> {
    let mut guard = state
        .0
        .lock()
        .map_err(|_| "Native voice worker lock was poisoned".to_string())?;
    if let Some(mut worker) = guard.take() {
        let _ = worker.child.kill();
        let _ = worker.child.wait();
    }
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(VoiceState::default())
        .invoke_handler(tauri::generate_handler![native_tts, reset_native_tts])
        .run(tauri::generate_context!())
        .expect("error while running Ashen Voice Studio");
}
