"""Safe CLI for local Ollama, Ollama Cloud and Amazon Bedrock."""

import argparse
import sys
from owl.runtime import run_task


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run an OWL task")
    parser.add_argument("task", help="English task for the selected model")
    parser.add_argument("--provider", choices=["ollama", "ollama-cloud", "bedrock"])
    parser.add_argument("--model", help="Override the configured model")
    parser.add_argument("--mode", choices=["assistant", "workforce"])
    args = parser.parse_args(argv)
    try:
        print(run_task(args.task, args.provider, args.model, args.mode))
    except ValueError as exc:
        parser.exit(2, f"Configuration error: {exc}\n")
    except Exception as exc:
        print(f"Execution failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
