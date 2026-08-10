from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CHECKS = (
    ("pytest", (sys.executable, "-m", "pytest", "-q")),
    (
        "ruff",
        (
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--no-cache",
            "app",
            "tests",
            "scripts",
            "apply_migration.py",
        ),
    ),
    ("pip check", (sys.executable, "-m", "pip", "check")),
)


def main() -> int:
    first_failure = 0

    for name, command in CHECKS:
        print(f"\n==> {name}", flush=True)
        result = subprocess.run(command, cwd=REPOSITORY_ROOT, check=False)
        print(f"<== {name}: exit {result.returncode}", flush=True)

        if result.returncode and not first_failure:
            first_failure = result.returncode

    return first_failure


if __name__ == "__main__":
    raise SystemExit(main())
