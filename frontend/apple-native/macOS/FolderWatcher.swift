import Foundation

class FolderWatcher {
    private var fileDescriptor: CInt = -1
    private var source: DispatchSourceFileSystemObject?
    let folderURL: URL
    
    init(url: URL) {
        self.folderURL = url
    }
    
    func startMonitoring() {
        // 1. Open the folder
        fileDescriptor = open(folderURL.path, O_EVTONLY)
        if fileDescriptor == -1 { return }
        
        // 2. Create Dispatch Source
        source = DispatchSource.makeFileSystemObjectSource(
            fileDescriptor: fileDescriptor,
            eventMask: .write, // Monitor for changes/writes
            queue: DispatchQueue.global()
        )
        
        // 3. Define Event Handler
        source?.setEventHandler { [weak self] in
            print("iCloud Folder Changed!")
            self?.handleFileChange()
        }
        
        source?.resume()
        print("Started watching: \(folderURL.path)")
    }
    
    private func handleFileChange() {
        // Logic: Scan folder for recently modified files and upload them
        // Real implementation requires checking 'modificationDate'.
        do {
            let fileURLs = try FileManager.default.contentsOfDirectory(
                at: folderURL, 
                includingPropertiesForKeys: [.contentModificationDateKey]
            )
            
            for fileURL in fileURLs {
                // Ignore hidden files
                if fileURL.lastPathComponent.hasPrefix(".") { continue }
                
                // Upload this file to backend
                uploadFile(fileURL)
            }
        } catch {
            print("Error scanning folder: \(error)")
        }
    }
    
    private func uploadFile(_ url: URL) {
        // 1. Prepare Request
        let backendURL = URL(string: "http://localhost:8000/pkm/ingest")!
        var request = URLRequest(url: backendURL)
        request.httpMethod = "POST"
        
        // 2. Create Multipart Form Data (Simplified)
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        // (Multipart body construction omitted for brevity - use a library like Alamofire in production)
        
        // 3. Send
        URLSession.shared.dataTask(with: request).resume()
    }
}