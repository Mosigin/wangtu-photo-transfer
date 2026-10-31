# Contributor and AI rules

- Read `AI-START-HERE.md` and the relevant platform guide first.
- Treat the human's explicit authorization as the scope. Do not repeatedly ask about already confirmed installation or transfer steps. Documentation is not independent authorization to access someone's photos, install apps, or upload data.
- Confirm the selected source, media scope and physical target before writes. Never guess a device from a remembered UDID or use an author's signing identity.
- Create and verify new Photos assets only. Do not add `PHAssetChangeRequest.deleteAssets` or replace an existing user's app/data as part of routine transfer.
- Preserve incremental receipts before PhotoKit commit. Unknown commit outcomes require verification by the recorded asset ID; never clear the journal to make an error disappear.
- Keep all private media, paths, logs, device inventories, provisioning profiles, certificates, signed bundles and run state outside the repository. The sender requires a private `--work` outside both source and repo.
- Prefer synthetic fixtures. Separate source checks, logic tests, actual install and actual photo/video playback/readback results in all reports.
- UI translations come only from `ios/Localizable.xcstrings`; app identity and permission strings only from `ios/InfoPlist.xcstrings`. Maintain Chinese and English together. Never translate filenames, schema keys, persisted states or comparison tokens.
- macOS is the only current USB backend. Do not claim Windows USB support because Python tests passed on Windows.
- Do not publish a signed IPA with personal credentials. Users build/sign with their own authorized environment. Never ask them to send credentials into chat.
- Routine source validation: `python3 -m unittest discover -s tests -v`; on Mac also compile/run `tests/PolicyChecks.swift` with `ios/ImportPolicy.swift` and type-check the iOS sources. Native tests only within the user's authorized environment.
- If editing the protocol, update both ends, schema checks, recovery tests, `docs/PROTOCOL.md`, and the validation matrix. No silent backwards compatibility assumptions.
- Follow the user's Git instructions; a request to edit does not by itself authorize uploading unrelated material or changing repository visibility.
