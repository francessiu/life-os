import SwiftUI

@main
struct LifeOSMacApp: App {
    // Connect the AppDelegate
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    
    var body: some Scene {
        WindowGroup {
            // This is the "Settings" or "Dashboard" window
            Text("LifeOS Butler Settings")
                .frame(width: 300, height: 200)
        }
    }
}