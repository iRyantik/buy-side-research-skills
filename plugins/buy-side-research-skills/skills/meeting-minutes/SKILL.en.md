---
name: meeting-minutes
description: Turn raw voice-transcribed meeting notes into structured research minutes with corrected names, background context, and RAG-verified claims.
---

# Meeting Minutes

Convert raw voice-transcribed meeting notes into structured, traceable, verifiable research minutes.

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

## Philosophy

Voice-to-text transcripts of sell-side/buy-side calls, industry surveys, and expert interviews have three fatal flaws:
1. **Names are wrong** — company names, personal names, product names, and technical jargon get mangled by ASR
2. **No context** — speakers assume the audience has background knowledge; readers don't
3. **Claims unverified** — numbers, customer relationships, and order data are scattered throughout with zero verification

This skill does three things: **correct → contextualize → attach sources**. The output is not "meeting minutes." It's a map of what's credible, what needs checking, and what to discard.

Failure mode: after reading the output, the reader still can't tell which claims have sources, which are the speaker's opinion alone, and which companies were even mentioned.

## Research Runtime Capsule

- Hook-enforced rules (source boundary, structure floor, table render) live in workspace hooks.
- Shared runtime baseline: `references/policy/research-policy-baseline.md` + workspace `CLAUDE.md`.
- **Data pipeline**: Does not invoke financial-data. Reuses existing workspace `_cache/`, teach-in, and quickread artifacts for background context.
- **RAG chain**: Reuses existing fallback — WebSearch → WebFetch → Playwright → curl → [UNVERIFIED]. Key claims mandatory Tier 2; general claims Tier 1 minimum.
- Sub-agent outputs: evidence_cards_only; main agent synthesizes, deduplicates, scores, tiers, and ranks.

## Triggers

- "Structure this meeting transcript"
- "Fix the ASR errors in this call transcript"
- "What's worth checking in this call?"
- "Clean up and verify this expert interview"
- "Turn this transcript into structured notes"
- User pastes a raw voice-to-text transcript along with a request to structure it

## Input Clarification

| Dimension | Meaning | Default |
|---|---|---|
| **Raw transcript** | Voice-to-text output file or pasted text | Use as-is |
| **Meeting type** | Sell-side call / buy-side call / industry survey / expert interview / company IR | Mark "Meeting type not specified" if unknown |
| **Industry / Company** | Primary industry and companies discussed | Infer from text; mark [TO CONFIRM] if uncertain |
| **Date** | Date the meeting took place | Use today's date + [TO CONFIRM] if unknown |

## Execution Flow

### Phase 1: Clean & Correct

**Step 1: Fix transcription errors**
- Cross-reference with existing teach-in/quickread artifacts in the workspace for matching industry terms and company names
- Check `references/company-name-alias.yaml` — the common ASR error lookup table (57 entries, covering optical module equipment, semiconductor equipment, AI/datacenter companies, and general technical terms)
- Fix obvious ASR errors (especially critical in mixed Chinese/English transcripts)
- Always preserve the original text alongside corrections — readers must be able to judge whether the correction is reasonable

**Step 2: Extract structured entities**
- List every company / product / customer / project mentioned in the call
- Produce a **name correction table** — raw transcript text → corrected name + ticker

### Phase 2: Extract & Classify Claims

**Step 3: Extract all verifiable claims**

| Classification | Examples | Verification Priority |
|---|---|---|
| **Key claims** (market share, customer relationships, order/revenue data, pricing/ASP, capacity/output, M&A/partnerships) | "Market share jumped from 15%→40%" "Deep cooperation with Huawei" "Keysight lead time now 6 months" | **Mandatory Tier 2** (must attempt Playwright verification) |
| **General claims** (industry trends, technology roadmap, competitive landscape qualitative statements, timelines) | "1.6T is the practical limit of pluggable optics" "Per-lane speed increase drives the upgrade cycle" | Tier 1 sufficient (WebFetch / WebSearch) |
| **Opinions / Judgments** (speaker's investment views, valuation opinions, revenue forecasts) | "Robotechnik market cap could surpass Semight" "Revenue could reach 10bn next year" | Do not verify — retain as "Speaker's view" with original labeling |

**Step 4: Claim verification (RAG Fallback Chain)**

Reuse the existing priority and degradation logic:

```
Tier 0: workspace _cache/ — teach-in / quickread / actuals → cite directly
Tier 1: WebSearch → WebFetch(url) → extract original text from page
Tier 2: Playwright MCP browser_navigate + browser_snapshot → extract verified text
Tier 3: curl -sL url → extract body text (raw HTML fallback)
Tier 4: [UNVERIFIED] — honest degradation, claim cannot be confirmed
```

- **Key claims**: Tier 2 is mandatory. Only mark [UNVERIFIED] if BOTH Tier 1 AND Tier 2 fail completely.
- **General claims**: Tier 1 is sufficient. Mark [UNVERIFIED] on failure.
- **Opinions**: Never verify. Label as "Speaker's view" and move on.

### Phase 3: Add Context

**Step 5: Supplement company and industry background**

For each company mentioned, pull background from these sources (read-only — cite existing material, never fabricate):
- `industry/<industry>/companies/<ticker>/_cache/` → actuals-resolved.json, quickread artifacts
- `industry/<industry>/` → teach-in, industry-landscape artifacts
- No existing cache available → WebSearch for core identifying information (≤ 3 sentences per company)

**Step 6: Supplement technical / industry background**

If the meeting involves technical concepts (e.g., CPO, PAM4, interposer, optical engine), cite existing teach-in / mechanism-insight artifacts for explanation. If none exist, write 1–2 sentences of essential context.

### Phase 4: Output

Follow the fixed output structure below. Each section is mandatory.

## Output Structure

```markdown
# <Meeting Topic> — Meeting Minutes

> <Date> | Source: <Meeting Type> | Coverage: <Industry / Companies>

## 1. Key Takeaways

4–8 items. One sentence each — what new information did this meeting actually surface?
Must clearly distinguish: **source-backed claims** vs. **speaker's view, not independently verified**.

## 2. Name Correction Table

| Transcript (raw) | Corrected Name | Ticker | Notes |
|---|---|---|---|

## 3. Claim Verification

### Key Claims (Tier 2 Verified)

| # | Claim | Category | Source | Method | Status |
|---|---|---|---|---|---|
| C1 | <original claim> | Market share / Customer / Order / Price | [S1](url) | Playwright ✅ | Verified |
| C2 | <original claim> | Customer relationship | — | WebFetch ❌ Playwright ❌ | [UNVERIFIED] |

### General Claims

| # | Claim | Category | Source | Status |
|---|---|---|---|---|
| I1 | <original claim> | Industry trend | [I1](url) | Verified |

### Speaker Opinions (Unverified)

- Opinion 1
- Opinion 2

## 4. Company Background

| Company | Ticker | Core Business | Relevant Positioning (how it relates to this meeting's topic) |
|---|---|---|---|

## 5. Technical / Industry Background

1–3 sentence explanations of key technical concepts mentioned in the call.
Cite existing teach-in / mechanism-insight artifacts where available.

## 6. Follow-Up Questions

- Specific, verifiable next-step question 1
- Specific, verifiable next-step question 2

## Resources

- [S1](url) — source description
- [I1](url) — source description
```

## Artifact / Save Policy

Save to the industry topic directory:
```
industry/<industry>/YYYY-MM-DD-call-summary-<qualifier>.md
```

- If the industry path is unclear → agent auto-creates directory per policy baseline §11.
- Qualifier: use the meeting topic or host institution (e.g., `optical-test-equipment`, `citi-2026-outlook`).

## Workflow Links

| Scenario | Next Step |
|---|---|
| A specific claim from the meeting needs deep verification | `/information-impact <claim>` |
| A newly mentioned company needs a first pass | `/stock-quickread <ticker>` |
| The meeting's industry thesis or technical claims need validation | `/mechanism-insight` or `/industry-landscape` |
| Insights from the meeting are worth preserving as earned knowledge | `/research-journal` |

## Anti-Patterns

### Correction
- ❌ Correcting terms without preserving the original text — readers can't judge whether the correction is reasonable
- ❌ Guessing company names — mark as `[TO CONFIRM]` when uncertain
- ❌ Treating the speaker's shorthand as a separate company (e.g., "K" used throughout a call → must note it means Keysight)

### Verification
- ❌ Key claims (market share / customer relationship / order data) stopped at Tier 1 — must attempt Tier 2
- ❌ Using WebSearch snippets as the source — must open and read the actual page
- ❌ Fabricating source URLs — never guess a URL
- ❌ Conflicting sources left unmarked — must explicitly note "Source A states X, Source B states Y"

### Output
- ❌ Presenting speaker opinion as fact ("Revenue 10bn" vs. "Speaker believes revenue could reach 10bn")
- ❌ Pure chronological transcription — no prioritization, no actionable guidance for the researcher
- ❌ Missing the name correction table — the single most important section for a transcript full of ASR errors
- ❌ Fabricating company introductions in the background section — must cite existing cache or web source
- ❌ Publishing sensitive content ("please don't record this," "not yet public," "embargoed") without flagging or redaction

## Word Count

- Standard minutes: 2,000–4,000 characters (including tables and source links)
- < 1,500 characters: insufficient claim extraction or verification — go back to Phase 2
- > 6,000 characters: doing `information-impact` or `industry-landscape` work — split into separate artifacts

## Boundaries with Adjacent Skills

| | meeting-minutes | information-impact | research-journal |
|---|---|---|---|
| **Entry** | Full meeting transcript | Single claim / rumor | Earned insight |
| **Question** | What was said, and what's credible? | Is this specific claim true? | What did I learn? |
| **Depth** | Broad & shallow — extract all claims + attach sources | Deep single-item — deliver a verdict | Capture insight only |
| **Verification** | Key claims Tier 2, general claims Tier 1 | Every claim runs the full fallback chain | No verification |
| **Artifact length** | 2,000–4,000 chars | 300–700 chars | 100–500 chars |
