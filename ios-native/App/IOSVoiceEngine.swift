import Foundation
import AVFoundation
import SherpaOnnx

final class IOSVoiceEngine {
    static let shared = IOSVoiceEngine()

    private let queue = DispatchQueue(label: "com.crashen.ashenvoice.ios-tts", qos: .userInitiated)
    private var kittenTTS: SherpaOnnxOfflineTtsWrapper?
    private var piperTTS: SherpaOnnxOfflineTtsWrapper?
    private var zipVoiceTTS: SherpaOnnxOfflineTtsWrapper?

    private init() {}

    private var modelRoot: URL {
        guard let root = Bundle.main.resourceURL?.appendingPathComponent("Models", isDirectory: true) else {
            return URL(fileURLWithPath: "/missing-models")
        }
        return root
    }

    private var supportRoot: URL {
        let fm = FileManager.default
        let base = fm.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let dir = base.appendingPathComponent("AshenVoiceStudio", isDirectory: true)
        try? fm.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    func handle(command: String, args: [String: Any]) async throws -> [String: Any] {
        switch command {
        case "native_tts":
            let request = args["request"] as? [String: Any] ?? [:]
            let op = (request["op"] as? String ?? "synthesize").lowercased()
            if op == "status" { return status() }
            if op == "reset" {
                reset()
                return ["ok": true]
            }
            return try await synthesize(request: request)

        case "reset_native_tts":
            reset()
            return ["ok": true]

        case "native_voice_designer_status":
            return [
                "ok": true,
                "available": false,
                "platform": "ios",
                "reason": "Parler Voice Designer is desktop-only in this build."
            ]

        case "native_voice_design":
            throw NSError(
                domain: "AshenVoiceIOS",
                code: 40,
                userInfo: [NSLocalizedDescriptionKey: "Parler Voice Designer is desktop-only. Use the designed voice on iPhone after it has been saved as a character reference."]
            )

        default:
            throw NSError(
                domain: "AshenVoiceIOS",
                code: 404,
                userInfo: [NSLocalizedDescriptionKey: "Unknown native command: \(command)"]
            )
        }
    }

    private func status() -> [String: Any] {
        let kitten = modelRoot.appendingPathComponent("kitten-nano-en-v0_8-int8/model.int8.onnx").path
        let piper = modelRoot.appendingPathComponent("vits-piper-en_US-lessac-medium/en_US-lessac-medium.onnx").path
        let zipEncoder = modelRoot.appendingPathComponent("sherpa-onnx-zipvoice-distill-int8-zh-en-emilia/encoder.int8.onnx").path
        let zipVocoder = modelRoot.appendingPathComponent("vocos_24khz.onnx").path
        let fm = FileManager.default

        return [
            "ok": true,
            "platform": "ios",
            "engines": [
                "kitten": ["available": fm.fileExists(atPath: kitten), "label": "KittenTTS iPhone"],
                "piper": ["available": fm.fileExists(atPath: piper), "label": "Piper iPhone"],
                "lux": ["available": fm.fileExists(atPath: zipEncoder) && fm.fileExists(atPath: zipVocoder), "label": "ZipVoice Clone"]
            ]
        ]
    }

    private func reset() {
        queue.sync {
            kittenTTS = nil
            piperTTS = nil
            zipVoiceTTS = nil
        }
    }

    private func synthesize(request: [String: Any]) async throws -> [String: Any] {
        try await withCheckedThrowingContinuation { continuation in
            queue.async { [self] in
                do {
                    let value = try synthesizeSync(request: request)
                    continuation.resume(returning: value)
                } catch {
                    continuation.resume(throwing: error)
                }
            }
        }
    }

    private func synthesizeSync(request: [String: Any]) throws -> [String: Any] {
        let engine = (request["engine"] as? String ?? "kitten").lowercased()
        let text = (request["text"] as? String ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { throw voiceError("No text was provided for synthesis.") }

        var config = SherpaOnnxGenerationConfigSwift()
        config.speed = Float(number(request["speed"], fallback: 1.0))
        config.silenceScale = 0.2

        let tts: SherpaOnnxOfflineTtsWrapper
        switch engine {
        case "kitten":
            tts = try kitten()
            config.sid = kittenSpeakerID(request["voice"] as? String)

        case "piper":
            tts = try piper()
            config.sid = 0

        case "lux":
            // Cross-platform project files call the locked clone route `lux`.
            // On iOS the route is implemented by sherpa-onnx ZipVoice, entirely on-device.
            tts = try zipVoice()
            let reference = try persistedReference(request: request)
            config.referenceAudio = reference.samples
            config.referenceSampleRate = reference.sampleRate
            config.referenceText = reference.text
            config.numSteps = max(2, min(8, Int(number(request["lux_steps"], fallback: 4))))
            config.extra = ["min_char_in_sentence": "10"]

        default:
            throw voiceError("The iPhone native build does not recognize engine '\(engine)'.")
        }

        let audio = tts.generateWithConfig(text: text, config: config, callback: nil, arg: nil)
        let temp = FileManager.default.temporaryDirectory
            .appendingPathComponent("ashen-\(UUID().uuidString).wav")
        defer { try? FileManager.default.removeItem(at: temp) }

        guard audio.save(filename: temp.path) == 1 else {
            throw voiceError("The native iPhone engine generated audio but could not save its WAV output.")
        }
        let data = try Data(contentsOf: temp)
        guard !data.isEmpty else { throw voiceError("The native iPhone engine returned an empty WAV.") }

        return [
            "ok": true,
            "platform": "ios",
            "engine": engine == "lux" ? "zipvoice" : engine,
            "wav_b64": data.base64EncodedString()
        ]
    }

    private func kitten() throws -> SherpaOnnxOfflineTtsWrapper {
        if let kittenTTS { return kittenTTS }
        let dir = modelRoot.appendingPathComponent("kitten-nano-en-v0_8-int8", isDirectory: true)
        let model = dir.appendingPathComponent("model.int8.onnx").path
        try requireFile(model, engine: "KittenTTS")

        let kitten = sherpaOnnxOfflineTtsKittenModelConfig(
            model: model,
            voices: dir.appendingPathComponent("voices.bin").path,
            tokens: dir.appendingPathComponent("tokens.txt").path,
            dataDir: dir.appendingPathComponent("espeak-ng-data", isDirectory: true).path
        )
        let modelConfig = sherpaOnnxOfflineTtsModelConfig(
            numThreads: 2,
            debug: 0,
            provider: "cpu",
            kitten: kitten
        )
        var ttsConfig = sherpaOnnxOfflineTtsConfig(model: modelConfig)
        let tts = SherpaOnnxOfflineTtsWrapper(config: &ttsConfig)
        kittenTTS = tts
        return tts
    }

    private func piper() throws -> SherpaOnnxOfflineTtsWrapper {
        if let piperTTS { return piperTTS }
        let dir = modelRoot.appendingPathComponent("vits-piper-en_US-lessac-medium", isDirectory: true)
        let model = dir.appendingPathComponent("en_US-lessac-medium.onnx").path
        try requireFile(model, engine: "Piper")

        let vits = sherpaOnnxOfflineTtsVitsModelConfig(
            model: model,
            lexicon: "",
            tokens: dir.appendingPathComponent("tokens.txt").path,
            dataDir: dir.appendingPathComponent("espeak-ng-data", isDirectory: true).path
        )
        let modelConfig = sherpaOnnxOfflineTtsModelConfig(vits: vits, numThreads: 2, debug: 0, provider: "cpu")
        var ttsConfig = sherpaOnnxOfflineTtsConfig(model: modelConfig)
        let tts = SherpaOnnxOfflineTtsWrapper(config: &ttsConfig)
        piperTTS = tts
        return tts
    }

    private func zipVoice() throws -> SherpaOnnxOfflineTtsWrapper {
        if let zipVoiceTTS { return zipVoiceTTS }
        let dir = modelRoot.appendingPathComponent("sherpa-onnx-zipvoice-distill-int8-zh-en-emilia", isDirectory: true)
        let encoder = dir.appendingPathComponent("encoder.int8.onnx").path
        try requireFile(encoder, engine: "ZipVoice")
        let vocoder = modelRoot.appendingPathComponent("vocos_24khz.onnx").path
        try requireFile(vocoder, engine: "ZipVoice vocoder")

        let zipvoice = sherpaOnnxOfflineTtsZipvoiceModelConfig(
            tokens: dir.appendingPathComponent("tokens.txt").path,
            encoder: encoder,
            decoder: dir.appendingPathComponent("decoder.int8.onnx").path,
            vocoder: vocoder,
            dataDir: dir.appendingPathComponent("espeak-ng-data", isDirectory: true).path,
            lexicon: dir.appendingPathComponent("lexicon.txt").path
        )
        let modelConfig = sherpaOnnxOfflineTtsModelConfig(numThreads: 2, debug: 0, provider: "cpu", zipvoice: zipvoice)
        var ttsConfig = sherpaOnnxOfflineTtsConfig(model: modelConfig)
        let tts = SherpaOnnxOfflineTtsWrapper(config: &ttsConfig)
        zipVoiceTTS = tts
        return tts
    }

    private func kittenSpeakerID(_ voice: String?) -> Int {
        // sherpa-onnx Kitten v0.8 exposes eight speaker embeddings. Keep Ashen's
        // existing friendly names stable while mapping them to native speaker IDs.
        switch (voice ?? "Jasper").lowercased() {
        case "bella": return 1
        case "jasper": return 0
        case "luna": return 3
        case "bruno": return 2
        case "rosie": return 5
        case "hugo": return 4
        case "kiki": return 7
        case "leo": return 6
        default: return abs((voice ?? "").hashValue) % 8
        }
    }

    private struct ReferencePrompt {
        let samples: [Float]
        let sampleRate: Int
        let text: String
    }

    private func persistedReference(request: [String: Any]) throws -> ReferencePrompt {
        let characterID = safeName(request["character_id"] as? String ?? "character")
        let dir = supportRoot.appendingPathComponent("VoiceReferences", isDirectory: true)
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)

        let suppliedText = (request["reference_text"] as? String ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        let suppliedName = request["reference_name"] as? String ?? "reference.wav"
        let ext = URL(fileURLWithPath: suppliedName).pathExtension.isEmpty ? "wav" : URL(fileURLWithPath: suppliedName).pathExtension
        let audioURL = dir.appendingPathComponent("\(characterID).\(ext)")
        let textURL = dir.appendingPathComponent("\(characterID).txt")

        if let b64 = request["reference_audio_b64"] as? String, let data = Data(base64Encoded: b64), !data.isEmpty {
            // Remove older formats for this character so we do not accidentally use a stale reference.
            if let files = try? FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil) {
                for file in files where file.deletingPathExtension().lastPathComponent == characterID && file.pathExtension != "txt" {
                    try? FileManager.default.removeItem(at: file)
                }
            }
            try data.write(to: audioURL, options: .atomic)
        }
        if !suppliedText.isEmpty {
            try suppliedText.write(to: textURL, atomically: true, encoding: .utf8)
        }

        let storedText = (try? String(contentsOf: textURL, encoding: .utf8))?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        guard !storedText.isEmpty else {
            throw voiceError("ZipVoice needs the exact transcript of \(characterID)'s reference recording.")
        }

        let candidate: URL
        if FileManager.default.fileExists(atPath: audioURL.path) {
            candidate = audioURL
        } else {
            let files = (try? FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil)) ?? []
            guard let found = files.first(where: { $0.deletingPathExtension().lastPathComponent == characterID && $0.pathExtension != "txt" }) else {
                throw voiceError("ZipVoice needs a reference recording for this character.")
            }
            candidate = found
        }

        let decoded = try decodeAudio(candidate)
        return ReferencePrompt(samples: decoded.samples, sampleRate: decoded.sampleRate, text: storedText)
    }

    private func decodeAudio(_ url: URL) throws -> (samples: [Float], sampleRate: Int) {
        let file = try AVAudioFile(forReading: url)
        let format = file.processingFormat
        guard let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: AVAudioFrameCount(file.length)) else {
            throw voiceError("Could not allocate a buffer for the reference recording.")
        }
        try file.read(into: buffer)
        guard let channels = buffer.floatChannelData else {
            throw voiceError("Reference recording could not be decoded to floating-point PCM.")
        }
        let frames = Int(buffer.frameLength)
        let channelCount = Int(format.channelCount)
        guard frames > 0, channelCount > 0 else { throw voiceError("Reference recording is empty.") }

        var mono = [Float](repeating: 0, count: frames)
        let divisor = Float(channelCount)
        for channel in 0..<channelCount {
            for i in 0..<frames { mono[i] += channels[channel][i] / divisor }
        }
        return (mono, Int(format.sampleRate.rounded()))
    }

    private func number(_ value: Any?, fallback: Double) -> Double {
        if let n = value as? NSNumber { return n.doubleValue }
        if let n = value as? Double { return n }
        if let n = value as? Int { return Double(n) }
        if let s = value as? String, let n = Double(s) { return n }
        return fallback
    }

    private func safeName(_ raw: String) -> String {
        let allowed = CharacterSet.alphanumerics.union(CharacterSet(charactersIn: "-_."))
        let cleaned = raw.unicodeScalars.map { allowed.contains($0) ? Character(String($0)) : "_" }
        let value = String(cleaned)
        return value.isEmpty ? "character" : value
    }

    private func requireFile(_ path: String, engine: String) throws {
        guard FileManager.default.fileExists(atPath: path) else {
            throw voiceError("\(engine) model resources are missing from this iPhone build.")
        }
    }

    private func voiceError(_ message: String) -> NSError {
        NSError(domain: "AshenVoiceIOS", code: 1, userInfo: [NSLocalizedDescriptionKey: message])
    }
}
