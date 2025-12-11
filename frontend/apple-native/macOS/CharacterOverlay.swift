import SwiftUI
import AppKit

// 1. The Transparent Floating Window
class CharacterWindow: NSWindow {
    init(contentRect: NSRect, backing: NSWindow.BackingStoreType, defer flag: Bool) {
        super.init(contentRect: contentRect, backing: backing, defer: flag)
        
        self.isOpaque = false
        self.backgroundColor = .clear
        self.level = .floating // Crucial: Keeps it above other apps
        self.styleMask = [.borderless, .nonactivatingPanel] // Removes title bar
        self.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary] // Shows on all desktops
        self.ignoresMouseEvents = false // Allow clicking the character
    }
}

// 2. The Character View
struct CharacterView: View {
    @State private var isHovering = false
    
    var body: some View {
        Image("character_idle") // TODO: create this asset
            .resizable()
            .frame(width: 100, height: 100)
            .shadow(radius: 5)
            .scaleEffect(isHovering ? 1.1 : 1.0)
            .onHover { hover in
                withAnimation { isHovering = hover }
            }
            .onTapGesture {
                print("Character clicked! Open Chat...") // TODO: allow user to rename the character
                // Trigger logic to open main app window
            }
    }
}

// 3. Controller to Launch it
class CharacterController: NSObject {
    var window: CharacterWindow!
    
    func show() {
        let screenSize = NSScreen.main?.frame.size ?? CGSize(width: 1920, height: 1080)
        // Position at bottom right
        let frame = CGRect(x: screenSize.width - 150, y: 50, width: 120, height: 120)
        
        window = ButlerWindow(contentRect: frame, backing: .buffered, defer: false)
        window.contentView = NSHostingView(rootView: CharacterView())
        window.makeKeyAndOrderFront(nil)
    }
}