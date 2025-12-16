import Cocoa
import SwiftUI

class AppDelegate: NSObject, NSApplicationDelegate, FolderWatcherDelegate {
    var characterController: CharacterController?
    var statusItem: NSStatusItem?
    var iCloudWatcher: FolderWatcher?

    // Hardcoded for demo. In production, fetch from Keychain after login.
    let userToken = "YOUR_JWT_TOKEN_HERE"

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

        // 5. Start watching file changes 
        setupiCloudWatch()
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

    func setupiCloudWatch() {
        // Use Apple's API to find the ubiquity (iCloud) container
        // Note: MUST enable "iCloud" capability in Xcode for this to work.
        // Pass 'nil' to get the default container.
        guard let iCloudURL = FileManager.default.url(forUbiquityContainerIdentifier: nil)?.appendingPathComponent("Documents") else {
            print("⚠️ iCloud Drive not enabled or accessible.")
            return
        }
        
        iCloudWatcher = FolderWatcher(url: iCloudURL)
        iCloudWatcher?.delegate = self
        iCloudWatcher?.start()
    }
    
    // Delegate Method
    func folderWatcher(_ watcher: FolderWatcher, didDetectChangesIn files: [URL]) {
        print("📂 Detected \(files.count) files in iCloud. Syncing...")
        
        for file in files {
            // Upload every file found (Optimised: Check modification date in production)
            NetworkManager.shared.uploadFile(fileURL: file, authToken: userToken)
        }
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