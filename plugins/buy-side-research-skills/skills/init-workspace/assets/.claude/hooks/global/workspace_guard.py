"""workspace_guard hook — Python edition.
Ensures all file writes stay within the workspace and follow naming conventions.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_hook_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_hook_dir))
import _hook_common as H  # noqa: E402


FORBIDDEN_TOP_PATHS = ("screens", "peers", "quickreads", "cross-market")
TOPIC_ARTIFACT_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9\-]*\.(md|html)$')


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-path", dest="input_path", default=None)
    args = parser.parse_args()

    payload = H.get_hook_payload(args.input_path)
    if payload is None:
        sys.exit(0)

    workspace_root = H.get_workspace_root(payload)
    tool_name = H.get_tool_name(payload)

    for path in H.get_candidate_paths(payload):
        # Must be within workspace
        if not H.test_path_under(path, workspace_root):
            H.write_block(
                f"Blocked by workspace_guard: write target escapes the workspace root ({path})."
            )

        relative = H.get_relative_display_path(path, workspace_root).replace("\\", "/")

        # Forbidden legacy root paths
        if any(relative.startswith(p + "/") or relative == p for p in FORBIDDEN_TOP_PATHS):
            H.write_block(
                f"Blocked by workspace_guard: legacy root artifact paths are not allowed "
                f"({relative}). Use topics/... instead."
            )

        # Topic root file naming
        if relative.startswith("topics/") and H.test_is_topic_artifact_root_file(path, workspace_root):
            leaf = Path(path).name
            if leaf != "index.md" and not TOPIC_ARTIFACT_PATTERN.match(leaf):
                H.write_block(
                    f"Blocked by workspace_guard: topic root artifact names must be "
                    f"date-prefixed and qualifier-safe ({relative})."
                )
            if tool_name == "Write" and Path(path).exists() and leaf != "index.md":
                H.write_block(
                    f"Blocked by workspace_guard: use Edit/apply_patch for existing topic "
                    f"artifacts instead of blind Write ({relative})."
                )

    sys.exit(0)


if __name__ == "__main__":
    main()
