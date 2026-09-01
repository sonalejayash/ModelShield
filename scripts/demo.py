"""Run the ModelShield interview demo end to end."""

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-version", default="demo-v1")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/demo"))
    arguments = parser.parse_args()
    output_dir = arguments.output_dir
    audit_path = output_dir / "audit.jsonl"

    print("ModelShield demo")
    print("1. Running deterministic release gate")
    release = _run(
        "scripts/release.py",
        "--model-version",
        arguments.model_version,
        "--output-dir",
        str(output_dir),
        "--audit-path",
        str(audit_path),
    )
    if release.returncode != 0:
        return release.returncode

    print("2. Regenerating advisory investigation from audit")
    investigation = _run("scripts/investigate_release.py", str(audit_path))
    if investigation.returncode != 0:
        return investigation.returncode

    print("3. Summarizing historical release evidence")
    history = _run("scripts/analyze_history.py", str(audit_path))
    if history.returncode != 0:
        return history.returncode

    print("Demo complete")
    return 0


def _run(script: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(ROOT / script), *arguments],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    return result


if __name__ == "__main__":
    sys.exit(main())