// Orquestrador Tauri v2 (DAS seção 3 / ERSW RN1).
//
// Responsabilidades:
// - Escolher uma porta livre em loopback e repassá-la ao Sidecar Python via
//   argumento de linha de comando (--port).
// - Instanciar o Sidecar usando tauri_plugin_shell::ShellExt no arranque.
// - Garantir o encerramento (kill) do processo Python quando a janela
//   principal ("main") for fechada, evitando processos órfãos.

use std::net::TcpListener;
use std::sync::Mutex;

use tauri::{Manager, RunEvent};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

struct SidecarState(Mutex<Option<CommandChild>>);

/// Encontra uma porta TCP livre no loopback, evitando conflitos com outros
/// softwares (DAS seção 4).
fn pick_free_port() -> u16 {
    TcpListener::bind("127.0.0.1:0")
        .expect("Não foi possível reservar uma porta de loopback")
        .local_addr()
        .expect("Endereço local inválido")
        .port()
}

#[tauri::command]
fn get_backend_port(state: tauri::State<BackendPort>) -> u16 {
    state.0
}

struct BackendPort(u16);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let port = pick_free_port();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(SidecarState(Mutex::new(None)))
        .manage(BackendPort(port))
        .invoke_handler(tauri::generate_handler![get_backend_port])
        .setup(move |app| {
            let shell = app.shell();
            
            let (mut rx, child) = shell
                .sidecar("app-backend")
                .expect("Falha ao localizar o binário sidecar")
                .args(["--port", &port.to_string()])
                .spawn()
                .expect("Falha ao iniciar o Sidecar Python");

            // --- NOVO BLOCO: Imprime os logs do Python no terminal do Tauri ---
            tauri::async_runtime::spawn(async move {
                use tauri_plugin_shell::process::CommandEvent;
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => println!("[PYTHON] {}", String::from_utf8_lossy(&line)),
                        CommandEvent::Stderr(line) => eprintln!("[PYTHON ERR] {}", String::from_utf8_lossy(&line)),
                        CommandEvent::Terminated(payload) => println!("[PYTHON] Backend encerrou sozinho com código: {:?}", payload.code),
                        _ => {}
                    }
                }
            });
            // ------------------------------------------------------------------

            let state = app.state::<SidecarState>();
            *state.0.lock().unwrap() = Some(child);

            log::info!("Sidecar iniciado na porta {port}");
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("erro ao construir a aplicação Tauri")
        .run(|app_handle, event| {
            // RN1 do ERSW: ao fechar a janela principal, o processo Rust deve
            // emitir o sinal de encerramento para o binário Python.
            if let RunEvent::WindowEvent {
                label,
                event: tauri::WindowEvent::CloseRequested { .. },
                ..
            } = &event
            {
                if label == "main" {
                    let state = app_handle.state::<SidecarState>();

                    // Pegamos o valor e o MutexGuard já é descartado no ponto e vírgula
                    let child_process = state.0.lock().unwrap().take(); 

                    if let Some(child) = child_process {
                        let _ = child.kill();
                    }
                }
            }

            if let RunEvent::Exit = &event {
                let state = app_handle.state::<SidecarState>();
                // Pegamos o valor e o MutexGuard já é descartado no ponto e vírgula
                let child_process = state.0.lock().unwrap().take(); 

                if let Some(child) = child_process {
                    let _ = child.kill();
                }
            }
        });
}
