use eframe::egui;
use serde_json::Value;
use tokio::net::TcpListener;
use tokio::io::AsyncReadExt;
use tokio::sync::mpsc::{self, UnboundedSender};

#[tokio::main]
async fn main() -> eframe::Result<()> {
    // Channel to send messages from TCP listener to GUI
    let (tx, rx) = mpsc::unbounded_channel::<String>();

    // Spawn TCP listener for Python
    tokio::spawn(async move {
        let listener = TcpListener::bind("127.0.0.1:4000").await.unwrap();
        println!("Listening for Python messages on 127.0.0.1:4000");
        loop {
            let (mut socket, _) = listener.accept().await.unwrap();
            let tx_clone: UnboundedSender<String> = tx.clone();
            tokio::spawn(async move {
                let mut buf = vec![0; 1024];
                let n = socket.read(&mut buf).await.unwrap();
                if n == 0 { return; }
                if let Ok(msg_json) = serde_json::from_slice::<Value>(&buf[..n]) {
                    if let Some(text) = msg_json.get("message").and_then(|v| v.as_str()) {
                        let _ = tx_clone.send(text.to_string());
                    }
                }
            });
        }
    });

    // Start GUI
    let app = MyApp { messages: Vec::new(), rx };
    let options = eframe::NativeOptions::default();
    eframe::run_native("Twitch Bot GUI", options, Box::new(|_cc| Box::new(app)))
}

struct MyApp {
    messages: Vec<String>,
    rx: tokio::sync::mpsc::UnboundedReceiver<String>,
}

impl eframe::App for MyApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // Drain all messages received from Python
        while let Ok(msg) = self.rx.try_recv() {
            self.messages.push(msg);
        }

        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("Twitch Bot GUI");
            for msg in &self.messages {
                ui.label(msg);
            }
        });

        ctx.request_repaint(); // continuously update
    }
}
