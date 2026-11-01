//! A project's live run events, from the daemon's WebSocket to the webview.
//!
//! The webview never sees the token and the CSP allows no `ws://`, so Rust holds the
//! socket: it sends the auth message first, forwards each event envelope through a
//! Tauri [`Channel`], tracks the last `seq` and, after a drop or a `4408 too_slow`
//! close, reconnects with `since=<last seq>` (backoff 0.5 s doubling to 10 s). A 4401,
//! 4404 or 1008 close, or a refused handshake, stops the stream for good. Unsubscribing
//! or closing the window ends it with a normal close.

use std::collections::HashMap;
use std::sync::Mutex;
use std::sync::atomic::{AtomicU32, Ordering};
use std::time::Duration;

use futures_util::{SinkExt, StreamExt};
use serde::Serialize;
use serde_json::Value;
use tauri::ipc::Channel;
use tokio::sync::watch;
use tokio_tungstenite::tungstenite::protocol::CloseFrame;
use tokio_tungstenite::tungstenite::protocol::frame::coding::CloseCode;
use tokio_tungstenite::tungstenite::{Error as WsError, Message};

use crate::daemon::{
    DaemonError, PORT_ENV_VAR, api_url, current_home, read_port, read_token, token_path,
};

#[derive(Debug, Clone, Copy)]
pub struct Backoff {
    pub first: Duration,
    pub max: Duration,
}

pub const BACKOFF: Backoff = Backoff {
    first: Duration::from_millis(500),
    max: Duration::from_secs(10),
};

/// What the webview receives on its channel.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum StreamMessage {
    /// One event envelope, as the daemon sent it.
    Event { event: Value },
    /// The stream stopped for good (bad token, unknown project, origin refused).
    Stopped { reason: String },
}

/// Where and how to connect; re-read before every attempt, like the HTTP commands do.
pub struct Target {
    pub url: String,
    pub token: String,
}

enum End {
    Retry { connected: bool },
    Final(String),
    Stopped,
}

fn final_reason(code: u16) -> Option<&'static str> {
    match code {
        4401 => Some("the daemon rejected the token"),
        4404 => Some("the daemon has no such project"),
        1008 => Some("the daemon refused this app's origin"),
        _ => None,
    }
}

/// Run one subscription until it stops: `stop` changes or its sender is dropped, a final
/// close arrives, or `send` returns false (the webview is gone).
pub async fn run_stream<T, S>(
    target: T,
    since: u64,
    backoff: Backoff,
    mut stop: watch::Receiver<bool>,
    mut send: S,
) where
    T: Fn(u64) -> Result<Target, DaemonError>,
    S: FnMut(StreamMessage) -> bool,
{
    let mut last = since;
    let mut delay = backoff.first;
    loop {
        match connect_once(&target, &mut last, &mut stop, &mut send).await {
            End::Stopped => return,
            End::Final(reason) => {
                send(StreamMessage::Stopped { reason });
                return;
            }
            End::Retry { connected } => {
                if connected {
                    delay = backoff.first;
                }
            }
        }
        tokio::select! {
            () = tokio::time::sleep(delay) => {}
            _ = stop.changed() => return,
        }
        delay = (delay * 2).min(backoff.max);
    }
}

async fn connect_once<T, S>(
    target: &T,
    last: &mut u64,
    stop: &mut watch::Receiver<bool>,
    send: &mut S,
) -> End
where
    T: Fn(u64) -> Result<Target, DaemonError>,
    S: FnMut(StreamMessage) -> bool,
{
    // No daemon, port or token yet: try again later, as the HTTP status poll does.
    let Ok(Target { url, token }) = target(*last) else {
        return End::Retry { connected: false };
    };
    let connected = tokio::select! {
        result = tokio_tungstenite::connect_async(url) => result,
        _ = stop.changed() => return End::Stopped,
    };
    let mut ws = match connected {
        Ok((ws, _)) => ws,
        Err(WsError::Http(response)) => {
            return End::Final(format!(
                "the daemon refused the connection (HTTP {})",
                response.status().as_u16()
            ));
        }
        Err(_) => return End::Retry { connected: false },
    };
    let auth = serde_json::json!({ "type": "auth", "token": token }).to_string();
    if ws.send(Message::text(auth)).await.is_err() {
        return End::Retry { connected: false };
    }
    loop {
        let message = tokio::select! {
            message = ws.next() => message,
            _ = stop.changed() => {
                let frame = CloseFrame { code: CloseCode::Normal, reason: "".into() };
                let _ = ws.close(Some(frame)).await;
                return End::Stopped;
            }
        };
        match message {
            Some(Ok(Message::Text(text))) => {
                let Ok(value) = serde_json::from_str::<Value>(text.as_str()) else {
                    continue;
                };
                // A ping has no seq; an event at or below `last` was already forwarded.
                let Some(seq) = value.get("seq").and_then(Value::as_u64) else {
                    continue;
                };
                if seq <= *last {
                    continue;
                }
                *last = seq;
                if !send(StreamMessage::Event { event: value }) {
                    let _ = ws.close(None).await;
                    return End::Stopped;
                }
            }
            Some(Ok(Message::Close(frame))) => {
                let code = frame.map(|frame| u16::from(frame.code));
                return match code.and_then(final_reason) {
                    Some(reason) => End::Final(reason.to_owned()),
                    None => End::Retry { connected: true },
                };
            }
            Some(Ok(_)) => {}
            Some(Err(_)) | None => return End::Retry { connected: true },
        }
    }
}

/// A project name as the daemon's routes accept it, so it can't change the path.
pub fn check_project(project: &str) -> Result<(), DaemonError> {
    let valid = !project.is_empty()
        && project.len() <= 64
        && project
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'-');
    if valid {
        Ok(())
    } else {
        Err(DaemonError::InvalidRequest {
            message: format!("not a project name: {project:?}"),
        })
    }
}

fn daemon_target(project: &str, since: u64) -> Result<Target, DaemonError> {
    let home = current_home()?;
    let port = read_port(&home, std::env::var_os(PORT_ENV_VAR))?;
    let http = api_url(
        port,
        &format!("/api/projects/{project}/events?since={since}"),
    )?;
    let token = read_token(&home)?.ok_or_else(|| DaemonError::TokenMissing {
        path: token_path(&home).display().to_string(),
    })?;
    Ok(Target {
        url: http.replacen("http://", "ws://", 1),
        token,
    })
}

/// The open subscriptions. Dropping a stop sender ends its stream.
#[derive(Default)]
pub struct Streams {
    next: AtomicU32,
    stops: Mutex<HashMap<u32, watch::Sender<bool>>>,
}

impl Streams {
    fn stops(&self) -> std::sync::MutexGuard<'_, HashMap<u32, watch::Sender<bool>>> {
        // A panic while holding the lock leaves the map usable.
        self.stops
            .lock()
            .unwrap_or_else(std::sync::PoisonError::into_inner)
    }

    /// End every stream (the window is closing).
    pub fn stop_all(&self) {
        self.stops().clear();
    }
}

/// Start forwarding `project`'s events after `since` to `on_event`; returns the id
/// `events_unsubscribe` takes.
#[tauri::command]
pub fn events_subscribe(
    streams: tauri::State<'_, Streams>,
    project: String,
    since: u64,
    on_event: Channel<StreamMessage>,
) -> Result<u32, DaemonError> {
    check_project(&project)?;
    let id = streams.next.fetch_add(1, Ordering::Relaxed);
    let (stop_tx, stop_rx) = watch::channel(false);
    streams.stops().insert(id, stop_tx);
    tauri::async_runtime::spawn(run_stream(
        move |since| daemon_target(&project, since),
        since,
        BACKOFF,
        stop_rx,
        move |message| on_event.send(message).is_ok(),
    ));
    Ok(id)
}

/// Stop a subscription and close its socket. An unknown id is a no-op.
#[tauri::command]
pub fn events_unsubscribe(streams: tauri::State<'_, Streams>, id: u32) {
    streams.stops().remove(&id);
}

#[cfg(test)]
mod tests {
    use std::sync::Arc;

    use tokio::net::{TcpListener, TcpStream};
    use tokio::sync::mpsc;
    use tokio_tungstenite::WebSocketStream;
    use tokio_tungstenite::tungstenite::handshake::server::{Request, Response};

    use super::*;

    const FAST: Backoff = Backoff {
        first: Duration::from_millis(10),
        max: Duration::from_millis(40),
    };
    const WAIT: Duration = Duration::from_secs(5);

    struct Harness {
        listener: TcpListener,
        messages: mpsc::UnboundedReceiver<StreamMessage>,
        stop: watch::Sender<bool>,
        task: tokio::task::JoinHandle<()>,
    }

    async fn start(since: u64) -> Harness {
        let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
        let port = listener.local_addr().unwrap().port();
        let (tx, messages) = mpsc::unbounded_channel();
        let (stop, stop_rx) = watch::channel(false);
        let task = tokio::spawn(run_stream(
            move |since| {
                Ok(Target {
                    url: format!("ws://127.0.0.1:{port}/api/projects/demo/events?since={since}"),
                    token: "secret-token".into(),
                })
            },
            since,
            FAST,
            stop_rx,
            move |message| tx.send(message).is_ok(),
        ));
        Harness {
            listener,
            messages,
            stop,
            task,
        }
    }

    /// Accept the next connection; returns the socket and the request's path and query.
    // The handshake callback's error type is tungstenite's, not ours.
    #[allow(clippy::result_large_err)]
    async fn accept(listener: &TcpListener) -> (WebSocketStream<TcpStream>, String) {
        let (tcp, _) = tokio::time::timeout(WAIT, listener.accept())
            .await
            .expect("the client connects")
            .unwrap();
        let uri = Arc::new(Mutex::new(String::new()));
        let seen = Arc::clone(&uri);
        let ws = tokio_tungstenite::accept_hdr_async(tcp, move |request: &Request, response| {
            *seen.lock().unwrap() = request.uri().to_string();
            Ok::<Response, _>(response)
        })
        .await
        .unwrap();
        let uri = uri.lock().unwrap().clone();
        (ws, uri)
    }

    async fn next_text(ws: &mut WebSocketStream<TcpStream>) -> Value {
        let message = tokio::time::timeout(WAIT, ws.next())
            .await
            .expect("a message arrives")
            .expect("the socket is open")
            .unwrap();
        serde_json::from_str(message.to_text().unwrap()).unwrap()
    }

    async fn send_event(ws: &mut WebSocketStream<TcpStream>, seq: u64) {
        let envelope = serde_json::json!({
            "seq": seq, "run_id": 1, "attempt": null, "ticket": "T01",
            "type": "log", "ts": "", "data": {}
        });
        ws.send(Message::text(envelope.to_string())).await.unwrap();
    }

    async fn close_with(ws: &mut WebSocketStream<TcpStream>, code: u16) {
        let frame = CloseFrame {
            code: CloseCode::from(code),
            reason: "".into(),
        };
        ws.close(Some(frame)).await.unwrap();
    }

    async fn received(harness: &mut Harness) -> StreamMessage {
        tokio::time::timeout(WAIT, harness.messages.recv())
            .await
            .expect("a message reaches the webview")
            .expect("the stream is still sending")
    }

    fn seq(message: &StreamMessage) -> u64 {
        match message {
            StreamMessage::Event { event } => event["seq"].as_u64().unwrap(),
            StreamMessage::Stopped { reason } => panic!("stopped: {reason}"),
        }
    }

    #[tokio::test]
    async fn the_auth_message_is_sent_first() {
        let harness = start(0).await;
        let (mut ws, uri) = accept(&harness.listener).await;
        assert_eq!(uri, "/api/projects/demo/events?since=0");
        assert_eq!(
            next_text(&mut ws).await,
            serde_json::json!({ "type": "auth", "token": "secret-token" })
        );
        drop(harness.stop);
        harness.task.await.unwrap();
    }

    #[tokio::test]
    async fn reconnect_resends_since_the_last_seq_after_4408() {
        let mut harness = start(2).await;
        let (mut first, uri) = accept(&harness.listener).await;
        assert_eq!(uri, "/api/projects/demo/events?since=2");
        next_text(&mut first).await;
        send_event(&mut first, 3).await;
        send_event(&mut first, 7).await;
        first
            .send(Message::text(r#"{"type":"ping"}"#))
            .await
            .unwrap();
        close_with(&mut first, 4408).await;

        let (mut second, uri) = accept(&harness.listener).await;
        assert_eq!(uri, "/api/projects/demo/events?since=7");
        assert_eq!(next_text(&mut second).await["type"], "auth");
        send_event(&mut second, 7).await; // already forwarded
        send_event(&mut second, 8).await;

        let mut seqs = Vec::new();
        for _ in 0..3 {
            seqs.push(seq(&received(&mut harness).await));
        }
        assert_eq!(seqs, [3, 7, 8]);
        drop(harness.stop);
        harness.task.await.unwrap();
    }

    #[tokio::test]
    async fn a_dropped_connection_reconnects() {
        let mut harness = start(0).await;
        let (mut first, _) = accept(&harness.listener).await;
        next_text(&mut first).await;
        send_event(&mut first, 5).await;
        assert_eq!(seq(&received(&mut harness).await), 5);
        drop(first); // no close frame: the daemon died

        let (_second, uri) = accept(&harness.listener).await;
        assert_eq!(uri, "/api/projects/demo/events?since=5");
        drop(harness.stop);
        harness.task.await.unwrap();
    }

    #[tokio::test]
    async fn unsubscribe_closes_the_socket() {
        let harness = start(0).await;
        let (mut ws, _) = accept(&harness.listener).await;
        next_text(&mut ws).await;
        drop(harness.stop);

        let message = tokio::time::timeout(WAIT, ws.next())
            .await
            .expect("the client closes");
        match message {
            Some(Ok(Message::Close(Some(frame)))) => assert_eq!(frame.code, CloseCode::Normal),
            other => panic!("expected a normal close, got {other:?}"),
        }
        tokio::time::timeout(WAIT, harness.task)
            .await
            .expect("the stream ends")
            .unwrap();
    }

    #[tokio::test]
    async fn a_4401_close_stops_for_good() {
        let mut harness = start(0).await;
        let (mut ws, _) = accept(&harness.listener).await;
        next_text(&mut ws).await;
        close_with(&mut ws, 4401).await;

        assert_eq!(
            received(&mut harness).await,
            StreamMessage::Stopped {
                reason: "the daemon rejected the token".into()
            }
        );
        tokio::time::timeout(WAIT, harness.task)
            .await
            .expect("the stream ends")
            .unwrap();
        let again = tokio::time::timeout(Duration::from_millis(200), harness.listener.accept());
        assert!(again.await.is_err(), "no reconnect after 4401");
    }

    #[test]
    fn project_names_are_checked() {
        for project in ["demo", "my-app-2"] {
            assert!(check_project(project).is_ok(), "{project}");
        }
        for project in ["", "Demo", "a/b", "..", "a?since=1", &"x".repeat(65)] {
            assert!(check_project(project).is_err(), "{project}");
        }
    }

    #[test]
    fn messages_serialise_with_a_kind_tag() {
        let message = StreamMessage::Stopped { reason: "r".into() };
        assert_eq!(
            serde_json::to_value(&message).unwrap(),
            serde_json::json!({ "kind": "stopped", "reason": "r" })
        );
    }
}
