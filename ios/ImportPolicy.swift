import Foundation

// Shared by the phone and the independent Mac regression runner.
enum ImportPolicy {
    static let reserve: Int64 = 1_000_000_000
    static let overhead: Int64 = 150_000_000
    static let batchLimit: Int64 = 32_000_000

    static func idleState(_ current: String) -> String {
        ["space", "error"].contains(current) ? current : "paused"
    }

    static func canReceive(free: Int64, bytes: Int64) -> Bool {
        bytes > 0 && free >= reserve + overhead && bytes <= (free - reserve - overhead) / 2
    }

    static func validFile(_ name: String) -> Bool {
        !name.isEmpty && name != "." && name != ".." && !name.contains("/")
            && !name.contains("\\") && !name.contains("\0")
    }
}

struct ImportResource: Codable, Equatable {
    let file: String
    let kind: String
    let bytes: Int64
    let originalFilename: String?
    let sha256: String
}

struct ImportEntry: Codable, Equatable {
    let id: String
    let resources: [ImportResource]
    let creationDate: String?

    var bytes: Int64 { resources.reduce(0) { $0 + $1.bytes } }
    var isVideo: Bool { resources.count == 1 && resources[0].kind == "video" }
    var isLive: Bool { resources.contains { $0.kind == "pairedVideo" } }
    var isValid: Bool {
        guard ImportPolicy.validFile(id), resources.count == 1 || resources.count == 2,
              Set(resources.map(\.file)).count == resources.count else { return false }
        let kinds = resources.map(\.kind).sorted()
        guard kinds == ["photo"] || kinds == ["video"] || kinds == ["pairedVideo", "photo"] else { return false }
        return resources.allSatisfy {
            ImportPolicy.validFile($0.file) && ($0.originalFilename.map(ImportPolicy.validFile) ?? true)
                && $0.bytes > 0 && $0.bytes <= 2_000_000_000_000
                && $0.sha256.count == 64 && $0.sha256.allSatisfy { "0123456789abcdef".contains($0) }
        }
    }
}

struct ImportBatch: Codable, Equatable {
    let id: String
    let entries: [ImportEntry]
    let schema: Int
    let reserveBytes: Int64
    var isValid: Bool {
        schema == 1 && reserveBytes >= ImportPolicy.reserve && reserveBytes <= 1_000_000_000_000
            && ImportPolicy.validFile(id) && !entries.isEmpty && entries.count <= 20
            && Set(entries.map(\.id)).count == entries.count && entries.allSatisfy(\.isValid)
    }
}

struct ImportReceipt: Codable {
    let id: String
    let asset: String
    let state: String
    let entry: ImportEntry
}

struct ImportSpaceStop: Codable {
    let batch: String
}
