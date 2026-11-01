<p align="center"><img src="assets/logo.png" width="128" alt="Wangtu Photo Transfer icon"></p>

# Wangtu Photo Transfer · 妄图照片直传

An independent, AI-assisted developer utility for adding selected computer photos and videos to an iPhone's Photos library over USB. The phone does not need an Apple/iCloud sign-in. The Mac needs Xcode and a legitimate signing environment to install the companion app.

**Current USB backend: macOS only. Windows can run offline planning and logic tests; Windows USB transfer is not implemented.** Video support and the generalized public version still need end-to-end device validation. The underlying photo/Live import engine has been used on a real device with original-resource readback verification; that is not proof of every codec or device working.

Start with [AI-START-HERE.md](AI-START-HERE.md) and [AGENTS.md](AGENTS.md). The detailed command workflow is in [docs/MAC.md](docs/MAC.md); platform limitations are in [docs/WINDOWS.md](docs/WINDOWS.md).

## Purpose and workflow

Use this tool to add photos/videos from a readable local folder or mounted external drive to an iPhone, for example when preparing a test device. It transfers original files without transcoding. The result appears in the iPhone's system Photos app.

There are two components: a **Mac command-line sender and an iPhone receiver app**. There is no Mac graphical interface or universal pre-signed download. You can ask an AI with access to your computer to run the documented workflow:

1. Build and install the companion using your own Mac signing environment and selected iPhone.
2. Connect by USB, unlock/trust the computer, open the receiver and grant full Photos access.
3. Choose the source folder, media scope and space reserve. Run an offline plan, then a small synthetic photo/video transfer.
4. Keep the receiver in the foreground during the batch transfer. Preserve the same working directory to resume after an interruption.

The AI can check the environment, run commands and inspect receipts. The user handles phone trust, Developer Mode when required, system permissions, and checking that saved photos/videos open and play. Cloning the repository does not install an app or start a transfer.

Requirements: full Xcode compatible with the selected phone, Python 3.9+ (CI uses 3.11), iOS 17+, a USB cable, your own valid signing setup, and temporary space on both devices. The Python scripts use only the standard library. Choose a private `--work` directory outside both the source and repository.

**Windows phone testing is not needed yet:** the USB backend still needs to be implemented. After that, a Windows machine and real iPhone will be needed to test import, playback/readback, interruption recovery and space limits. Offline planning is available now; automated Windows checks do not validate USB transfer.

## Give this to your AI

> Please work with https://github.com/Mosigin/wangtu-photo-transfer . Read AI-START-HERE.md, AGENTS.md, and the platform guide. Help me add photos/videos from my selected folder to my confirmed iPhone over USB, with at least 1GB free plus processing headroom. Use my authorized installation/signing setup and let me confirm phone permissions. Run an offline plan and synthetic smoke test before real media. Verify receipts and video playback. Resume with the same ledger after errors, without clearing records or blindly re-importing. On Windows, explain that USB transfer is not implemented before attempting device commands.

## Mac quick start

```sh
git clone https://github.com/Mosigin/wangtu-photo-transfer.git
cd wangtu-photo-transfer
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

## Pause, resume and assess the result

Create a file named `STOP` inside the private working directory, or tap Pause on the phone. The current small transaction may finish first. To resume, remove that computer-side STOP file, tap Start Importing on the phone, and run the same command with the same source and working directory. Preserve the ledger and phone receipts.

On normal completion, read `summary.json`: `verified` is the verified count, `failed` the failed count, `remaining` the unprocessed count, and `freeBytes` the phone's observed remaining capacity. Check `pending` too. A space-limit stop is not a complete source import; an abnormal exit requires receipt recovery, not a success claim.

The tool does not scan the existing library for duplicates or recreate folder/album structures, favorites, hidden status or editing history. Avoid changing the source path, clearing records or reinstalling the receiver to retry an interrupted job. See the [recovery protocol](docs/PROTOCOL.md).

## Behavior and data boundaries

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
