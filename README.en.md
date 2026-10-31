<p align="center"><img src="assets/logo.png" width="128" alt="Wangtu Photo Transfer icon"></p>

# Wangtu Photo Transfer · 妄图照片直传

An independent, AI-assisted developer utility for adding selected computer photos and videos to an iPhone's Photos library over USB. The phone does not need an Apple/iCloud sign-in. The Mac needs Xcode and a legitimate signing environment to install the companion app.

**Current USB backend: macOS only. Windows can run offline planning and logic tests; Windows USB transfer is not implemented.** Video support and the generalized public version still need end-to-end device validation. The underlying photo/Live import engine has been used on a real device with original-resource readback verification; that is not proof of every codec or device working.

Start with [AI-START-HERE.md](AI-START-HERE.md) and [AGENTS.md](AGENTS.md). The detailed command workflow is in [docs/MAC.md](docs/MAC.md); platform limitations are in [docs/WINDOWS.md](docs/WINDOWS.md).

```sh
python3 -m unittest discover -s tests -v
python3 tools/transfer.py --list-devices
python3 tools/build.py --platform device --team YOUR_TEAM_ID \
  --bundle-id com.example.yourname.wangtu --output "$HOME/WangtuBuild"
```

The build script only prepares a project by default. After the user's installation authorization, add `--compile --allow-provisioning-updates`, then install and launch the generated app on the explicitly selected device as described in the Mac guide. The user confirms full Photos access in the phone's system prompt.

Dry-run first:

```sh
python3 tools/transfer.py --source "/path/to/media" --media all \
  --work "$HOME/WangtuRuns/first" --reserve-gb 1
```

After a synthetic smoke test, add `--device YOUR_DEVICE_ID --bundle-id com.example.yourname.wangtu --execute`. Keep the phone app in the foreground. `--media photos` and `--media videos` narrow the scope.

- Existing Photos assets and computer source files are never deleted or replaced.
- Each resource is hashed before transmission and read back from Photos for SHA-256 verification.
- Durable intent and result receipts protect interrupted commits from blind duplicate creation.
- The default free-space reserve is 1GB plus processing headroom; exact free bytes vary with system activity.
- Large videos can travel alone when the safe temporary-space budget permits.
- Recursive folders with duplicate filenames are isolated by stable transport names while preserving original resource names.
- Live Photos require an explicit manifest; matching filenames alone are not a pairing rule.
- Embedded original metadata is preserved in the bytes. Supply ISO-8601 `creationDate` with timezone in the manifest when Photos timeline dates must be set explicitly.
- No app-level cloud transport is used. If the user has system iCloud Photos enabled, iOS may independently sync newly saved assets.

Keep all media, signing files, device inventories and run ledgers out of Git. Do not distribute a personal signed IPA. See the [protocol](docs/PROTOCOL.md), [validation matrix](docs/VALIDATION.md) and [security policy](SECURITY.md).

MIT license, including the generated text-free app icon. Icon origin and prompt: [assets/LOGO.md](assets/LOGO.md).
