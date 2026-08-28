"""Verify the ModelShield Phase 0 repository contract."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "README.md",
    "pyproject.toml",
    "docs/architecture.md",
    "docs/threat-model.md",
    "docs/model-lifecycle.md",
    "policies/model.yaml",
    "policies/security.yaml",
    "policies/deployment.yaml",
)
REQUIRED_DIRECTORIES = (
    "docs",
    "policies",
    "model",
    "api",
    "quality",
    "security",
    "policy",
    "controller",
    "tests/unit",
    "tests/integration",
    "tests/scenarios",
    "scripts",
)


def main() -> int:
    missing_files = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    missing_directories = [path for path in REQUIRED_DIRECTORIES if not (ROOT / path).is_dir()]

    if missing_files or missing_directories:
        print("Phase 0 verification failed.")
        if missing_files:
            print("Missing files:", ", ".join(missing_files))
        if missing_directories:
            print("Missing directories:", ", ".join(missing_directories))
        return 1

    print(f"Phase 0 verification passed: {ROOT}")
    print(f"Checked {len(REQUIRED_FILES)} files and {len(REQUIRED_DIRECTORIES)} directories.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
