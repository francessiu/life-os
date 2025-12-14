import SwiftUI
import FamilyControls

struct ContentView: View {
    @EnvironmentObject var focusManager: FocusManager
    @State var isPresented = false
    
    var body: some View {
        VStack(spacing: 20) {
            Text("LifeOS Focus Shield")
                .font(.title)
                .bold()
            
            // 3. Native Family Picker to select apps to block
            Button("Select Apps to Block") {
                isPresented = true
            }
            .familyActivityPicker(isPresented: $isPresented, selection: $focusManager.selection)
            
            // 4. Toggle Focus
            Button(action: {
                if focusManager.isFocusActive {
                    focusManager.endFocusSession()
                } else {
                    focusManager.startFocusSession()
                }
            }) {
                Text(focusManager.isFocusActive ? "Stop Focus" : "Start Focus")
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(focusManager.isFocusActive ? Color.red : Color.black)
                    .foregroundColor(.white)
                    .cornerRadius(12)
            }
        }
        .padding()
    }
}

// Updated FocusManager to handle Real Selections
class FocusManager: ObservableObject {
    let store = ManagedSettingsStore()
    @Published var selection = FamilyActivitySelection() // Holds the user's chosen apps
    @Published var isFocusActive = false
    
    func startFocusSession() {
        // Apply the shield to the specific apps selected by user
        store.shield.applicationCategories = ShieldSettings.ActivityCategoryPolicy.specific(selection.categoryTokens)
        store.shield.applications = selection.applicationTokens
        store.shield.webDomains = selection.webDomainTokens
        isFocusActive = true
    }
    
    func endFocusSession() {
        store.shield.applicationCategories = nil
        store.shield.applications = nil
        store.shield.webDomains = nil
        isFocusActive = false
    }
}