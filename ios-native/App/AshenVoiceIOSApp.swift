import SwiftUI

@main
struct AshenVoiceIOSApp: App {
    var body: some Scene {
        WindowGroup {
            AshenWebView()
                .ignoresSafeArea()
                .preferredColorScheme(.dark)
        }
    }
}
