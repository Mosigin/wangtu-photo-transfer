import Foundation

@main
struct PolicyChecks {
    static func main() throws {
        let resource = ImportResource(file: "PF1.heic", kind: "photo", bytes: 10, originalFilename: "original.heic",
                                      sha256: String(repeating: "a", count: 64))
        let photo = ImportEntry(id: "PF1", resources: [resource], creationDate: nil)
        assert(photo.isValid)
        let video = ImportResource(file: "PF1.mov", kind: "video", bytes: 10, originalFilename: "clip.mov", sha256: resource.sha256)
        assert(ImportEntry(id: "PF1", resources: [video], creationDate: nil).isValid)
        assert(!ImportEntry(id: "PF1", resources: [resource, video], creationDate: nil).isValid)
        let paired = ImportResource(file: "PF1.mov", kind: "pairedVideo", bytes: 10, originalFilename: "original.mov", sha256: resource.sha256)
        let live = ImportEntry(id: "PF1", resources: [resource, paired], creationDate: nil)
        assert(live.isValid && live.isLive && live.bytes == 20)
        assert(!ImportBatch(id: "one", entries: [photo, photo], schema: 1, reserveBytes: 1_000_000_000).isValid)
        for path in ["../secret", "/secret", "..", "folder\\photo", "a\0b"] {
            assert(!ImportPolicy.validFile(path))
        }
        assert(!ImportPolicy.canReceive(free: 1_150_000_000, bytes: 1))
        assert(ImportPolicy.canReceive(free: 1_150_000_020, bytes: 10))
        assert(!ImportPolicy.canReceive(free: 1_150_000_019, bytes: 10))
        assert(ImportPolicy.idleState("space") == "space")
        assert(ImportPolicy.idleState("error") == "error")
        assert(ImportPolicy.idleState("batchDone") == "paused")
        assert(ImportPolicy.idleState(ImportPolicy.idleState("space")) == "space")
        assert(ImportBatch(id: "one", entries: [photo], schema: 1, reserveBytes: 1_000_000_000).isValid)
        assert(!ImportBatch(id: "one", entries: [photo], schema: 2, reserveBytes: 1_000_000_000).isValid)
        let data = try JSONEncoder().encode(live)
        let decoded = try JSONDecoder().decode(ImportEntry.self, from: data)
        assert(decoded == live)
        print("Phone import policy, resource types, identities and reserve checks passed")
    }
}
