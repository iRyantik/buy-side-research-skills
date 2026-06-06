# Research Runtime

Workspace runtime 由 plugin release 的 `runtime/managed-assets.json` 管理。

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

公开 CLI：

```powershell
python _scripts/source-intake.py add <file> --topic <path> --category <type>
python _scripts/source-intake.py scan _inbox [--recursive]
python _scripts/financial-data.py fetch <ticker> --profile lite [--from <period> --to <period>]
python _scripts/runtime-manager.py plan|init|update|repair|verify
```

Router 是正式 `_raw/_cache` 路径和删除策略的唯一 owner。Converter 不移动、不删除、不决定路径。Hook 只提交当前运行明确创建的文件，不自动扫描整个 `_inbox`。
