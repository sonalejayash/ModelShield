"""Train the reproducible ModelShield demonstration model."""

import argparse
from pathlib import Path

from model.training import train_model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--model-version", default="v1")
    arguments = parser.parse_args()
    result = train_model(arguments.output_dir, model_version=arguments.model_version)
    print(f"trained {result.model_version}: {result.artifact_path}")
    print(f"sha256: {result.artifact_sha256}")
    print(f"metrics: {result.metrics}")


if __name__ == "__main__":
    main()