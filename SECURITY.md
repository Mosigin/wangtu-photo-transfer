# Data and security boundaries

This tool adds selected media using Apple's supported Photos API. It does not edit DCIM or the Photos database, delete existing library assets, or run an upload server.

Use only a device and source directory the user authorized. Full Photos permission is confirmed by the user on the phone; it is used to fetch the new assets by the importer-recorded IDs for verification. Existing library contents are not enumerated for transfer.

Keep private media, original filenames, source paths, device IDs, ledgers, build logs, signed apps, certificates, private keys and provisioning profiles outside this repository. The default ignore rules are additional protection, not proof that a `git add .` is safe.

Do not disable phone trust, signing, development-mode requirements, OS security or TLS validation to work around setup errors. Do not borrow a developer certificate or ask a user to post passwords into an issue.

If iCloud Photos is enabled by the user, Apple's system may sync imported media independently of this app. This tool does not change that setting.

Report bugs with synthetic fixtures and redacted logs. For sensitive security findings, contact the maintainer through their GitHub profile; do not put personal media, credentials or full device inventories in a public issue. There is no published guarantee of secure deletion or recovery of arbitrary existing library data.
