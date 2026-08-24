#!/usr/bin/env python3
"""Interactive Terminal CLI Chat for testing TunSay AI Backend.

This script communicates directly with Gateway (http://localhost:9000/chat) or
Orchestrator (http://localhost:9001/chat) to test live multi-turn Socratic responses,
latency, intent classification, and language modes in real time.

Usage:
    python scripts/interactive_chat.py [--url http://localhost:9000]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
import httpx

# ANSI Color Codes for beautiful terminal display
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
BLUE = "\033[94m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"


def print_banner() -> None:
    print(f"\n{BOLD}{CYAN}========================================================================{RESET}")
    print(f"{BOLD}{MAGENTA}   🐰 TunSay AI — Interactive Terminal Backend Tester 🇰🇭{RESET}")
    print(f"{BOLD}{CYAN}========================================================================{RESET}")
    print(f"{YELLOW}Commands:{RESET}")
    print(f"  {BOLD}/lang [km|en]{RESET}   — Switch reply language (Khmer or English)")
    print(f"  {BOLD}/mode [student|parent]{RESET} — Switch mode (student=Socratic, parent=full solution)")
    print(f"  {BOLD}/clear{RESET}          — Reset session ID / conversation history")
    print(f"  {BOLD}/exit{RESET}           — Exit interactive session\n")


def acquire_test_user(base_url: str = "http://localhost:9000") -> tuple[str, str]:
    """Register or log in a test student in Postgres DB to satisfy foreign key constraints."""
    import random
    unique_name = f"TestStudentCLI_{random.randint(1000, 9999)}"
    
    # Try gateway endpoint first, fallback to auth_service directly
    urls = [
        f"{base_url.rstrip('/')}/api/auth/register",
        "http://localhost:9002/register",
    ]
    payload = {
        "student_name": unique_name,
        "grade": 4,
        "language": "en",
    }
    
    for url in urls:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    token = data.get("access_token") or data.get("accessToken") or ""
                    # Extract user_id from JWT payload sub
                    import jwt
                    claims = jwt.decode(token, options={"verify_signature": False})
                    user_id = claims.get("sub", "")
                    return user_id, token
        except Exception:
            pass

    # If registration fails, fallback to hardcoded UUID
    demo_uuid = "f728f1f3-6cb5-4e0e-bbdc-8862034bedfa"
    import jwt
    token = jwt.encode({"sub": demo_uuid, "exp": 9999999999}, "replace-with-a-long-random-secret", algorithm="HS256")
    return demo_uuid, token


def interactive_chat(base_url: str = "http://localhost:9000") -> None:
    session_id = str(uuid.uuid4())
    student_id, jwt_token = acquire_test_user(base_url)
    language = "en"
    mode = "student"

    chat_endpoint = f"{base_url.rstrip('/')}/chat"

    print_banner()
    print(f"{BOLD}Connected to:{RESET} {GREEN}{chat_endpoint}{RESET}")
    print(f"{BOLD}Student ID:{RESET} {CYAN}{student_id}{RESET}")
    print(f"{BOLD}Session ID:{RESET} {CYAN}{session_id}{RESET}")
    print(f"{BOLD}Config:{RESET} Language={YELLOW}{language.upper()}{RESET} | Mode={YELLOW}{mode}{RESET}\n")

    with httpx.Client(timeout=40.0) as client:
        while True:
            try:
                user_input = input(f"{BOLD}{BLUE}Student 👤 > {RESET}").strip()
            except (KeyboardInterrupt, EOFError):
                print(f"\n{YELLOW}Exiting TunSay CLI test. Goodbye! 🐰{RESET}")
                sys.exit(0)

            if not user_input:
                continue

            # Command Handling
            cmd_lower = user_input.lower()
            if cmd_lower in ("/exit", "/quit", "exit", "quit"):
                print(f"{YELLOW}Exiting TunSay CLI test. Goodbye! 🐰{RESET}")
                break

            if cmd_lower == "/clear":
                session_id = str(uuid.uuid4())
                print(f"{GREEN}✓ Conversation reset. New Session ID: {session_id}{RESET}\n")
                continue

            if cmd_lower.startswith("/lang"):
                parts = user_input.split()
                if len(parts) > 1 and parts[1].lower() in ("km", "khmer", "en", "english"):
                    language = "km" if parts[1].lower() in ("km", "khmer") else "en"
                    print(f"{GREEN}✓ Language set to: {language.upper()}{RESET}\n")
                else:
                    print(f"{RED}Usage: /lang km  OR  /lang en{RESET}\n")
                continue

            if cmd_lower.startswith("/mode"):
                parts = user_input.split()
                if len(parts) > 1 and parts[1].lower() in ("student", "parent"):
                    mode = parts[1].lower()
                    print(f"{GREEN}✓ Mode set to: {mode}{RESET}\n")
                else:
                    print(f"{RED}Usage: /mode student  OR  /mode parent{RESET}\n")
                continue

            # Send request to Gateway/Orchestrator
            payload = {
                "sessionId": session_id,
                "session_id": session_id,
                "studentId": student_id,
                "student_id": student_id,
                "prompt": user_input,
                "language": language,
                "mode": mode,
            }

            headers = {"Content-Type": "application/json"}
            if jwt_token:
                headers["Authorization"] = f"Bearer {jwt_token}"

            try:
                t0 = time.perf_counter()
                response = client.post(chat_endpoint, json=payload, headers=headers)
                
                # If Gateway returns 401 unauth, try Orchestrator port 9001 directly
                if response.status_code == 401:
                    orchestrator_endpoint = "http://localhost:9001/chat"
                    response = client.post(orchestrator_endpoint, json=payload, headers={"Content-Type": "application/json"})

                elapsed_ms = (time.perf_counter() - t0) * 1000

                if response.status_code == 200:
                    data = response.json()

                    # Extract reply text
                    reply_km = data.get("textKhmer") or data.get("text_khmer") or ""
                    reply_en = data.get("textEng") or data.get("text_eng") or ""
                    reply_text = reply_km if language == "km" else reply_en
                    if not reply_text:
                        reply_text = reply_km or reply_en or "No reply text returned."

                    intent = data.get("intent", "explain")
                    is_fallback = data.get("from_fallback", False)

                    print(f"\n{BOLD}{MAGENTA}TunSay 🐰 > {RESET}{reply_text}")
                    
                    # Metadata footer
                    fallback_str = f" | {RED}FALLBACK{RESET}" if is_fallback else f" | {GREEN}LIVE GEMINI AI{RESET}"
                    print(
                        f"{BOLD}{CYAN}[Intent: {intent}{fallback_str} | Latency: {elapsed_ms:.1f}ms]{RESET}\n"
                    )
                else:
                    print(f"\n{RED}❌ Backend Error {response.status_code}:{RESET} {response.text}\n")

            except httpx.ConnectError:
                print(f"\n{RED}❌ Connection Failed! Could not reach {chat_endpoint}.{RESET}")
                print(f"{YELLOW}Make sure your Docker services are running (`docker compose up -d`).{RESET}\n")
            except Exception as exc:
                print(f"\n{RED}❌ Unexpected Error: {exc}{RESET}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TunSay AI Interactive CLI Chat")
    parser.add_argument(
        "--url",
        default="http://localhost:9000",
        help="Backend URL (default: http://localhost:9000)",
    )
    args = parser.parse_args()
    interactive_chat(args.url)
