import Foundation

class NetworkManager {
    static let shared = NetworkManager()
    
    func uploadFile(fileURL: URL, authToken: String) {
        let url = URL(string: "http://localhost:8000/pkm/ingest")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        // Authorization Header
        request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        
        // Multipart Form Data Setup
        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        guard let fileData = try? Data(contentsOf: fileURL) else { return }
        let filename = fileURL.lastPathComponent
        let mimeType = "application/pdf" // Simplified. Use UniformTypeIdentifiers for dynamic mime.
        
        // Build Body
        var body = Data()
        
        // 1. Boundary + Headers
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        
        // 2. File Data
        body.append(fileData)
        body.append("\r\n".data(using: .utf8)!)
        
        // 3. Closing Boundary
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        
        // Send
        let task = URLSession.shared.uploadTask(with: request, from: body) { data, response, error in
            if let error = error {
                print("❌ Upload failed: \(error)")
                return
            }
            if let httpResp = response as? HTTPURLResponse, httpResp.statusCode == 200 {
                print("✅ Uploaded: \(filename)")
            }
        }
        task.resume()
    }
}