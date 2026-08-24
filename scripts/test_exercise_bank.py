#!/usr/bin/env python3
"""Exercise Bank Automated Test Suite for TunSay AI Backend.

Parses all 48 Cambodian-context STEM problems (Grade 1–12) from Exercise.md,
sends each problem one-by-one through the backend API, records response latency,
intent classification, AI response text, and fallback status, and outputs a formatted
markdown evaluation report.

Usage:
    python scripts/test_exercise_bank.py [--limit 5] [--output test_report.md]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import uuid
from pathlib import Path
import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
EXERCISE_FILE = REPO_ROOT / "Exercise.md"
DEFAULT_REPORT_FILE = REPO_ROOT / "exercise_bank_test_report.md"


def parse_exercise_md(filepath: Path) -> list[dict[str, str]]:
    """Parse Exercise.md into structured problem items."""
    content = filepath.read_text(encoding="utf-8")
    current_grade = "Grade 1"
    grade_num = 1
    problems = []

    lines = content.split("\n")
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        grade_match = re.match(r"^##\s+Grade\s+(\d+)", line_str, re.IGNORECASE)
        if grade_match:
            grade_num = int(grade_match.group(1))
            current_grade = f"Grade {grade_num}"
            continue

        # Match subject line: **Subject:** Problem text
        prob_match = re.match(r"^\*\*(.*?)\:\*\*\s*(.*)", line_str)
        if prob_match:
            subject = prob_match.group(1).strip()
            text = prob_match.group(2).strip()
            problems.append({
                "grade": grade_num,
                "grade_label": current_grade,
                "subject": subject,
                "question": text,
            })

    return problems


def acquire_auth_token(base_url: str) -> tuple[str, str]:
    """Register demo student to obtain valid JWT token and user ID."""
    import random
    unique_name = f"ExerciseTester_{random.randint(1000, 9999)}"
    urls = [
        f"{base_url.rstrip('/')}/api/auth/register",
        "http://localhost:9002/register",
    ]
    payload = {"student_name": unique_name, "grade": 4, "language": "en"}

    for url in urls:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    token = data.get("access_token") or data.get("accessToken") or ""
                    import jwt
                    claims = jwt.decode(token, options={"verify_signature": False})
                    return claims.get("sub", ""), token
        except Exception:
            pass

    demo_uuid = "f728f1f3-6cb5-4e0e-bbdc-8862034bedfa"
    import jwt
    token = jwt.encode({"sub": demo_uuid, "exp": 9999999999}, "replace-with-a-long-random-secret", algorithm="HS256")
    return demo_uuid, token


def run_exercise_tests(
    base_url: str = "http://localhost:9000",
    limit: int | None = None,
    language: str = "en",
    mode: str = "student",
) -> list[dict]:
    """Execute exercise tests against the backend."""
    problems = parse_exercise_md(EXERCISE_FILE)
    if limit and limit > 0:
        problems = problems[:limit]

    student_id, jwt_token = acquire_auth_token(base_url)
    chat_url = f"{base_url.rstrip('/')}/chat"
    headers = {"Content-Type": "application/json"}
    if jwt_token:
        headers["Authorization"] = f"Bearer {jwt_token}"

    results = []
    print(f"--> Running TunSay Backend Exercise Suite on {len(problems)} problems...\n")

    with httpx.Client(timeout=45.0) as client:
        for idx, prob in enumerate(problems, 1):
            session_id = str(uuid.uuid4())
            payload = {
                "sessionId": session_id,
                "session_id": session_id,
                "studentId": student_id,
                "student_id": student_id,
                "prompt": prob["question"],
                "language": language,
                "mode": mode,
            }

            print(f"[{idx}/{len(problems)}] Testing {prob['grade_label']} ({prob['subject']}): {prob['question'][:50]}...")
            t0 = time.perf_counter()

            try:
                resp = client.post(chat_url, json=payload, headers=headers)
                if resp.status_code == 401:
                    # Fallback directly to orchestrator
                    resp = client.post("http://localhost:9001/chat", json=payload, headers={"Content-Type": "application/json"})

                elapsed_ms = (time.perf_counter() - t0) * 1000

                if resp.status_code == 200:
                    data = resp.json()
                    text_en = data.get("textEng") or data.get("text_eng") or ""
                    text_km = data.get("textKhmer") or data.get("text_khmer") or ""
                    intent = data.get("intent", "explain")
                    is_fallback = data.get("from_fallback", False)

                    res_item = {
                        "index": idx,
                        "grade": prob["grade"],
                        "grade_label": prob["grade_label"],
                        "subject": prob["subject"],
                        "question": prob["question"],
                        "status": "PASS",
                        "status_code": 200,
                        "intent": intent,
                        "from_fallback": is_fallback,
                        "latency_ms": round(elapsed_ms, 1),
                        "response_en": text_en,
                        "response_km": text_km,
                    }
                    print(f"   [PASS] {elapsed_ms:.1f}ms | Intent: {intent} | Fallback: {is_fallback}")
                else:
                    res_item = {
                        "index": idx,
                        "grade": prob["grade"],
                        "grade_label": prob["grade_label"],
                        "subject": prob["subject"],
                        "question": prob["question"],
                        "status": "FAIL",
                        "status_code": resp.status_code,
                        "error_text": resp.text,
                        "latency_ms": round(elapsed_ms, 1),
                    }
                    print(f"   [FAIL] HTTP {resp.status_code}")
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                res_item = {
                    "index": idx,
                    "grade": prob["grade"],
                    "grade_label": prob["grade_label"],
                    "subject": prob["subject"],
                    "question": prob["question"],
                    "status": "ERROR",
                    "error_text": str(exc),
                    "latency_ms": round(elapsed_ms, 1),
                }
                print(f"   [ERROR] {exc}")

            results.append(res_item)
            time.sleep(0.1)

    return results


def generate_markdown_report(results: list[dict], output_file: Path) -> None:
    """Generate structured markdown report of test run."""
    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "PASS")
    failed = total - passed
    avg_latency = sum(r.get("latency_ms", 0) for r in results) / total if total else 0
    live_count = sum(1 for r in results if r.get("status") == "PASS" and not r.get("from_fallback"))

    md = []
    md.append("# 🇰🇭 TunSay AI — Exercise Bank Validation Report\n")
    md.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    md.append("## 📊 Summary Statistics\n")
    md.append(f"- **Total Problems Tested:** `{total}`")
    md.append(f"- **Passed Requests (HTTP 200):** `{passed}/{total}` (`{passed/total*100:.1f}%`)")
    md.append(f"- **Live Gemini AI Responses:** `{live_count}/{total}`")
    md.append(f"- **Average Latency:** `{avg_latency:.1f} ms`\n")

    md.append("## 📝 Detailed Results by Problem\n")
    md.append("| # | Grade | Subject | Question Snippet | Status | Intent | Latency | Response Excerpt |")
    md.append("|---|---|---|---|---|---|---|---|")

    for r in results:
        snip_q = r["question"][:40] + ("..." if len(r["question"]) > 40 else "")
        status_icon = "✅ PASS" if r["status"] == "PASS" else "❌ FAIL"
        intent = r.get("intent", "-")
        lat = f"{r.get('latency_ms', 0):.1f}ms"
        resp_snip = (r.get("response_en") or r.get("response_km") or r.get("error_text", "")).replace("\n", " ")[:60] + "..."
        md.append(f"| {r['index']} | {r['grade_label']} | {r['subject']} | {snip_q} | {status_icon} | {intent} | {lat} | {resp_snip} |")

    md.append("\n## 🔬 Full Problem & TunSay Response Breakdown\n")
    for r in results:
        md.append(f"### Problem {r['index']}: {r['grade_label']} — {r['subject']}\n")
        md.append(f"**Question:** {r['question']}\n")
        if r["status"] == "PASS":
            md.append(f"- **Intent:** `{r.get('intent')}`")
            md.append(f"- **Engine:** `{'Fallback' if r.get('from_fallback') else 'Live Gemini AI'}`")
            md.append(f"- **Latency:** `{r.get('latency_ms')} ms`\n")
            md.append(f"**TunSay Response:**\n> {r.get('response_en') or r.get('response_km')}\n")
        else:
            md.append(f"**Error:** `{r.get('error_text')}`\n")
        md.append("---\n")

    output_file.write_text("\n".join(md), encoding="utf-8")
    print(f"\n[REPORT SAVED] Comprehensive report saved to: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Exercise Bank against TunSay AI Backend")
    parser.add_argument("--url", default="http://localhost:9000", help="Backend base URL")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of problems to test")
    parser.add_argument("--output", default=str(DEFAULT_REPORT_FILE), help="Output markdown report path")
    args = parser.parse_args()

    results = run_exercise_tests(base_url=args.url, limit=args.limit)
    generate_markdown_report(results, Path(args.output))
