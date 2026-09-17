import SwiftUI
import WebKit

struct AshenWebView: UIViewRepresentable {
    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        config.mediaTypesRequiringUserActionForPlayback = []

        let controller = WKUserContentController()
        controller.add(context.coordinator, name: "ashenNative")
        controller.addUserScript(WKUserScript(
            source: Self.bridgeScript,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        ))
        config.userContentController = controller

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = context.coordinator
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.isOpaque = false
        webView.backgroundColor = UIColor(red: 0.043, green: 0.035, blue: 0.031, alpha: 1)
        context.coordinator.webView = webView

        guard let index = Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "Web") else {
            webView.loadHTMLString("<body style='background:#0b0908;color:white;font-family:system-ui;padding:24px'><h2>Ashen Voice Studio</h2><p>Bundled web assets are missing. Run the iOS preparation step before building.</p></body>", baseURL: nil)
            return webView
        }
        let webRoot = index.deletingLastPathComponent()
        webView.loadFileURL(index, allowingReadAccessTo: webRoot)
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    static let bridgeScript = #"""
    (() => {
      window.AshenIOS = { native: true, version: '1.6.0' };
      const pending = new Map();

      window.__ashenNativeResolve = (id, ok, b64) => {
        const p = pending.get(id);
        if (!p) return;
        pending.delete(id);
        try {
          const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
          const json = new TextDecoder().decode(bytes);
          const payload = JSON.parse(json);
          if (ok) p.resolve(payload);
          else p.reject(new Error(payload.error || payload.message || 'Native iPhone command failed'));
        } catch (e) {
          p.reject(e);
        }
      };

      const invoke = (command, args = {}) => new Promise((resolve, reject) => {
        const id = (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`);
        pending.set(id, { resolve, reject });
        window.webkit.messageHandlers.ashenNative.postMessage({ id, command, args });
      });

      // Tauri-shaped compatibility layer. The shared Ashen Voice frontend can use the
      // same invoke() calls on Linux and iPhone while the native implementation differs.
      window.__TAURI__ = window.__TAURI__ || {};
      window.__TAURI__.core = window.__TAURI__.core || {};
      window.__TAURI__.core.invoke = invoke;
      window.__TAURI_INTERNALS__ = window.__TAURI_INTERNALS__ || { platform: 'ios' };
    })();
    """#

    final class Coordinator: NSObject, WKScriptMessageHandler, WKNavigationDelegate {
        weak var webView: WKWebView?

        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
            guard message.name == "ashenNative",
                  let body = message.body as? [String: Any],
                  let id = body["id"] as? String,
                  let command = body["command"] as? String else { return }
            let args = body["args"] as? [String: Any] ?? [:]

            Task {
                do {
                    let result = try await IOSVoiceEngine.shared.handle(command: command, args: args)
                    await respond(id: id, ok: true, payload: result)
                } catch {
                    await respond(id: id, ok: false, payload: ["error": error.localizedDescription])
                }
            }
        }

        @MainActor
        private func respond(id: String, ok: Bool, payload: [String: Any]) {
            guard JSONSerialization.isValidJSONObject(payload),
                  let data = try? JSONSerialization.data(withJSONObject: payload),
                  let webView else { return }
            let b64 = data.base64EncodedString()
            let safeID = id.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"")
            webView.evaluateJavaScript("window.__ashenNativeResolve(\"\(safeID)\", \(ok ? "true" : "false"), \"\(b64)\");")
        }
    }
}
