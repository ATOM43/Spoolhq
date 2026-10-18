fn main() {
    // Declaring the app's commands makes Tauri generate a permission for each one, so
    // the webview can call only the commands its capability lists.
    let manifest = tauri_build::AppManifest::new().commands(&["daemon_info", "daemon_get"]);
    tauri_build::try_build(tauri_build::Attributes::new().app_manifest(manifest))
        .expect("failed to run the Tauri build script");
}
