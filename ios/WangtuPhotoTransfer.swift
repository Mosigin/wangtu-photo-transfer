import SwiftUI
import Photos
import CryptoKit
import Darwin

private let documents = URL.documentsDirectory
private func availableBytes() throws -> Int64 {
    var stats = statfs()
    guard statfs(documents.path, &stats) == 0 else { throw ImportError.storage }
    return Int64(stats.f_bavail) * Int64(stats.f_bsize)
}
private enum ImportError: Error { case storage, manifest, journal, changed, uncertain, verify }

private func digest(_ url: URL) throws -> (Int64, String) {
    let handle = try FileHandle(forReadingFrom: url)
    defer { try? handle.close() }
    var hash = SHA256(); var size: Int64 = 0
    while true {
        let count: Int = try autoreleasepool {
            let data = try handle.read(upToCount: 1_048_576) ?? Data()
            hash.update(data: data); size += Int64(data.count)
            return data.count
        }
        if count == 0 { break }
    }
    return (size, hash.finalize().map { String(format: "%02x", $0) }.joined())
}

private final class ResourceDigest: @unchecked Sendable {
    let lock = NSLock()
    var hash = SHA256(); var size: Int64 = 0; var error: Error?
    func update(_ data: Data) {
        lock.lock(); defer { lock.unlock() }
        hash.update(data: data); size += Int64(data.count)
    }
}

private actor ImportWorker {
    private var enabled = false
    private var working = false
    private var loaded = false
    private var records: [String: ImportReceipt] = [:]
    private var state = "paused"
    private var batchID = ""
    private var reserveBytes = ImportPolicy.reserve
    private var batchContent: ImportBatch?
    private var spaceStoppedBatchID: String?
    private var batchResults: [String: String] = [:]
    private var errorCode = ""
    private let journal = documents.appendingPathComponent("receipts.jsonl")

    func setEnabled(_ value: Bool) {
        if value {
            let stop = documents.appendingPathComponent("STOP")
            if FileManager.default.fileExists(atPath: stop.path) {
                do { try FileManager.default.removeItem(at: stop) }
                catch { state = "error"; enabled = false; return }
            }
        }
        if value && state == "space" { state = "ready" }
        enabled = value
    }

    private func loadJournal() throws {
        guard !loaded else { return }
        if FileManager.default.fileExists(atPath: journal.path) {
            let text = try String(contentsOf: journal, encoding: .utf8)
            guard text.isEmpty || text.hasSuffix("\n") else { throw ImportError.journal }
            for line in text.split(separator: "\n") {
                let receipt = try JSONDecoder().decode(ImportReceipt.self, from: Data(line.utf8))
                guard receipt.id == receipt.entry.id, receipt.entry.isValid else { throw ImportError.journal }
                records[receipt.id] = receipt
            }
        }
        let stopURL = documents.appendingPathComponent("space-stop.json")
        if FileManager.default.fileExists(atPath: stopURL.path) {
            let stop = try JSONDecoder().decode(ImportSpaceStop.self, from: Data(contentsOf: stopURL))
            guard ImportPolicy.validFile(stop.batch) else { throw ImportError.manifest }
            spaceStoppedBatchID = stop.batch; batchID = stop.batch; state = "space"
            let request = try JSONDecoder().decode(ImportBatch.self,
                from: Data(contentsOf: documents.appendingPathComponent("request.json")))
            guard request.isValid, request.id == stop.batch else { throw ImportError.manifest }
            reserveBytes = request.reserveBytes
            batchContent = request
            for entry in request.entries {
                if let record = records[entry.id] {
                    guard record.entry == entry, ["verified", "failed"].contains(record.state) else {
                        throw ImportError.uncertain
                    }
                    batchResults[entry.id] = record.state
                }
            }
        }
        loaded = true
    }

    private func append(_ receipt: ImportReceipt) throws {
        if !FileManager.default.fileExists(atPath: journal.path) {
            guard FileManager.default.createFile(atPath: journal.path, contents: nil) else { throw ImportError.journal }
        }
        let handle = try FileHandle(forWritingTo: journal)
        defer { try? handle.close() }
        try handle.seekToEnd()
        var data = try JSONEncoder().encode(receipt); data.append(10)
        try handle.write(contentsOf: data); try handle.synchronize()
        records[receipt.id] = receipt
    }

    private func report() throws {
        let free = try availableBytes()
        let result: [String: Any] = ["state": state, "batch": batchID, "results": batchResults,
            "freeBytes": free, "reserveBytes": reserveBytes,
            "imported": records.values.filter { $0.state == "verified" }.count,
            "failed": records.values.filter { $0.state == "failed" }.count,
            "error": errorCode, "time": Date().timeIntervalSince1970, "enabled": enabled,
            "authorized": PHPhotoLibrary.authorizationStatus(for: .readWrite) == .authorized]
        try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
            .write(to: documents.appendingPathComponent("status.json"), options: .atomic)
    }

    private func verify(_ receipt: ImportReceipt) throws {
        let options = PHFetchOptions(); options.includeAllBurstAssets = true; options.includeHiddenAssets = true
        guard PHPhotoLibrary.authorizationStatus(for: .readWrite) == .authorized,
              let asset = PHAsset.fetchAssets(withLocalIdentifiers: [receipt.asset], options: options).firstObject,
              asset.mediaType == (receipt.entry.isVideo ? .video : .image),
              asset.mediaSubtypes.contains(.photoLive) == receipt.entry.isLive else { throw ImportError.uncertain }
        let actual = PHAssetResource.assetResources(for: asset)
        for expected in receipt.entry.resources {
            let type: PHAssetResourceType = expected.kind == "photo" ? .photo : (expected.kind == "video" ? .video : .pairedVideo)
            let matches = actual.filter {
                $0.type == type && $0.originalFilename.caseInsensitiveCompare(expected.originalFilename ?? expected.file) == .orderedSame
            }
            guard matches.count == 1 else { throw ImportError.verify }
            let accumulator = ResourceDigest(); let semaphore = DispatchSemaphore(value: 0)
            let requestOptions = PHAssetResourceRequestOptions(); requestOptions.isNetworkAccessAllowed = false
            let requestID = PHAssetResourceManager.default().requestData(for: matches[0], options: requestOptions,
                dataReceivedHandler: { data in autoreleasepool { accumulator.update(data) } },
                completionHandler: { error in accumulator.error = error; semaphore.signal() })
            if semaphore.wait(timeout: .now() + 60) == .timedOut {
                PHAssetResourceManager.default().cancelDataRequest(requestID)
                throw ImportError.verify
            }
            guard accumulator.error == nil, accumulator.size == expected.bytes,
                  accumulator.hash.finalize().map({ String(format: "%02x", $0) }).joined() == expected.sha256
            else { throw ImportError.verify }
        }
    }

    private func sourceURL(_ resource: ImportResource, batch: ImportBatch) throws -> URL {
        let url = documents.appendingPathComponent("Incoming", isDirectory: true)
            .appendingPathComponent(batch.id, isDirectory: true).appendingPathComponent(resource.file)
        let values = try url.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey])
        guard values.isRegularFile == true, values.isSymbolicLink != true else { throw ImportError.manifest }
        return url
    }

    private func removeStaged(_ entry: ImportEntry, batch: ImportBatch) throws {
        for resource in entry.resources {
            let url = documents.appendingPathComponent("Incoming").appendingPathComponent(batch.id)
                .appendingPathComponent(resource.file)
            if FileManager.default.fileExists(atPath: url.path) { try FileManager.default.removeItem(at: url) }
        }
    }

    private func importEntry(_ entry: ImportEntry, batch: ImportBatch) throws -> String {
        if let previous = records[entry.id] {
            guard previous.entry == entry else { throw ImportError.changed }
            if previous.state == "verified" {
                try removeStaged(entry, batch: batch)
                return "verified"
            }
            if previous.state == "pending" {
                // An unknown commit is verified by its persisted Photos ID; never create another copy.
                try verify(previous)
                try append(ImportReceipt(id: entry.id, asset: previous.asset, state: "verified", entry: entry))
                try removeStaged(entry, batch: batch)
                return "verified"
            }
            try removeStaged(entry, batch: batch)
            return "failed"
        }
        var sources: [URL] = []
        for resource in entry.resources {
            let url = try sourceURL(resource, batch: batch)
            let (size, hash) = try digest(url)
            guard size == resource.bytes, hash == resource.sha256 else { throw ImportError.changed }
            sources.append(url)
        }
        if entry.isLive {
            let semaphore = DispatchSemaphore(value: 0)
            var recognized = false
            let requestID = PHLivePhoto.request(withResourceFileURLs: sources, placeholderImage: nil,
                targetSize: CGSize(width: 32, height: 32), contentMode: .aspectFit) { photo, info in
                if (info[PHLivePhotoInfoIsDegradedKey] as? Bool) == true { return }
                recognized = photo != nil
                semaphore.signal()
            }
            if semaphore.wait(timeout: .now() + 60) == .timedOut {
                PHLivePhoto.cancelRequest(withRequestID: requestID)
                throw ImportError.verify
            }
            guard recognized else { throw ImportError.verify }
        }
        // The payload is already staged. Keep room for Photos metadata and thumbnails as well.
        guard try availableBytes() >= reserveBytes + ImportPolicy.overhead else { return "space" }
        var attempted: ImportReceipt?
        var journalError: Error?
        do {
            try PHPhotoLibrary.shared().performChangesAndWait {
                let request = PHAssetCreationRequest.forAsset()
                if let date = entry.creationDate {
                    let formatter = ISO8601DateFormatter()
                    formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
                    request.creationDate = formatter.date(from: date) ?? ISO8601DateFormatter().date(from: date)
                }
                let identifier = request.placeholderForCreatedAsset!.localIdentifier
                let record = ImportReceipt(id: entry.id, asset: identifier, state: "pending", entry: entry)
                do { try self.append(record); attempted = record }
                catch {
                    journalError = error
                    // A failed durable intent must never be allowed to commit an asset.
                    fatalError("Cannot persist import intent; refusing to commit")
                }
                for (resource, url) in zip(entry.resources, sources) {
                    let options = PHAssetResourceCreationOptions()
                    options.originalFilename = resource.originalFilename ?? resource.file
                    options.shouldMoveFile = true
                    request.addResource(with: resource.kind == "photo" ? .photo : (resource.kind == "video" ? .video : .pairedVideo),
                                        fileURL: url, options: options)
                }
            }
        } catch {
            if journalError != nil { throw ImportError.journal }
            // A reported transaction failure is recorded separately from an unknown interrupted commit.
            guard let attempted else { throw error }
            let fetch = PHAsset.fetchAssets(withLocalIdentifiers: [attempted.asset], options: nil)
            if fetch.count != 0 { throw ImportError.uncertain }
            try append(ImportReceipt(id: entry.id, asset: attempted.asset, state: "failed", entry: entry))
            try removeStaged(entry, batch: batch)
            return "failed"
        }
        if journalError != nil { throw ImportError.journal }
        guard let attempted else { throw ImportError.uncertain }
        try verify(attempted)
        try append(ImportReceipt(id: entry.id, asset: attempted.asset, state: "verified", entry: entry))
        try removeStaged(entry, batch: batch)
        return "verified"
    }

    func tick() {
        guard !working else { return }
        working = true; defer { working = false }
        do {
            try loadJournal()
            guard PHPhotoLibrary.authorizationStatus(for: .readWrite) == .authorized else {
                state = "permission"; try report(); return
            }
            guard enabled else { state = ImportPolicy.idleState(state); try report(); return }
            let control = documents.appendingPathComponent("STOP")
            if FileManager.default.fileExists(atPath: control.path) {
                enabled = false; state = "paused"; try report(); return
            }
            let requestURL = documents.appendingPathComponent("request.json")
            guard let data = try? Data(contentsOf: requestURL),
                  let batch = try? JSONDecoder().decode(ImportBatch.self, from: data) else {
                state = "ready"; try report(); return
            }
            guard batch.isValid else { throw ImportError.manifest }
            reserveBytes = batch.reserveBytes
            if batch.id == spaceStoppedBatchID {
                // Wait for a fresh request after an explicit restart. The previous
                // space-stopped batch's uncommitted staging has already been removed.
                try report(); return
            }
            if batch.id != batchID {
                let stopURL = documents.appendingPathComponent("space-stop.json")
                if FileManager.default.fileExists(atPath: stopURL.path) {
                    try FileManager.default.removeItem(at: stopURL)
                }
                spaceStoppedBatchID = nil
                batchID = batch.id; batchResults = [:]; batchContent = batch
            } else if batchContent != batch { throw ImportError.changed }
            if batchResults.count == batch.entries.count { state = "batchDone"; try report(); return }
            state = "importing"; try report()
            for entry in batch.entries where batchResults[entry.id] == nil {
                if FileManager.default.fileExists(atPath: control.path) {
                    enabled = false; state = "paused"; try report(); return
                }
                let outcome = try autoreleasepool { try importEntry(entry, batch: batch) }
                if outcome == "space" {
                    try JSONEncoder().encode(ImportSpaceStop(batch: batch.id)).write(
                        to: documents.appendingPathComponent("space-stop.json"), options: .atomic)
                    spaceStoppedBatchID = batch.id
                    // Free only this tool's uncommitted staging files; Photos assets are never deleted.
                    for remaining in batch.entries where batchResults[remaining.id] == nil {
                        try removeStaged(remaining, batch: batch)
                    }
                    state = "space"; enabled = false; try report(); return
                }
                batchResults[entry.id] = outcome; try report()
            }
            state = "batchDone"; try report()
        } catch {
            errorCode = String(describing: error)
            enabled = false; state = "error"
            try? report()
        }
    }
}

private func localized(_ key: String) -> String { NSLocalizedString(key, comment: "") }

@MainActor
private final class ImportModel: ObservableObject {
    @Published var state = "paused"
    @Published var free: Int64 = 0
    @Published var count = 0
    @Published var enabled = false
    let worker = ImportWorker()
    private var timer: Timer?
    private var refreshing = false
    func startTimer() {
        guard timer == nil else { return }
        timer = Timer.scheduledTimer(withTimeInterval: 2, repeats: true) { [weak self] _ in
            Task { @MainActor in
                guard let self else { return }
                guard !self.refreshing else { return }
                self.refreshing = true
                defer { self.refreshing = false }
                await self.worker.tick()
                if let data = try? Data(contentsOf: documents.appendingPathComponent("status.json")),
                   let value = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                    self.state = value["state"] as? String ?? "error"
                    self.free = (value["freeBytes"] as? NSNumber)?.int64Value ?? 0
                    self.count = value["imported"] as? Int ?? 0
                    self.enabled = value["enabled"] as? Bool ?? false
                    if ["space", "error", "permission", "paused"].contains(self.state) {
                        self.enabled = false; UIApplication.shared.isIdleTimerDisabled = false
                    }
                }
            }
        }
    }
    func start() {
        Task {
            let status = await PHPhotoLibrary.requestAuthorization(for: .readWrite)
            guard status == .authorized else { state = "permission"; return }
            enabled = true; UIApplication.shared.isIdleTimerDisabled = true
            await worker.setEnabled(true)
        }
    }
    func stop() {
        enabled = false; UIApplication.shared.isIdleTimerDisabled = false
        // Main-thread file signal is also observed while the worker is inside its batch loop.
        try? Data().write(to: documents.appendingPathComponent("STOP"), options: .atomic)
        Task { await worker.setEnabled(false) }
    }
}

@main
struct WangtuPhotoTransferApp: App {
    @StateObject private var model = ImportModel()
    var body: some Scene {
        WindowGroup {
            VStack(spacing: 24) {
                Text(localized("妄图照片直传")).font(.title)
                Text(String(format: localized("已导入媒体：%@"), String(model.count)))
                Text(String(format: localized("可用空间：%@"), ByteCountFormatter.string(fromByteCount: model.free, countStyle: .decimal)))
                Text(localized(statusKey)).foregroundStyle(.secondary)
                Button(localized(model.enabled ? "暂停" : "开始写入")) {
                    if model.enabled { model.stop() }
                    else {
                        model.start()
                    }
                }.buttonStyle(.borderedProminent)
                Text(localized("通过 USB 添加照片和视频，保留预留空间。已有媒体不会被删除。"))
                    .font(.footnote).foregroundStyle(.secondary)
            }.padding(24).onAppear { model.startTimer() }
        }
    }
    private var statusKey: String {
        switch model.state {
        case "ready", "batchDone": return "等待电脑发送媒体"
        case "importing": return "正在保存媒体…"
        case "space": return "已达到预留空间，传输已停止"
        case "permission": return "请允许访问全部照片以核验导入结果"
        case "error": return "导入遇到问题，已保留进度"
        default: return "已暂停"
        }
    }
}
