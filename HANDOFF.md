# HANDOFF — Ingest 工具链替换

## Goal

将 `skills/ingest` 的 Python 依赖从当前的重型方案替换为更优的工具组合，覆盖全球市场（A股、港股、日、韩、台、欧、英、美）的 filing / 原始材料处理。

## 研究结论（已确认）

### PDF 文件转换层

**最终方案：docling + PyMuPDF4LLM 双层**

- **PyMuPDF4LLM**（9.7k stars, AGPL）：文字为主的文档（transcripts、IR deck 文本页），CPU 即可，10-50x 速度优势
- **docling**（59.5k stars, MIT）：表格密集型（10-K、招股书含并格表格），258M 参数 VLM，MIT 许可证在金融机构不可替代
- **Marker**（34.9k stars, GPL-3.0）：准确度最高（FinTabNet 0.907），但 GPL 许可证对商用不友好，留作精度参考

### 结构化数据层（按市场）

| 市场 | 工具 | Stars | 状态 |
|---|---|---|---|
| A股 + 港股 | AKShare | 19.1k | 活跃（May 2026） |
| 日本 | edinet-tools | 42 | 活跃（Apr 2026） |
| 韩国 | dart-fss | 367 | 成熟（Dec 2025） |
| 欧洲 | Arelle + openesef | 201/8 | 活跃，Arelle 被 ESMA 使用 |
| 台湾 | mops-financial-api | 0 | 原型，iXBRL only |
| 英国 | 无成熟工具 | — | gap，需 Arelle DIY |
| 美股 | EdgarTools（保留） | — | 成熟 |
| 跨市场（免费） | AKShare + 各市场工具组合 | — | — |
| 跨市场（付费） | EODHD | — | 覆盖所有目标市场 |

### 要去掉的

- **Tesseract** — Claude Vision 多模态完全覆盖 OCR 场景
- **markitdown[all]** —太重，`[all]` extras 无价值
- **pdfplumber** — 保留，轻量表格数字交叉校验

### 当前 `requirements-ingest.txt` vs 目标

```text
当前：
docling, edgartools, markitdown[all], openpyxl, python-pptx, python-docx, pdfplumber, pypdf, pytesseract, Pillow

目标（待改）：
docling, edgartools, pymupdf4llm, openpyxl, python-pptx, python-docx, pdfplumber, pypdf, Pillow
# 去掉: markitdown[all], pytesseract
# 新增: pymupdf4llm
# 按市场新增（用户自行选择安装）: akshare, edinet-tools, dart-fss, openesef
```

## 当前进展

- [x] 研究完成，方案确认
- [ ] 更新 `skills/ingest/assets/requirements-ingest.txt`
- [ ] 更新 `skills/ingest/scripts/bootstrap-ingest-deps.ps1`（支持多市场可选安装）
- [ ] 更新 `skills/ingest/SKILL.md` 的工具资源描述
- [ ] 更新 `docs/architecture.md` Ingest 工具链章节
- [ ] macOS 版本 bootstrap 脚本？（当前只有 PowerShell 版本）

## 注意事项

- `pymupdf4llm` 是 AGPL v3，金融机构使用需确认合规；备选方案是用 PyMuPDF 的 MIT 子集但功能受限
- 台湾和英国的结构化数据仍是 gap，需要在 SKILL.md 中标注 `[数据来源有限]`
- 跨市场工具（AKShare 等）不应作为强制依赖——用户按覆盖市场自行选择
