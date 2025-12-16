import Foundation

protocol FolderWatcherDelegate: AnyObject {
    func folderWatcher(_ watcher: FolderWatcher, didDetectChangesIn files: [URL])
}

class FolderWatcher {
    private var dirFD: CInt = -1
    private var source: DispatchSourceFileSystemObject?
    private let queue = DispatchQueue(label: "com.lifeos.folderwatcher", attributes: .concurrent)
    
    let folderURL: URL
    weak var delegate: FolderWatcherDelegate?
    
    init(url: URL) {
        self.folderURL = url
    }

    func start() {
        // 1. Open Directory File Descriptor
        dirFD = open(folderURL.path, O_EVTONLY)
        if dirFD == -1 {
            print("❌ Failed to open folder: \(folderURL.path)")
            return
        }
        
        // 2. Create Dispatch Source
        source = DispatchSource.makeFileSystemObjectSource(
            fileDescriptor: dirFD,
            eventMask: .write, // Listen for content changes
            queue: queue
        )
        
        // 3. Define Event Handler
        source?.setEventHandler { [weak self] in
            self?.scanForChanges()
        }
        
        source?.setCancelHandler { [weak self] in
            guard let self = self else { return }
            close(self.dirFD)
        }
        
        source?.resume()
        print("👀 Watching: \(folderURL.path)")
    }

    func stop() {
        source?.cancel()
    }

    private func scanForChanges() {
        // Logic: Scan folder for recently modified files and upload them
        do {
            let fileURLs = try FileManager.default.contentsOfDirectory(
                at: folderURL,
                includingPropertiesForKeys: [.contentModificationDateKey]
            )
            
            // In a real app, you compare 'modificationDate' against a saved timestamp
            // For now, we send all visible files
            let visibleFiles = fileURLs.filter { !$0.lastPathComponent.hasPrefix(".") }
            
            DispatchQueue.main.async {
                self.delegate?.folderWatcher(self, didDetectChangesIn: visibleFiles)
            }
        } catch {
            print("Scan error: \(error)")
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