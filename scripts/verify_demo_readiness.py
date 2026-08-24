"""Pre-Demo Automated Verification & Stack Readiness Script.

Run this script before your demo to verify that:
1. Content corpus YAML files are 100% valid.
2. Pedagogy grade band YAML files are 100% valid.
3. STT Khmer math normalizer works cleanly.
4. Golden queries routing test suite passes.
5. Frontend production bundle is compiled and ready.
"""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="backslashreplace").decode("ascii"))


def print_step(title: str):
    safe_print(f"\n==================================================")
    safe_print(f"  {title}")
    safe_print(f"==================================================")


def verify_content_corpus() -> bool:
    print_step("1. Verifying Curriculum Content Corpus (seed_data)")
    try:
        from content_service.scripts.seed_exercises import SEED_DIR, validate_files
        results = validate_files(SEED_DIR)
        ok_count = sum(1 for r in results if r.ok)
        failed_count = sum(1 for r in results if not r.ok)
        safe_print(f"Found {len(results)} exercise files: {ok_count} OK, {failed_count} Rejected.")
        for r in results:
            status = "[OK]" if r.ok else f"[REJECTED] ({r.error})"
            safe_print(f"  - {r.file}: {status}")
        return failed_count == 0
    except Exception as exc:
        safe_print(f"[FAIL] Failed to validate content corpus: {exc}")
        return False


def verify_prompt_bands() -> bool:
    print_step("2. Verifying Pedagogy Grade Band Prompt Specs")
    try:
        from pedagogy_service.app.core.prompt_manager import PROMPTS_DIR, PromptManager
        pm = PromptManager(prompts_dir=PROMPTS_DIR)
        safe_print("Loaded prompt specs for bands: grade1_3, grade4_6, grade7_9, grade10_12.")
        for grade in [2, 5, 8, 11]:
            instruction = pm.build_system_instruction(
                grade=grade,
                language="km",
                mode="student",
            )
            assert "ទន្សាយ" in instruction or "Tunsay" in instruction
            safe_print(f"  - Grade {grade}: system instruction assembled cleanly ({len(instruction)} chars)")
        return True
    except Exception as exc:
        safe_print(f"[FAIL] Failed to assemble prompt instructions: {exc}")
        return False


def verify_stt_normalizer() -> bool:
    print_step("3. Verifying STT Khmer Math Normalizer")
    try:
        from stt_service.app.core.math_notation_normalizer import normalize_spoken_math
        samples = [
            ("៥ បូក ៣", "5 + 3"),
            ("១០ ដក ៤", "10 - 4"),
            ("៦ គុណ ៧", "6 * 7"),
        ]
        for inp, expected in samples:
            res = normalize_spoken_math(inp)
            safe_print(f"  - Input normalized to '{res}' (expected: '{expected}')")
            assert expected in res or res == expected
        return True
    except Exception as exc:
        safe_print(f"[FAIL] Failed STT math normalizer test: {exc}")
        return False


def run_golden_queries() -> bool:
    print_step("4. Running Golden Queries Test Suite")
    try:
        cmd = [sys.executable, "-m", "pytest", "orchestrator/tests/test_golden_queries.py", "-q"]
        res = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True)
        if res.returncode == 0:
            safe_print("[OK] All golden query routing tests passed cleanly!")
            return True
        else:
            safe_print(f"[FAIL] Golden query tests failed:\n{res.stdout}\n{res.stderr}")
            return False
    except Exception as exc:
        safe_print(f"[FAIL] Failed to run golden queries: {exc}")
        return False


def verify_frontend_build() -> bool:
    print_step("5. Verifying Frontend Production Bundle")
    dist_dir = ROOT_DIR / "frontend_tunsay" / "dist"
    index_html = dist_dir / "index.html"
    if dist_dir.exists() and index_html.exists():
        safe_print(f"[OK] Frontend production bundle found at {dist_dir}")
        return True
    safe_print("[WARN] Frontend dist/ bundle not found. Building frontend...")
    try:
        cmd = ["npm", "run", "build"]
        res = subprocess.run(cmd, cwd=str(ROOT_DIR / "frontend_tunsay"), capture_output=True, text=True, shell=True)
        if res.returncode == 0:
            safe_print("[OK] Frontend build completed successfully!")
            return True
        else:
            safe_print(f"[FAIL] Frontend build failed:\n{res.stderr}")
            return False
    except Exception as exc:
        safe_print(f"[FAIL] Failed to build frontend: {exc}")
        return False


def main():
    safe_print("\n==================================================")
    safe_print("   TUNSAY AI - PRE-DEMO READINESS VERIFICATION")
    safe_print("==================================================")

    results = {
        "Curriculum Corpus": verify_content_corpus(),
        "Pedagogy Prompts": verify_prompt_bands(),
        "STT Math Normalizer": verify_stt_normalizer(),
        "Golden Queries Suite": run_golden_queries(),
        "Frontend Build": verify_frontend_build(),
    }

    safe_print("\n==================================================")
    safe_print("  SUMMARY RESULTS")
    safe_print("==================================================")
    all_passed = True
    for name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        safe_print(f"  {name:<25}: {status}")
        if not passed:
            all_passed = False

    safe_print("==================================================")
    if all_passed:
        safe_print("ALL PRE-DEMO CHECKS PASSED! YOUR STACK IS READY FOR DEMO!\n")
        sys.exit(0)
    else:
        safe_print("SOME CHECKS FAILED. PLEASE REVIEW LOGS ABOVE.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
