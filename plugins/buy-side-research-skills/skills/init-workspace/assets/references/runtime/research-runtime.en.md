# Research Runtime

The workspace runtime is managed by plugin release `runtime/managed-assets.json`.

```text
Agent / Playwright download
→ _scripts/source-intake.py add|scan
→ _raw/<category>/<source-id>/original.ext
→ _cache/<category>/<source-id>/document.md + source-manifest.json

_scripts/financial-data.py fetch
→ provider/source evidence pack
→ canonical facts-store.json
→ generated read-only actuals-resolved.json
→ research/model consumers
```

Public CLIs:

```powershell
python _scripts/source-intake.py add <file> --topic <path> --category <type>
python _scripts/source-intake.py scan _inbox [--recursive]
python _scripts/financial-data.py fetch <ticker> --profile lite [--from <period> --to <period>]
python _scripts/runtime-manager.py plan|init|update|repair|verify
```

The Router is the only owner of formal `_raw/_cache` paths and deletion policy. Converters never move, delete, or choose routes. Hooks submit only files explicitly created by the current run and never scan the entire `_inbox` automatically.
