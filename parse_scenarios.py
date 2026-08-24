"""
Parses tunsay_multiturn_scenarios_grade1-12.md into structured JSON fixtures
for the pytest suite (test_tunsay_multiturn.py).

Usage:
    python parse_scenarios.py <input.md> <output.json>
"""
import re
import json
import sys


def parse(md_text: str):
    scenarios = []
    grade = None
    subject_title = None

    # Split into grade sections
    grade_blocks = re.split(r"^## (Grade \d+)\s*$", md_text, flags=re.MULTILINE)
    # grade_blocks[0] is preamble; then alternates [grade_label, content, grade_label, content, ...]
    for i in range(1, len(grade_blocks), 2):
        grade_label = grade_blocks[i].strip()
        grade_num = int(re.search(r"\d+", grade_label).group())
        content = grade_blocks[i + 1]

        # Split into subject subsections
        subject_blocks = re.split(r"^### (.+?)\s*$", content, flags=re.MULTILINE)
        for j in range(1, len(subject_blocks), 2):
            subject_title = subject_blocks[j].strip()  # e.g. "Math — Psar Chas mangoes"
            body = subject_blocks[j + 1]

            subject_match = re.match(r"([A-Za-z]+)\s*—\s*(.+)", subject_title)
            subject = subject_match.group(1) if subject_match else subject_title
            topic = subject_match.group(2) if subject_match else ""

            # Extract turns: lines starting with **Student:** or **Tunsay:**
            turns = []
            for line in body.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                m = re.match(r"\*\*(Student|Tunsay):\*\*\s*(.*)", line)
                if m:
                    role, text = m.group(1), m.group(2).strip()
                    turns.append({
                        "role": "student" if role == "Student" else "bot",
                        "text": text
                    })

            scenarios.append({
                "id": f"grade{grade_num}_{subject.lower()}",
                "grade": grade_num,
                "subject": subject,
                "topic": topic,
                "turns": turns
            })

    return scenarios


if __name__ == "__main__":
    in_path = sys.argv[1] if len(sys.argv) > 1 else "tunsay_multiturn_scenarios_grade1-12.md"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "tunsay_multiturn_fixtures.json"

    with open(in_path, "r", encoding="utf-8") as f:
        text = f.read()

    scenarios = parse(text)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(scenarios, f, ensure_ascii=False, indent=2)

    print(f"Parsed {len(scenarios)} scenarios -> {out_path}")
