use eframe::{egui, App};
use std::io::{BufRead, BufReader};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Mutex};
use std::thread;

const CHAT_LOG_MAX_LINES: usize = 100;

#[derive(Default)]
struct GuiState {
    chat_log: Vec<String>,
    stats: String,
    llm_output: String,
}

struct MyApp {
    state: Arc<Mutex<GuiState>>,
}

impl App for MyApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        let state = self.state.lock().unwrap();

        // Top heading
        egui::TopBottomPanel::top("top_panel").show(ctx, |ui| {
            ui.heading("📊 Twitch Bot Dashboard");
        });

        // Central panel with 3 vertical sections
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.horizontal(|ui| {
                // Left: Twitch Chat
                ui.vertical(|ui| {
                    ui.group(|ui| {
                        ui.label("💬 Twitch Chat");
                        egui::ScrollArea::vertical().show(ui, |ui| {
                            for msg in &state.chat_log {
                                ui.label(msg);
                            }
                        });
                    });
                });

                // Middle: Stats
                ui.vertical(|ui| {
                    ui.group(|ui| {
                        ui.label("📊 Stats");
                        egui::ScrollArea::vertical().show(ui, |ui| {
                            ui.label(&state.stats);
                        });
                    });
                });

                // Right: LLM Output
                ui.vertical(|ui| {
                    ui.group(|ui| {
                        ui.label("🤖 LLM Output");
                        egui::ScrollArea::vertical().show(ui, |ui| {
                            ui.label(&state.llm_output);
                        });
                    });
                });
            });
        });

        // Request repaint for live updates
        ctx.request_repaint();
    }
}

fn handle_client(stream: TcpStream, state: &Arc<Mutex<GuiState>>) {
    println!("Rust GUI connected from {:?}", stream.peer_addr());
    let reader = BufReader::new(stream);

    for line in reader.lines() {
        if let Ok(msg) = line {
            let mut state = state.lock().unwrap();

            if msg.starts_with("CHAT:") {
                state.chat_log.push(msg[5..].to_string());

                // Truncate chat log if it exceeds max lines
                if state.chat_log.len() > CHAT_LOG_MAX_LINES {
                    let excess = state.chat_log.len() - CHAT_LOG_MAX_LINES;
                    state.chat_log.drain(0..excess);
                }
            } else if msg.starts_with("STATS:") {
                state.stats = msg[6..].to_string();
            } else if msg.starts_with("LLM:") {
                state.llm_output = msg[4..].to_string();
            }
        }
    }

    println!("Rust GUI client disconnected");
}

fn main() -> eframe::Result<()> {
    let state = Arc::new(Mutex::new(GuiState::default()));
    let state_clone = state.clone();

    // TCP listener thread
    thread::spawn(move || {
        let listener = TcpListener::bind("127.0.0.1:7879")
            .expect("Failed to bind to port 7879");
        println!("Waiting for Rust GUI to connect on 127.0.0.1:7879...");

        for stream in listener.incoming() {
            if let Ok(stream) = stream {
                let state_clone = state_clone.clone();
                thread::spawn(move || handle_client(stream, &state_clone));
            }
        }
    });

    // GUI options
    let options = eframe::NativeOptions::default();

    eframe::run_native(
        "Twitch Bot Dashboard",
        options,
        Box::new(|_cc| Box::new(MyApp { state })),
    )
}
