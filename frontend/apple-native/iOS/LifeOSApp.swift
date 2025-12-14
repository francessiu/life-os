mport SwiftUI
import FamilyControls // REQUIRED for Screen Time
import ManagedSettings

@main
struct LifeOSApp: App {
    // 1. The Center for Screen Time permissions
    let center = AuthorizationCenter.shared
    @StateObject var focusManager = FocusManager()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(focusManager)
                .onAppear {
                    requestPermissions()
                }
        }
    }
    
    // 2. Request Authorization on App Launch
    func requestPermissions() {
        Task {
            do {
                try await center.requestAuthorization(for: .individual)
                print("Screen Time Permission Granted")
            } catch {
                print("Failed to authorize: \(error)")
            }
        }
    }
}