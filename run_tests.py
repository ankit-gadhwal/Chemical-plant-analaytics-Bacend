"""
run_tests.py
============
Pre-deployment test runner script.

Usage:
    python run_tests.py              # Run all backend tests
    python run_tests.py --frontend   # Run backend + frontend E2E tests
    python run_tests.py --fast       # Run only fast (no I/O) tests via markers
"""
import subprocess
import sys
import argparse


def run(cmd: list[str]) -> int:
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run pre-deployment tests")
    parser.add_argument("--frontend", action="store_true", help="Include Playwright frontend tests")
    parser.add_argument("--fast", action="store_true", help="Skip slow integration tests")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    args = parser.parse_args()

    base_cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]

    if args.html:
        base_cmd += ["--html=tests/report.html", "--self-contained-html"]

    if args.fast:
        base_cmd += ["-m", "not frontend"]

    # ── Backend tests ──────────────────────────────────────────────────────
    backend_cmd = base_cmd + [
        "tests/test_auth.py",
        "tests/test_datasets.py",
        "tests/test_equipment.py",
        "tests/test_documents.py",
        "tests/test_chatbot.py",
    ]
    code = run(backend_cmd)

    # ── Frontend tests (optional) ──────────────────────────────────────────
    if args.frontend:
        frontend_cmd = base_cmd + ["tests/test_frontend.py", "--base-url=http://localhost:8000"]
        fe_code = run(frontend_cmd)
        code = code or fe_code

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    if code == 0:
        print("[SUCCESS] All tests PASSED - safe to deploy!")
    else:
        print("[FAILED] Some tests FAILED - check output above.")
    print("=" * 60)
    sys.exit(code)


if __name__ == "__main__":
    main()
