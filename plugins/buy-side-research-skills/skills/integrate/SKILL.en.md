---
name: integrate
description: Merge a whole child topic into a parent topic and update topic indexes.
---

> This is the English translation of [SKILL.md](./SKILL.md). The Chinese version is the source of truth.

# Integrate

Merge a researched child topic (e.g., a company) into a parent topic (e.g., its industry), forming an `industry/<parent>/companies/<child>/` hierarchy, and update bidirectional `index.md` references.

This is an operations skill. It does not write research conclusions and does not perform cross-topic analysis.

## Philosophy

Research tends to fragment: you first study an industry, then study a company within it — two topics that are independent but logically in a parent-child relationship. `integrate` encodes this relationship into the directory structure, so that subsequent research naturally discovers the parent topic's industry cache and the child topic's company cache.

## Responsibility Boundary

Responsible for:
- Moving the entire child topic directory under the parent topic
- Updating the Sub-topics / Related topics section of the parent `index.md`
- Updating the child `index.md` to record the parent reference
- Reporting a merge summary

Not responsible for:
- Writing research conclusions
- Modifying session content within the child topic
- Deleting or merging `index.md` files
- Performing cross-topic analysis or comparison

## Triggers and Inputs

Trigger phrases:
- "merge ge-aerospace into aerospace"
- "merge GE research under aerospace"
- "integrate these two topics"
- "merge these two topics"

Input requirements:

| Input | Purpose |
|---|---|
| `parent_slug` | Parent topic slug (e.g., `aerospace`) |
| `child_slug` | Child topic slug (e.g., `ge-aerospace`) |
| `workspace_path` | Research workspace root directory |

## Execution Mode

### Merge

1. Verify parent exists: `industry/<parent>/index.md`
2. Verify child exists: `industry/<child>/index.md`
3. Check for conflict: whether `industry/<parent>/companies/<child>/` already exists
4. Execute move: `industry/<child>/` → `industry/<parent>/companies/<child>/`
5. Update parent `index.md`: append `## Sub-topics` section with link to child
6. Update child `index.md`: append `**Parent topic**: [parent]` reference
7. Output merge summary

## Output Contract

```markdown
## Integrate Result

**Conclusion-first**
Merged `industry/<child>/` into `industry/<parent>/companies/<child>/`

## Moved
- `industry/<child>/` → `industry/<parent>/companies/<child>/`
  - _raw files: N
  - _cache files: N
  - sessions: N

## Index Updated
- parent: `industry/<parent>/index.md` (+sub-topic link)
- child: `industry/<parent>/companies/<child>/index.md` (+parent reference)
```

## Tool Resources

- Use filesystem checks to confirm parent / child topic existence.
- Use safe move operations to place the child topic under the parent topic.
- Use text editing to update the parent and child `index.md` links.
- No dependency on external network, models, databases, or research sources.

## File Safety

- Do not delete the child's original path (it is a move, not a copy-then-delete)
- On conflict (child directory name already exists under parent) → block and prompt for manual handling
- Do not modify session artifact content inside the child topic
- Parent or child does not exist → block and prompt to create the topic first

## Failure Handling

- Parent does not exist: agent auto-creates the parent topic per policy baseline §11
- Child does not exist: block, prompt to confirm child slug
- Conflict: block, prompt that a subdirectory with the same name already exists, requires manual handling
- Cross-industry merge: prompt user for confirmation (e.g., merging a `semiconductor` company under `aerospace`)

## Workflow Integration

| Scenario | Handling |
|---|---|
| Studied an industry first, then a company, want to place company under industry | `integrate` |
| Two independent topics overlap but should not be merged | Add mutual Related topics links in `index.md` only; no integrate needed |
| Three or more topics to merge | Integrate one by one (merge two first, then merge the third) |

Artifact policy:
- `save_policy`: `none`
- `default_artifact`: `conversation-only` (filesystem operations only)
- `canonical_location`: `conversation-only`

## Safety Self-Check

- ❌ Writing research conclusions
- ❌ Deleting the original child directory (move only)
- ❌ Overwriting an existing `index.md`
- ❌ Merging topics from different industries without confirmation prompt
