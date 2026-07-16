---
name: meeting-minutes
description: Turn audio or transcripts into structured research output — briefing (external email) and qa (external Q&A transcript), bilingual optional, with layered appendix for flexible sharing.
---

# Meeting Minutes

Convert audio or raw transcripts into structured research output. Two templates: `briefing` (external email) + `qa` (external Q&A). Internal-use components (claim verification, name corrections, follow-up) sit in the appendix — skip them when sending.

English edition defaults to English output. Use `--zh` for Chinese, `--qa` for Q&A only.

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

## Principles

- **Content depth and completeness first. No length limit.**
- **State facts directly, no narrative scaffolding** — no "management kicked off by stating" or "this was the most candid moment of the call."
- **No English source quotes in Chinese output** — everything translated and woven into prose. English output may keep original phrasing.
- **No verification tags in body text** — `[UNVERIFIED]`, `[Speaker's view]` etc. only appear in the appendix Claim Verification section.

## Philosophy

Voice-to-text transcripts have three fatal flaws:
1. **Names are wrong** — companies, people, products, technical terms mangled by ASR
2. **No context** — speakers assume background knowledge; readers don't have it
3. **Claims unverified** — numbers, customer relationships, and order data scattered throughout with zero verification

This skill does three things: **correct → contextualize → attach sources**.

## Research Runtime Capsule

- Hook-enforced rules live in workspace hooks.
- Shared runtime baseline: `.references/policy/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **Data pipeline**: Does not invoke financial-data. Reuses existing workspace `.cache/`, teach-in, and quickread artifacts.
- **RAG chain**: WebSearch → WebFetch → Playwright → curl → [UNVERIFIED]. Key claims mandatory Tier 2; general claims Tier 1 minimum.
- **Transcription env**: Whisper API key + endpoint + default model configured in `init-workspace`. This skill calls `.scripts/shared/transcribe.py`.
- Sub-agent outputs: evidence_cards_only; main agent synthesizes, deduplicates, scores, tiers, and ranks.

## Triggers

- "Structure this meeting transcript"
- "Fix the ASR errors in this call transcript"
- "What's worth checking in this call?"
- "Clean up and verify this expert interview"
- Paste raw voice-to-text transcript + request to structure
- Provide audio file path directly

## Input Clarification

| Dimension | Meaning | Default |
|---|---|---|
| **Source** | Transcript text or .mp3/.m4a/.wav file | Audio → transcribe first (Step 1) |
| **Meeting type** | Sell-side / buy-side / industry survey / expert interview / company IR | Mark "unspecified" if unknown |
| **Industry / Company** | Primary industry and companies | Infer from text; mark [TO CONFIRM] if uncertain |
| **Date** | Meeting date | Today's date + [TO CONFIRM] if unknown |
| **Output language** | Default EN, `--zh` for Chinese | English |
| **Output mode** | Default --briefing, --qa for Q&A, --all for both | Briefing |

---

## Execution Flow

### Step 0: Environment Check

**Only for audio input.** Text input → skip Step 0.

Check transcription dependencies, install what's missing:

```bash
# 1. whisper deps (idempotent, skips if installed)
pip install openai-whisper requests

# 2. ffmpeg (auto-download BtbN portable if missing)
python -c "
import urllib.request, zipfile, io, shutil, os
from pathlib import Path
ff = Path('.scripts/shared/ffmpeg.exe')
if ff.exists(): exit()
print('Downloading ffmpeg...')
url = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip'
with urllib.request.urlopen(url) as r: data = r.read()
tmp = Path(os.environ.get('TEMP','/tmp')) / 'ffmpeg_install'
shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir()
with zipfile.ZipFile(io.BytesIO(data)) as z: z.extractall(tmp)
inner = next(tmp.iterdir())
shutil.copy2(inner / 'bin' / 'ffmpeg.exe', ff)
shutil.rmtree(tmp, ignore_errors=True)
print('ffmpeg ready')
"
```

**whisper API key**: Read from env vars `WHISPER_API_KEY`, `WHISPER_API_BASE`, `WHISPER_MODEL`. Prompt user if not set.

### Step 1: Audio Transcription (audio input only)

```
audio .mp3/.wav/.m4a
  ↓
① Language detection + confirmation: infer language from filename/source path/user message, then ask user "Detected audio language is X. Transcribe in X?" Run only after user confirms. No default, no guessing
  ↓
② Bitrate check: <32kbps → block, request ≥64kbps version
  ↓
③ Split (>10min trigger): ffmpeg into ≤540s chunks
  ↓
④ Transcribe: whisper-large-v3-turbo (default), verbose_json + timestamp_granularities[]=segment
  ↓
⑤ Merge: sort segments by start, shift chunk timestamps, dedup overlapping
  ↓
⑥ Save _verbatim.txt + _verbatim.json → .cache/meeting-minutes/transcripts/
```

Step 1 boundary: no text modification, no speaker diarization, no annotations. Raw material only.

### Step 2: Shared Preprocessing → Scratchpad

Output: `_scratchpad.json`, saved to `.cache/meeting-minutes/`. Language-neutral (keys in English, values in source language).

**① Term correction**: Cross-reference teach-in/quickread for matching terms. Fix obvious ASR errors. **All factual claims must be verified via WebSearch before writing to final output** — no exceptions. Verification scope:
- Company: name/ticker/listing status/industry classification/geographic presence/ownership
- Product: name/tech roadmap/iteration timeline/market position/competitive landscape
- Technical: terminology/standards/physical limits
- Financial: numbers/growth rates/margin ranges/consistency with actual disclosures
- Industry: trends/landscape/market share/supply chain
- Macro: policy/geopolitics/trade restrictions
- Ambiguous: abbreviations (CPU/CPO/GPU), homophones

Retain original text for appendix Name Corrections. Mark uncertain fixes `[TO CONFIRM]`.

**② Entity extraction**: Companies / products / customers / projects / numbers.

**③ Background injection**: Cite existing cache/teach-in/mechanism-insight (≤3 sentences per item). No existing cache → WebSearch for core info (≤3 sentences).

**④ Read chunk-by-chunk, accumulate scratchpad, verify end reached**
- Transcripts can be long (50min+, 600+ segments). **Do not skim a few segments and start writing final files.**
- Reading protocol:
  ```
  Read chunk 1 (L1-200)   → extract entities, numbers, claims, topics → write to scratchpad
  Read chunk 2 (L201-400) → same, append
  Read chunk 3 (L401-600) → same, append
  Read chunk N (L601-end) → same, confirm end is Q&A closing / thanks / ending
  ```
- **Verify end reached**: The last Read's content must not repeat the beginning (no loop hallucination), and semantically be a conclusion.
- Enter Step 3 only after scratchpad is complete. Never start writing briefing/qa without reaching the end.

**⑤ Verification log — mandatory gate**

Scratchpad must include a  field where every fact is paired with a web search URL. Step 3 entry check: if  is empty or covers <80% of entities, return to Step 2. Format: 

### Step 3: Output by Template

**Two templates: briefing + qa.** Each in the default language, optionally in the other language. Internal components embedded as appendix.

**Style rules** — the following are PROHIBITED, rewrite on violation:

| # | Prohibition | Example |
|---|---|---|
| ① | Narrative scaffolding | "Management kicked off by stating" "The analyst spent a few minutes explaining" |
| ② | English source quotes in non-English output | "the company is actually older than the United States" |
| ③ | Standalone "Key Takeaway" sections | pros ending with separate "Key Takeaway:" block |
| ④ | Isolated cross-company judgments | "Much milder than DPC Holdings" |
| ⑤ | Judgment on reader's behalf | "This is the single most important variable" "Worth watching closely" |
| ⑥ | Rhetorical metaphors | "Crown jewels" "true moat" "master of your own destiny" "like baking cupcakes" |
| ⑦ | Colloquial/evaluative phrasing | "deal is hot" "that's great for them" "a small player" "still sucks" |
| ⑧ | Meta commentary on the meeting itself | "The analyst pressed with a key question" "The analyst used a jewelry metaphor" "The analyst gave an example" |
| ⑨ | Emotional/colorful phrasing | "older than America" "insulting offers" "the most extreme proof" |
| ⑩ | Intensifying adverbs and editorial qualifiers | "far exceeds" "near-monopoly" "inevitably low" "crushing leverage" |

Allowed: Neutral attribution of analyst/speaker views ("The analyst's view is" "Management believes"), buy-side question context.

---

## Output Structure

### briefing

```
# <Meeting Topic>

> <Date> | <Meeting Type> | <Industry / Company>

## 1. <Topic 1>

<prose with embedded background>

## 2. <Topic 2>

...
## N. <Topic N>

---

## Company Profile                                         ← appendix boundary

Company-level meetings only (earnings call / IR / expert call on a single company). Industry-level meetings skip this section, go directly to Listed Companies.

Core dimensions (required):

| Dimension | Detail |
|---|---|
| Company | |
| Ticker | |
| Business | <one sentence> |
| Key Platforms / Products | |
| End Markets | |

Optional dimensions (fill if available, omit otherwise):

| Dimension | Detail |
|---|---|
| Revenue & Growth | |
| Margin Profile | |
| Key Customers | |
| Key Suppliers | |
| Competitive Position | |

If stock-quickread exists → reference it directly, do not re-search.

## Industry Context

If teach-in / industry-landscape exists → reference it directly, do not re-search.

## Listed Companies Mentioned

All listed companies mentioned in the call (excluding the main Company Profile subject). Business descriptions are detailed, 1-2 sentences with key products or market position. The last column header is contextual to the meeting topic.

| Company | Ticker | Business | <Context Column> |
|---|---|---|---|

## Technical / Industry Background

Explain key technical concepts or industry context mentioned in the call. Reference mechanism-insight / teach-in artifacts where available.

## Claim Verification

### Key Claims (Tier 2)

| # | Claim | Category | Source | Status |
|---|---|---|---|---|
| C1 | | | | |

### General Claims

| # | Claim | Category | Source | Status |
|---|---|---|---|---|

### Speaker Opinions (Unverified)

- <opinion>

## Name Corrections

| Transcript | Corrected | Ticker | Notes |
|---|---|---|---|

## Follow-Up

- <actionable item>

## Resources

- `.cache/meeting-minutes/...`
```

Appendix layers, top to bottom:
- `Company Profile` + `Listed Companies` + `Industry Context` + `Technical Background`: safe for external sharing
- `Claim Verification`: internal use, contains `[UNVERIFIED]` tags
- `Name Corrections`: internal use
- `Follow-Up`: internal use
- `Resources`: internal use, contains local paths

When emailing, stop pasting at `Claim Verification`.

### qa

```
# <Meeting Topic> — Q&A

> <Date> | <Meeting Type>

**Q1: <condensed question>**
A: <condensed answer, no filler, all data preserved>

**Q2: ...**

---

## Company Profile
...

## Claim Verification
...
```

Appendix layering same as briefing.

---

## Artifact / Save Policy

```
.cache/meeting-minutes/                        ← all hidden
├── raw/YYYY-MM-DD-<call>.mp3                  ← Step 0: original audio
├── transcripts/YYYY-MM-DD-<call>_verbatim.txt  ← Step 1: raw transcript
├── transcripts/YYYY-MM-DD-<call>_verbatim.json
└── YYYY-MM-DD-<call>_scratchpad.json           ← Step 2: preprocessing middleware

Company-level artifacts (visible):
  companies/<ticker>/
  ├── YYYY-MM-DD-<call>_briefing_en.md           ← English briefing (default)
  ├── YYYY-MM-DD-<call>_briefing_zh.md           ← Chinese briefing (optional)
  ├── YYYY-MM-DD-<call>_qa_en.md                 ← English qa (default)
  └── YYYY-MM-DD-<call>_qa_zh.md                 ← Chinese qa (optional)

Industry-level (industry panel / sell-side call):
  industry/<slug>/panorama/meeting-minutes/
  ├── YYYY-MM-DD-<topic>_briefing_en.md
  └── YYYY-MM-DD-<topic>_qa_en.md
```

- `_zh` variants only output when requested.
- When path is unclear → agent auto-creates per workspace structure.

## Workflow Links

| Scenario | Next Step |
|---|---|
| A specific claim needs deep verification | `/information-impact` |
| A newly mentioned company needs first pass | `/stock-quickread <ticker>` |
| Industry thesis or technical claims need validation | `/mechanism-insight` or `/industry-landscape` |
| Insights worth preserving as earned knowledge | `/research-journal` |

## Anti-Patterns

### Reading
- ❌ Output started before reading full transcript — must read to the end
- ❌ Guessing company names — mark `[TO CONFIRM]`
- ❌ Treating speaker's shorthand as a separate company

### Verification
- ❌ Key claims stopped at Tier 1 — must attempt Tier 2
- ❌ Using WebSearch snippets as source — must open the actual page
- ❌ Fabricating source URLs
- ❌ Empty verification_log or coverage <80% → return to Step 2
- ❌ Fact written to output without web search URL support

### Output
- ❌ "Management kicked off by stating / admitted / emphasized" narrative scaffolding — state facts directly
- ❌ Separate "Key Takeaway" callout sections — weave into prose
- ❌ Isolated cross-company judgment without context ("X is milder than Y" with no reasoning)
- ❌ Fabricating company background — must cite cache or web source
- ❌ Verification tags in body text — appendix only
- ❌ Sensitive content published without flagging
