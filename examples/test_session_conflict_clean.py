"""Tests for session_conflict_clean.py — 5 scenarios + real-file timing.

Run:  python .cache/tests/test_session_conflict_clean.py
"""
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

HOOK_DIR = Path(r"C:\Users\yuzhe\CC research workspace\.claude\hooks\rules")
sys.path.insert(0, str(HOOK_DIR))
import session_conflict_clean as scc  # noqa: E402

T0 = time.perf_counter()
def tic(label):
    print(f"  [{time.perf_counter() - T0:7.3f}s] {label}")

def row(i, prefix="u"):
    return json.dumps({
        "type": "user",
        "uuid": f"{prefix}{i:06d}",
        "timestamp": f"2026-08-21T12:00:{i % 60:02d}.{i:03d}Z",
        "message": {"role": "user", "content": f"row {i}"},
    })

def write_rows(path, rows):
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")

def setup():
    tmp = Path(tempfile.mkdtemp(prefix="scc-test-"))
    sessions = tmp / ".sessions"
    manifests = tmp / ".sessions-manifests"
    sessions.mkdir()
    manifests.mkdir()
    return tmp, sessions, manifests

def teardown(tmp):
    shutil.rmtree(tmp, ignore_errors=True)

PASS = 0
def check(name, cond, detail=""):
    global PASS
    status = "PASS" if cond else "FAIL"
    if cond:
        PASS += 1
    print(f"  {status}: {name} {detail}")

# ── Scenario 1: subset → delete-copy ─────────────────────────────
def scenario_1(sessions, manifests):
    print("\n[1] subset copy -> delete")
    base = sessions / "11111111-1111-1111-1111-111111111111.jsonl"
    copy = sessions / "11111111-1111-1111-1111-111111111111.sync-conflict-20260821-120000-ABCDEFG.jsonl"
    rows = [row(i, "a") for i in range(1, 101)]
    write_rows(base, rows)
    write_rows(copy, rows[30:80])  # subset
    t0 = time.perf_counter()
    res = scc.process_sessions(sessions, manifests)
    dt = time.perf_counter() - t0
    check("deleted=1", res["deleted"] == 1, str(res))
    check("copy gone", not copy.exists())
    check("base intact 100 rows", len(base.read_text(encoding="utf-8").splitlines()) == 100)
    check("fast (<1s)", dt < 1.0, f"{dt:.3f}s")

# ── Scenario 2: superset → replace-base ──────────────────────────
def scenario_2(sessions, manifests):
    print("\n[2] superset copy (copy is FULLER) -> replace base")
    base = sessions / "22222222-2222-2222-2222-222222222222.jsonl"
    copy = sessions / "22222222-2222-2222-2222-222222222222.sync-conflict-20260821-120000-ABCDEFG.jsonl"
    rows = [row(i, "b") for i in range(1, 51)]
    fuller = rows + [row(100 + i, "b2") for i in range(1, 11)]  # base rows + 10 unique
    write_rows(base, rows)
    write_rows(copy, fuller)
    t0 = time.perf_counter()
    res = scc.process_sessions(sessions, manifests)
    dt = time.perf_counter() - t0
    check("replaced=1", res["replaced"] == 1, str(res))
    check("copy gone", not copy.exists())
    got = base.read_text(encoding="utf-8").splitlines()
    check("base now = 60 rows (copy content)", len(got) == 60, str(len(got)))
    check("no content loss", got == fuller, "rows differ!" if got != fuller else "")
    check("fast (<1s)", dt < 1.0, f"{dt:.3f}s")

# ── Scenario 3: mutual-unique (small) → merge ────────────────────
def scenario_3(sessions, manifests):
    print("\n[3] mutual-unique rows -> merge (small file)")
    base = sessions / "33333333-3333-3333-3333-333333333333.jsonl"
    copy = sessions / "33333333-3333-3333-3333-333333333333.sync-conflict-20260821-120000-ABCDEFG.jsonl"
    base_rows = [row(i, "c") for i in range(1, 31)]          # u000001..u000030
    copy_rows = [row(i, "c2") for i in range(31, 51)] + [row(i, "c") for i in range(20, 31)]  # 20 unique + 11 shared
    write_rows(base, base_rows)
    write_rows(copy, copy_rows)
    t0 = time.perf_counter()
    res = scc.process_sessions(sessions, manifests)
    dt = time.perf_counter() - t0
    check("merged=1", res["merged"] == 1, str(res))
    check("copy gone", not copy.exists())
    got = base.read_text(encoding="utf-8").splitlines()
    check("base = 50 unique rows", len(got) == 50, str(len(got)))
    got_uuids = {json.loads(l)["uuid"] for l in got}
    check("all 50 uuids present", len(got_uuids) == 50)
    check("merge fast (<1s)", dt < 1.0, f"{dt:.3f}s")

# ── Scenario 4: identical → delete-copy ──────────────────────────
def scenario_4(sessions, manifests):
    print("\n[4] identical -> delete-copy")
    base = sessions / "44444444-4444-4444-4444-444444444444.jsonl"
    copy = sessions / "44444444-4444-4444-4444-444444444444.sync-conflict-20260821-120000-ABCDEFG.jsonl"
    rows = [row(i, "d") for i in range(1, 21)]
    write_rows(base, rows)
    write_rows(copy, rows)
    res = scc.process_sessions(sessions, manifests)
    check("deleted=1", res["deleted"] == 1, str(res))
    check("copy gone", not copy.exists())

# ── Scenario 5: mutual-unique → merge, no size threshold ─────────
def scenario_5(sessions, manifests):
    print("\n[5] mutual-unique -> merge (no size threshold)")
    base = sessions / "55555555-5555-5555-5555-555555555555.jsonl"
    copy = sessions / "55555555-5555-5555-5555-555555555555.sync-conflict-20260821-120000-ABCDEFG.jsonl"
    base_rows = [row(i, "e") for i in range(1, 31)]
    copy_rows = [row(i, "e2") for i in range(31, 51)]  # fully unique
    write_rows(base, base_rows)
    write_rows(copy, copy_rows)
    res = scc.process_sessions(sessions, manifests)
    check("merged=1", res["merged"] == 1, str(res))
    check("copy gone", not copy.exists())
    got = base.read_text(encoding="utf-8").splitlines()
    check("base = 50 unique rows", len(got) == 50, str(len(got)))

# ── Scenario 6: active session guard ─────────────────────────────
def scenario_6(sessions, manifests):
    print("\n[6] active session -> subset copy deleted, base untouched; non-subset left")
    sid = "66666666-6666-6666-6666-666666666666"
    (manifests / "12345.json").write_text(json.dumps({"sessionId": sid}), encoding="utf-8")
    # 6a: subset copy of an ACTIVE session — safe to delete, base never rewritten
    base = sessions / f"{sid}.jsonl"
    copy = sessions / f"{sid}.sync-conflict-20260821-120000-ABCDEFG.jsonl"
    rows = [row(i, "f") for i in range(1, 11)]
    write_rows(base, rows)
    write_rows(copy, rows[3:8])  # subset
    res = scc.process_sessions(sessions, manifests)
    check("6a subset deleted=1", res["deleted"] == 1, str(res))
    check("6a copy gone", not copy.exists())
    check("6a base intact 10 rows", len(base.read_text(encoding="utf-8").splitlines()) == 10)
    # 6b: non-subset copy of an ACTIVE session — left until session ends
    sid2 = "66666666-6666-6666-6666-666666666667"
    (manifests / "12346.json").write_text(json.dumps({"sessionId": sid2}), encoding="utf-8")
    base2 = sessions / f"{sid2}.jsonl"
    copy2 = sessions / f"{sid2}.sync-conflict-20260821-120000-ABCDEFG.jsonl"
    b_rows = [row(i, "g") for i in range(1, 11)]
    c_rows = [row(i, "g2") for i in range(6, 16)]  # unique rows 11-15
    write_rows(base2, b_rows)
    write_rows(copy2, c_rows)
    res = scc.process_sessions(sessions, manifests)
    check("6b untouched", res["deleted"] == 0 and res["replaced"] == 0 and res["merged"] == 0, str(res))
    check("6b both exist", base2.exists() and copy2.exists())

# ── Real-file timing: the 228MB transcript ───────────────────────
def timing_real():
    real = Path(r"C:\Users\yuzhe\CC research workspace\.sessions\cbd158a5-741f-4b37-8d9b-4e4ce6a4c017.jsonl")
    if not real.is_file():
        print(f"\n[timing] real file not found, skipped: {real}")
        return
    size_mb = real.stat().st_size / 1e6
    print(f"\n[timing] real base file: {size_mb:.0f} MB")
    t0 = time.perf_counter()
    idx = scc._build_index(real)
    dt = time.perf_counter() - t0
    check("index built", len(idx) > 1000, f"{len(idx)} rows")
    print(f"  index build: {dt:.2f}s -> {(len(idx)/dt):,.0f} rows/s ({size_mb/dt:.0f} MB/s)")

def main():
    print(f"hook file: {HOOK_DIR / 'session_conflict_clean.py'}")
    for fn in (scenario_1, scenario_2, scenario_3, scenario_4, scenario_5, scenario_6):
        tmp, sessions, manifests = setup()
        try:
            fn(sessions, manifests)
        finally:
            teardown(tmp)
    timing_real()
    print(f"\n=== {PASS} checks passed ===")
    sys.exit(0 if PASS else 1)

if __name__ == "__main__":
    main()
