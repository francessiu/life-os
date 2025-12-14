import Cocoa
import SwiftUI

class AppDelegate: NSObject, NSApplicationDelegate {
    var characterController: CharacterController?
    var statusItem: NSStatusItem? // Menu Bar Icon

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Initialize Controller
        characterController = CharacterController()

        // 1. Locate iCloud Drive Folder
        // Note: The path is usually ~/Library/Mobile Documents/com~apple~CloudDocs
        if let iCloudURL = FileManager.default.url(forUbiquityContainerIdentifier: nil)?.appendingPathComponent("Documents") {
            
            folderWatcher = FolderWatcher(url: iCloudURL)
            folderWatcher?.startMonitoring()
            
        } else {
            print("iCloud not enabled or accessible.")
        }
        
        // 2. Show the Butler immediately
        characterController?.show()
        
        // 3. Setup Menu Bar Icon (Optional)
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let button = statusItem?.button {
            button.image = NSImage(systemSymbolName: "brain.head.profile", accessibilityDescription: "LifeOS")
        }
        
        // 4. Start Polling Backend for Emotion State
        startPollingBackend()
    }
    
    func startPollingBackend() {
        Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { _ in
            self.fetchCharacterState()
        }
    }
    
    func fetchCharacterState() {
        // Simple URLSession to hit your FastAPI
        guard let url = URL(string: "http://localhost:8000/gamification/character/state") else { return }
        
        // Note: In a real app, you need to attach the JWT Token here!
        // var request = URLRequest(url: url)
        // request.setValue("Bearer <TOKEN>", forHTTPHeaderField: "Authorization")
        
        let task = URLSession.shared.dataTask(with: url) { data, _, _ in
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let emotion = json["emotion"] as? String else { return }
            
            // Dispatch to Main Thread to update UI
            DispatchQueue.main.async {
                // We notify the CharacterView via NotificationCenter or ObservableObject
                NotificationCenter.default.post(name: .updateEmotion, object: nil, userInfo: ["emotion": emotion])
            }
        }
        task.resume()
    }
}

// Extension for Notification
extension Notification.Name {
    static let updateEmotion = Notification.Name("updateEmotion")
}

// Updated CharacterView to listen for updates
struct CharacterView: View {
    @State private var currentEmotion = "happy"
    
    var body: some View {
        VStack {
            Text(emojiForEmotion(currentEmotion))
                .font(.system(size: 80))
                .shadow(radius: 5)
        }
        .onReceive(NotificationCenter.default.publisher(for: .updateEmotion)) { notification in
            if let emotion = notification.userInfo?["emotion"] as? String {
                self.currentEmotion = emotion
            }
        }
    }
    
    func emojiForEmotion(_ emotion: String) -> String {
        switch emotion {
        case "worried": return "🙀"
        case "panicked": return "😿"
        default: return "😺"
        }
    }
}