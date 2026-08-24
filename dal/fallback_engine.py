"""Dynamic Math Solver & Reusable Socratic Fallback Engine for TunSay AI.

Parses linear equations, quadratic equations, basic arithmetic expressions,
and word problems dynamically to render full worked examples using different numbers,
never solving the student's actual numbers.
"""

from __future__ import annotations

import math
import re


class FallbackTemplateEngine:
    """Universal Dynamic Solver & Socratic Explanation Engine for TunSay AI."""

    @staticmethod
    def parse_quadratic(text: str) -> tuple[float, float, float] | None:
        """Parses ax^2 + bx + c = 0 for any coefficients."""
        clean = text.replace(" ", "").lower()
        match = re.search(r"([+-]?\d*\.?\d*)x\^?2([+-]?\d*\.?\d*)x([+-]?\d+\.?\d*)?=0", clean)
        if not match:
            match = re.search(r"([+-]?\d*\.?\d*)x²([+-]?\d*\.?\d*)x([+-]?\d+\.?\d*)?=0", clean)
        if not match:
            return None

        a_str, b_str, c_str = match.groups()

        def parse_val(val: str | None, default: float) -> float:
            if not val or val == "+":
                return 1.0
            if val == "-":
                return -1.0
            try:
                return float(val)
            except ValueError:
                return default

        a = parse_val(a_str, 1.0)
        b = parse_val(b_str, 0.0)
        c = parse_val(c_str, 0.0) if c_str else 0.0
        return a, b, c

    @staticmethod
    def parse_linear(text: str) -> tuple[float, float, float] | None:
        """Parses ax + b = c for any coefficients (e.g., 2x + 5 = 15)."""
        clean = text.replace(" ", "").lower()
        match = re.search(r"([+-]?\d*\.?\d*)x([+-]?\d+\.?\d*)?=([+-]?\d+\.?\d*)", clean)
        if not match:
            return None

        a_str, b_str, c_str = match.groups()
        if "x^2" in clean or "x²" in clean:
            return None

        def parse_val(val: str | None, default: float) -> float:
            if not val or val == "+":
                return 1.0
            if val == "-":
                return -1.0
            try:
                return float(val)
            except ValueError:
                return default

        a = parse_val(a_str, 1.0)
        b = float(b_str) if b_str else 0.0
        c = float(c_str) if c_str else 0.0
        return a, b, c

    @staticmethod
    def parse_arithmetic(text: str) -> tuple[str, float] | None:
        """Parses bare arithmetic like 12 * 5, 250 / 5, 25 + 75."""
        clean = text.strip()
        match = re.search(r"(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)", clean)
        if not match:
            return None
        n1_str, op, n2_str = match.groups()
        n1, n2 = float(n1_str), float(n2_str)
        if op == "+":
            ans = n1 + n2
        elif op == "-":
            ans = n1 - n2
        elif op == "*":
            ans = n1 * n2
        elif op == "/":
            if n2 == 0:
                return None
            ans = n1 / n2
        else:
            return None
        expr = f"{n1_str} {op} {n2_str}"
        return expr, ans

    @classmethod
    def render_explanation(
        cls,
        prompt: str,
        language: str = "km",
        context: str | None = None,
    ) -> str:
        """Universal entry point to render dynamic explanations for any prompt."""
        is_km = str(language).lower() in ("km", "khmer")
        prompt_clean = prompt.strip().lower()
        full_text = prompt_clean + " " + (context or "").lower()

        # 1. Greetings
        if prompt_clean in ("hello", "hi", "hey", "សួស្ដី", "ជំរាបសួរ"):
            if is_km:
                return "សួស្ដី! ខ្ញុំគឺទន្សាយ (Tunsay) 🐰 រីករាយណាស់ដែលបានជួបប្អូន! តើយើងរៀន ឬធ្វើលំហាត់អ្វីជាមួយគ្នាថ្ងៃនេះ?"
            return "Hello! I'm Tunsay! 🐰 Let's solve your homework together! What are you working on today?"

        # 2. Quadratic Equation Worked Example (ax^2 + bx + c = 0)
        quad = cls.parse_quadratic(full_text)
        if quad:
            a, b, c = quad
            # Select a similar but different equation as worked example
            if a == 1 and b == 6 and c == -3:
                a_ex, b_ex, c_ex = 1.0, 8.0, -5.0
            else:
                a_ex, b_ex, c_ex = 1.0, 6.0, -3.0

            delta = b_ex**2 - 4 * a_ex * c_ex
            rhs = -c_ex
            half_b = b_ex / (2 * a_ex)
            sq_add = half_b**2
            final_rhs = rhs + sq_add

            b_sign = f"+ {b_ex:g}" if b_ex >= 0 else f"- {abs(b_ex):g}"
            half_b_sign = f"+ {half_b:g}" if half_b >= 0 else f"- {abs(half_b):g}"

            if is_km:
                return (
                    f"សួស្ដី! ខ្ញុំគឺទន្សាយ (Tunsay) 🐰 ដើម្បីជួយប្អូនដោះស្រាយសមីការ ${a:g}x^2 {f'+ {b:g}' if b>=0 else f'- {abs(b):g}'}x {f'+ {c:g}' if c>=0 else f'- {abs(c):g}'} = 0$ នេះ "
                    f"ទន្សាយនឹងបង្ហាញលំហាត់គំរូស្រដៀងគ្នាដែលមានលេខផ្សេងគ្នាគឺ៖ ${a_ex:g}x^2 {b_sign}x + ({c_ex:g}) = 0$\n\n"
                    f"សូមប្អូនពិនិត្យជំហានគំរូខាងក្រោម ៖\n\n"
                    f"📌 **ជំហានទី ១ (ផ្លាស់ទីចំនួនថេរ):**\n"
                    f"ផ្លាស់ទីចំនួនថេរ ${c_ex:g}$ ទៅខាងស្តាំនៃសញ្ញាស្មើ ($=$) ៖\n"
                    f"$${a_ex:g}x^2 {b_sign}x = {rhs:g}$$\n\n"
                    f"📌 **ជំហានទី ២ (បំពេញជាកាតារេពេញ):**\n"
                    f"យកមេគុណនៃ $x$ គឺ ${b_ex:g} / 2 = {half_b:g}$ លើកជាការ៉េបាន ${half_b:g}^2 = {sq_add:g}$។ បូកលេខ ${sq_add:g}$ ទៅខាងសងខាង៖\n"
                    f"$$(x {half_b_sign})^2 = {final_rhs:g}$$\n\n"
                    f"📌 **ជំហានទី ៣ (រកតម្លៃនៃ x):**\n"
                    f"បំពាក់ឬសការ៉េលើអវយវៈទាំងពីរ ៖\n"
                    f"$$x {half_b_sign} = \\pm \\sqrt{{{final_rhs:g}}}$$\n"
                    f"$$x = {-half_b:g} \\pm \\sqrt{{{final_rhs:g}}}$$\n\n"
                    f"ឥឡូវនេះ សូមប្អូនសាកល្បងអនុវត្តជំហានគំរូទាំងនេះទៅលើលំហាត់ដើមរបស់ប្អូន គឺសមីការ ${a:g}x^2 {f'+ {b:g}' if b>=0 else f'- {abs(b):g}'}x {f'+ {c:g}' if c>=0 else f'- {abs(c):g}'} = 0$ វិញម្តងណា! 🐰✨"
                )
            return (
                f"Hi! I'm Tunsay 🐰 To help you solve ${a:g}x^2 {f'+ {b:g}' if b>=0 else f'- {abs(b):g}'}x {f'+ {c:g}' if c>=0 else f'- {abs(c):g}'} = 0$, "
                f"I will walk you through a similar worked example with different numbers: ${a_ex:g}x^2 {b_sign}x + ({c_ex:g}) = 0$\n\n"
                f"Follow these steps to solve it:\n\n"
                f"📌 **Step 1: Move the constant term**\n"
                f"$$x^2 {b_sign}x = {rhs:g}$$\n\n"
                f"📌 **Step 2: Complete the square**\n"
                f"Add $({b_ex:g}/2)^2 = {sq_add:g}$ to both sides:\n"
                f"$$(x {half_b_sign})^2 = {final_rhs:g}$$\n\n"
                f"📌 **Step 3: Solve for x**\n"
                f"$$x = {-half_b:g} \\pm \\sqrt{{{final_rhs:g}}}$$\n\n"
                f"Now, try to apply these same steps to solve your original equation: ${a:g}x^2 {f'+ {b:g}' if b>=0 else f'- {abs(b):g}'}x {f'+ {c:g}' if c>=0 else f'- {abs(c):g}'} = 0$! You can do it! 🐰✨"
            )

        # 3. Linear Equation Worked Example (ax + b = c)
        lin = cls.parse_linear(full_text)
        if lin:
            a, b, c = lin
            if a == 2 and b == 6 and c == 16:
                a_ex, b_ex, c_ex = 3.0, 4.0, 19.0
            else:
                a_ex, b_ex, c_ex = 2.0, 6.0, 16.0

            diff = c_ex - b_ex
            x_val = diff / a_ex
            b_sign = f"+ {b_ex:g}" if b_ex >= 0 else f"- {abs(b_ex):g}"

            if is_km:
                return (
                    f"សួស្ដី! ខ្ញុំគឺទន្សាយ (Tunsay) 🐰 ដើម្បីជួយប្អូនដោះស្រាយសមីការ ${a:g}x {f'+ {b:g}' if b>=0 else f'- {abs(b):g}'} = {c:g} "
                    f"ទន្សាយនឹងបង្ហាញលំហាត់គំរូស្រដៀងគ្នាគឺ៖ ${a_ex:g}x {b_sign} = {c_ex:g}$\n\n"
                    f"📌 **ជំហានទី ១ (ផ្លាស់ទីចំនួនថេរ):**\n"
                    f"ផ្លាស់ទី ${b_ex:g}$ ទៅខាងស្តាំ ៖\n"
                    f"$${a_ex:g}x = {c_ex:g} - ({b_ex:g}) = {diff:g}$$\n\n"
                    f"📌 **ជំហានទី ២ (រកតម្លៃ x):**\n"
                    f"ចែកអវយវៈទាំងពីរនឹង ${a_ex:g}$ ៖\n"
                    f"$$x = \\frac{{{diff:g}}}{{{a_ex:g}}} = {x_val:g}$$\n\n"
                    f"ឥឡូវនេះ សូមប្អូនសាកល្បងអនុវត្តជំហានគំរូនេះទៅលើលំហាត់ដើមរបស់ប្អូន គឺសមីការ ${a:g}x {f'+ {b:g}' if b>=0 else f'- {abs(b):g}'} = {c:g} វិញណា! 🐰✨"
                )
            return (
                f"Hi! I'm Tunsay 🐰 To help you solve ${a:g}x {f'+ {b:g}' if b>=0 else f'- {abs(b):g}'} = {c:g}, "
                f"here is a similar worked example: ${a_ex:g}x {b_sign} = {c_ex:g}$\n\n"
                f"📌 **Step 1: Isolate the variable term**\n"
                f"$${a_ex:g}x = {c_ex:g} - ({b_ex:g}) = {diff:g}$$\n\n"
                f"📌 **Step 2: Solve for x**\n"
                f"$$x = \\frac{{{diff:g}}}{{{a_ex:g}}} = {x_val:g}$$\n\n"
                f"Now, try to apply these same steps to solve your original equation: ${a:g}x {f'+ {b:g}' if b>=0 else f'- {abs(b):g}'} = {c:g}! 🐰✨"
            )

        # 4. Arithmetic Worked Example (e.g. 12 * 5)
        arith = cls.parse_arithmetic(prompt_clean)
        if arith:
            expr, ans = arith
            match = re.search(r"(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)", expr)
            n1_str, op, n2_str = match.groups()
            n1, n2 = float(n1_str), float(n2_str)
            n1_ex = n1 - 2 if n1 > 2 else n1 + 3
            n2_ex = n2 - 1 if n2 > 1 else n2 + 2
            if op == "+":
                ans_ex = n1_ex + n2_ex
            elif op == "-":
                ans_ex = n1_ex - n2_ex
            elif op == "*":
                ans_ex = n1_ex * n2_ex
            elif op == "/":
                ans_ex = n1_ex / n2_ex
            
            expr_ex = f"{n1_ex:g} {op} {n2_ex:g}"

            if is_km:
                return (
                    f"សួស្ដី! ខ្ញុំគឺទន្សាយ (Tunsay) 🐰 ដើម្បីគណនា ${expr}$ "
                    f"តោះយើងមើលគំរូនៃប្រមាណវិធីស្រដៀងគ្នាគឺ៖ ${expr_ex}$ ៖\n\n"
                    f"📌 **គំរូគណនា៖**\n"
                    f"$${expr_ex} = {ans_ex:g}$$\n\n"
                    f"ឥឡូវនេះ សូមប្អូនសាកល្បងគណនាប្រមាណវិធីដើមរបស់ប្អូន ${expr}$ ដោយខ្លួនឯងណា! 🐰✨"
                )
            return (
                f"Hi! I'm Tunsay 🐰 To help you solve ${expr}$, "
                f"here is a similar worked example: ${expr_ex}$:\n\n"
                f"📌 **Worked Example:**\n"
                f"$${expr_ex} = {ans_ex:g}$$\n\n"
                f"Now, try to calculate your original expression ${expr}$ yourself! 🐰✨"
            )

        # 5. Practice / Affirmation request
        if prompt_clean in ("yes", "yeah", "yep", "ok", "okay", "sure", "បាទ", "ចាស", "សាកល្បង"):
            if is_km:
                return (
                    "អស្ចារ្យណាស់! 🎉 តោះយើងសាកល្បងដោះស្រាយលំហាត់គំរូស្រដៀងគ្នានេះមួយទៀត៖\n\n"
                    "📝 **លំហាត់គំរូ៖** ដោះស្រាយសមីការ $x^2 + 6x - 3 = 0$\n\n"
                    "📌 **ជំហានទី ១ (កំណត់មេគុណ):** $a = 1, \\; b = 6, \\; c = -3$\n"
                    "📌 **ជំហានទី ២ (គណនា $\\Delta$):** $\\Delta = 6^2 - 4(1)(-3) = 36 + 12 = 48$\n"
                    "📌 **ជំហានទី ៣ (រកឬស):** $x = \\frac{-6 \\pm \\sqrt{48}}{2} = -3 \\pm 2\\sqrt{3}$\n\n"
                    "តើប្អូនយល់ច្បាស់ពីជំហានគំរូនេះហើយឬនៅ? 🐰✨"
                )
            return (
                "Awesome! 🎉 Let's look at another similar worked example:\n\n"
                "📝 **Worked Example:** Solve $x^2 + 6x - 3 = 0$\n\n"
                "📌 **Step 1:** $a = 1, \\; b = 6, \\; c = -3$\n"
                "📌 **Step 2:** $\\Delta = 6^2 - 4(1)(-3) = 48$\n"
                "📌 **Step 3:** $x = -3 \\pm 2\\sqrt{3}$\n\n"
                "Does this worked example make sense? 🐰✨"
            )

        # 6. Generalized Word Problem & Context Extraction
        numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", prompt_clean)]
        if len(numbers) >= 2:
            n1, n2 = numbers[0], numbers[1]
            if "total" in prompt_clean or "altogether" in prompt_clean or "sells" in prompt_clean or "សរុប" in prompt_clean:
                # Alternate example values
                n1_ex = n1 + 2
                n2_ex = n2 + 3
                total_ex = n1_ex + n2_ex
                if is_km:
                    return (
                        f"សួស្ដី! ខ្ញុំគឺទន្សាយ (Tunsay) 🐰 ដើម្បីដោះស្រាយលំហាត់នេះ "
                        f"តោះយើងពិនិត្យលំហាត់គំរូស្រដៀងគ្នាដែលមានលេខផ្សេងគ្នា ៖\n\n"
                        f"📝 **លំហាត់គំរូ៖** ចំនួនទី១ = {n1_ex:g}, ចំនួនទី២ = {n2_ex:g}\n"
                        f"📌 **គំរូគណនាសរុប៖** ${n1_ex:g} + {n2_ex:g} = {total_ex:g}$\n\n"
                        f"ឥឡូវនេះ សូមប្អូនសាកល្បងគណនាលំហាត់ដើមរបស់ប្អូនដោយប្រើវិធីដូចគ្នាណា! 🐰✨"
                    )
                return (
                    f"Hi! I'm Tunsay 🐰 To help you solve this word problem, "
                    f"let's check a similar worked example with different numbers:\n\n"
                    f"📝 **Worked Example:** First quantity = {n1_ex:g}, Second quantity = {n2_ex:g}\n"
                    f"📌 **Calculation:** $${n1_ex:g} + {n2_ex:g} = {total_ex:g}$$\n\n"
                    f"Now, try to solve your original word problem using the same method! 🐰✨"
                )

        # 7. Fallback General Socratic
        if is_km:
            return "តោះយើងពិនិត្យមើលសំណួរនេះជាមួយគ្នា! 🐰 ជំហានទី ១៖ តើប្អូនឃើញលេខ ឬពាក្យគន្លឹះអ្វីខ្លះនៅក្នុងសំណួរនេះដំបូងគេ?"
        return "Let me help you with this exercise! 🐰 Step 1: What is the first key number or observation you see in the problem?"
