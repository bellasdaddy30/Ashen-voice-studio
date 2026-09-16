use serde_json::{json, Value};
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
const DESIGNER_SOURCE: &str = include_str!("../../voice_designer_worker.py");

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

fn designer_python_path() -> PathBuf {
    if let Ok(v) = env::var("ASHEN_VOICE_DESIGNER_PYTHON") {
        return PathBuf::from(v);
    }
    app_home()
        .join("designer-venv")
        .join("bin")
        .join("python")
}

fn install_embedded_script(name: &str, source: &str) -> Result<PathBuf, String> {
    let dir = app_home();
    fs::create_dir_all(&dir).map_err(|e| format!("Could not create native voice folder: {e}"))?;
    let path = dir.join(name);
    let needs_write = fs::read_to_string(&path)
        .map(|s| s != source)
        .unwrap_or(true);
    if needs_write {
        fs::write(&path, source)
            .map_err(|e| format!("Could not install {name}: {e}"))?;
    }
    Ok(path)
}

fn worker_script_path() -> Result<PathBuf, String> {
    install_embedded_script("native_voice_worker.py", WORKER_SOURCE)
}

fn designer_script_path() -> Result<PathBuf, String> {
    install_embedded_script("voice_designer_worker.py", DESIGNER_SOURCE)
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

#[tauri::command]
fn native_voice_designer_status() -> Value {
    let python = designer_python_path();
    json!({
        "ok": true,
        "available": python.exists(),
        "python": python.to_string_lossy(),
        "model": "parler-tts/parler-tts-tiny-v1"
    })
}

fn run_designer(request: Value) -> Result<Value, String> {
    let python = designer_python_path();
    if !python.exists() {
        return Err(
            "Parler Voice Designer is not installed. Run: bash scripts/install-native-engines.sh --with-designer"
                .into(),
        );
    }
    let script = designer_script_path()?;
    let mut child = Command::new(&python)
        .arg("-u")
        .arg(&script)
        .env("ASHEN_VOICE_HOME", app_home())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Could not start Parler Voice Designer: {e}"))?;

    if let Some(mut stdin) = child.stdin.take() {
        let body = serde_json::to_vec(&request).map_err(|e| e.to_string())?;
        stdin
            .write_all(&body)
            .map_err(|e| format!("Could not send design request: {e}"))?;
    }

    let output = child
        .wait_with_output()
        .map_err(|e| format!("Could not wait for Voice Designer: {e}"))?;
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    let value: Value = serde_json::from_str(stdout.trim()).map_err(|e| {
        format!(
            "Voice Designer returned invalid output: {e}. stderr: {}",
            stderr.trim()
        )
    })?;

    if !output.status.success() && value.get("ok").and_then(Value::as_bool) != Some(false) {
        return Err(format!("Voice Designer failed: {}", stderr.trim()));
    }
    Ok(value)
}

#[tauri::command]
async fn native_voice_design(request: Value) -> Result<Value, String> {
    tauri::async_runtime::spawn_blocking(move || run_designer(request))
        .await
        .map_err(|e| format!("Voice Designer task failed: {e}"))?
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(VoiceState::default())
        .invoke_handler(tauri::generate_handler![
            native_tts,
            reset_native_tts,
            native_voice_designer_status,
            native_voice_design
        ])
        .run(tauri::generate_context!())
        .expect("error while running Ashen Voice Studio");
}
