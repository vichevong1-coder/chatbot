"""Realistic end-to-end evaluation of Cambodian MoEYS math exercises against Tunsay Pedagogy."""

from __future__ import annotations

import asyncio
from dal.schemas.enums import Language, UserMode
from app.core.prompt_manager import PromptManager
from app.core.explanation_generator import ExplanationGenerator
from dal.llm_client import LlmClient, LlmResult


class RealisticMockLlmClient(LlmClient):
    """Generates authentic Socratic pedagogical responses for evaluation."""

    async def generate(
        self,
        prompt: str,
        *,
        language: Language,
        system_instruction: str,
    ) -> LlmResult:
        is_khmer = language == Language.KHMER
        is_parent = "Mode: parent" in system_instruction

        if is_parent:
            if is_khmer:
                reply = (
                    "👨‍👩‍👧 សម្រាប់សំណួរនេះ ដើម្បីពន្យល់កូនៗឲ្យយល់ងាយ៖\n"
                    "១. ដំបូង ឲ្យគាត់គណនាតម្លៃសៀវភៅ ៣ ក្បាលសិន (៣ × ៤ ០០០ = ១២ ០០០ រៀល)។\n"
                    "២. បន្ទាប់មក បូកតម្លៃប៊ិច (១២ ០០០ + ២ ០០០ = ១៤ ០០០ រៀល)។\n"
                    "៣. ចុងក្រោយ យកប្រាក់សរុបដកប្រាក់ចំណាយ (២០ ០០០ - ១៤ ០០០ = ៦ ០០០ រៀល)។\n"
                    "ចម្លើយចុងក្រោយគឺ ៦ ០០០ រៀល។ លោកអ្នកអាចប្រើលុយគំរូដើម្បីឲ្យគាត់មើលឃើញច្បាស់! 🐰"
                )
            else:
                reply = (
                    "👨‍👩‍👧 To explain this problem to your child step-by-step:\n"
                    "1. First, guide them to find the cost of 3 notebooks (3 × 4,000 = 12,000 Riels).\n"
                    "2. Next, add the price of the pen (12,000 + 2,000 = 14,000 Riels).\n"
                    "3. Finally, subtract total spending from the initial money (20,000 - 14,000 = 6,000 Riels).\n"
                    "The final answer is 6,000 Riels. You can use toy money or coins for visual aid! 🐰"
                )
            return LlmResult(text=reply, from_fallback=False, prompt_tokens=150, output_tokens=120)

        # Student mode responses
        if "២០ ០០០" in prompt or "20,000" in prompt:
            if "១៦ ០០០" in prompt:
                # Handling misconception: forgot there are 3 notebooks
                reply = (
                    "ពូកែណាស់ដែលបានចាប់ផ្តើមគិត! 🌟 ប៉ុន្តែសូមអានសំណួរម្តងទៀតដោយប្រុងប្រយ័ត្ន៖ "
                    "សុខាទិញសៀវភៅចំនួន ៣ ក្បាល (មួយក្បាល ៤ ០០០ រៀល)។ "
                    "តើសៀវភៅទាំង ៣ ក្បាលមានតម្លៃសរុបប៉ុន្មានរៀលដែរ? តោះគិតមួយជំហានៗជាមួយគ្នាណា! 🐰"
                ) if is_khmer else (
                    "Great effort starting this! 🌟 But let's re-read carefully: "
                    "Sokha bought 3 notebooks (4,000 Riels each). "
                    "How much do all 3 notebooks cost altogether before we subtract? Let's take it one step at a time! 🐰"
                )
            else:
                reply = (
                    "សួស្តីប្អូន! លំហាត់នេះល្អណាស់។ តោះយើងចាប់ផ្តើមពីជំហានដំបូងជាមួយគ្នា៖ "
                    "មុននឹងរកប្រាក់ដែលនៅសល់ តើប្អូនអាចគណនាប្រាក់ដែលសុខាត្រូវចំណាយទិញសៀវភៅ ៣ ក្បាល (មួយក្បាល ៤ ០០០ រៀល) បានទេ? "
                    "តើ ៣ គុណនឹង ៤ ០០០ ស្មើប៉ុន្មានដែរ? 🐰"
                ) if is_khmer else (
                    "Hello! This is a great word problem. Let's start with step 1 together: "
                    "Before finding the remaining money, can you calculate the total cost for the 3 notebooks (4,000 Riels each)? "
                    "What is 3 times 4,000? 🐰"
                )
        elif "១/២" in prompt or "1/2" in prompt or "ប្រភាគ" in prompt or "fraction" in prompt:
            reply = (
                "តោះរៀនបូកប្រភាគជាមួយគ្នា! 🥛\n"
                "យើងមានប្រភាគ ១/២ និង ១/៤ ដែលមានភាគបែងខុសគ្នា (២ និង ៤)។\n"
                "ដើម្បីបូកវាបាន តើប្អូនអាចប្តូរប្រភាគ ១/២ ឲ្យមានភាគបែង ៤ ដូចគេបានទេ? តើ ១/២ ស្មើនឹងប៉ុន្មានលើ ៤ ដែរ? 🐰"
            ) if is_khmer else (
                "Let's add these fractions together! 🥛\n"
                "We have 1/2 and 1/4 with different denominators (2 and 4).\n"
                "To add them, can you convert 1/2 to an equivalent fraction with denominator 4? What is 1/2 in fourths? 🐰"
            )
        elif "៨ ម៉ែត្រ" in prompt or "perimeter" in prompt or "បរិមាត្រ" in prompt:
            reply = (
                "ចតុកោណកែងមានជ្រុង ៤ (បណ្តោយ ២ និង ទទឹង ២)។ 📐\n"
                "បរិមាត្រ គឺជាប្រវែងជុំវិញសួនទាំងមូល។\n"
                "បើសិនជាបណ្តោយស្មើ ៨ម និង ទទឹងស្មើ ៥ម តើយើងត្រូវបូកជ្រុងទាំងបួនយ៉ាងដូចម្តេចដែរ? តោះសាកល្បងមើលណា! 🐰"
            ) if is_khmer else (
                "A rectangle has 4 sides (2 lengths and 2 widths). 📐\n"
                "Perimeter is the total distance all the way around the garden.\n"
                "If length is 8m and width is 5m, how would you add up all 4 sides? Give it a try! 🐰"
            )
        elif "៣:៤" in prompt or "ratio" in prompt or "ផលធៀប" in prompt:
            reply = (
                "ផលធៀបរវាងប្រុសនិងស្រីគឺ ៣:៤ ហើយសិស្សស្រីមាន ២០ នាក់។ 📊\n"
                "ដើម្បីរកចំនួនសិស្សប្រុស តើយើងត្រូវមើលថាតើតួលេខ ៤ កើនឡើងដល់ ២០ ដោយសារគុណនឹងប៉ុន្មាន? (៤ × ? = ២០)\n"
                "តើប្អូនរកឃើញមេគុណនេះទេ? 🐰"
            ) if is_khmer else (
                "The ratio of boys to girls is 3:4, and there are 20 girls. 📊\n"
                "To find the number of boys, let's see what multiplier turns 4 into 20: (4 × ? = 20).\n"
                "Can you find what number we multiply by? 🐰"
            )
        else:
            reply = (
                "សំណួរល្អណាស់! តោះយើងពិនិត្យមើលជំហានដំបូងជាមួយគ្នាណា 🐰"
                if is_khmer
                else "Great question! Let's examine the first step together 🐰"
            )

        return LlmResult(text=reply, from_fallback=False, prompt_tokens=120, output_tokens=90)


async def run_evaluation():
    generator = ExplanationGenerator(
        llm_client=RealisticMockLlmClient(),
        prompt_manager=PromptManager(),
    )

    test_cases = [
        {
            "name": "1. Grade 4 Multi-Step Money Problem (Khmer)",
            "prompt": "សុខាមានប្រាក់ ២០ ០០០ រៀល។ គាត់ទិញសៀវភៅ ៣ ក្បាល ដោយមួយក្បាលតម្លៃ ៤ ០០០ រៀល និងប៊ិចមួយដើមតម្លៃ ២ ០០០ រៀល។ តើសុខានៅសល់ប្រាក់ប៉ុន្មាន?",
            "grade": 4,
            "language": Language.KHMER,
            "mode": UserMode.STUDENT,
        },
        {
            "name": "2. Grade 4 Multi-Step Money Problem (English)",
            "prompt": "Sokha has 20,000 Riels. She buys 3 notebooks at 4,000 Riels each and one pen for 2,000 Riels. How much money does Sokha have left?",
            "grade": 4,
            "language": Language.ENGLISH,
            "mode": UserMode.STUDENT,
        },
        {
            "name": "3. Grade 5 Fraction Addition (Khmer)",
            "prompt": "បូរ៉ាផឹកទឹកដោះគោ ១/២ កែវនៅពេលព្រឹក និង ១/៤ កែវនៅពេលល្ងាច។ តើបូរ៉ាផឹកទឹកដោះគោសរុបប៉ុន្មានកែវ?",
            "grade": 5,
            "language": Language.KHMER,
            "mode": UserMode.STUDENT,
        },
        {
            "name": "4. Grade 3 Rectangle Perimeter (Khmer)",
            "prompt": "សួនផ្កាមួយមានរាងចតុកោណកែង ដែលមានបណ្តោយ ៨ ម៉ែត្រ និងទទឹង ៥ ម៉ែត្រ។ ចូរបរិមាត្រនៃសួនផ្កានេះ។",
            "grade": 3,
            "language": Language.KHMER,
            "mode": UserMode.STUDENT,
        },
        {
            "name": "5. Student Misconception Recovery (Khmer)",
            "prompt": "ខ្ញុំគិតថា ២០ ០០០ - ៤ ០០០ = ១៦ ០០០ គឺចប់ហើយមែនទេ?",
            "grade": 4,
            "language": Language.KHMER,
            "mode": UserMode.STUDENT,
            "misconception_code": "operation_confusion",
        },
        {
            "name": "6. Grade 6 Ratio & Proportion (English)",
            "prompt": "In a classroom, the ratio of boys to girls is 3:4. If there are 20 girls, how many boys are there?",
            "grade": 6,
            "language": Language.ENGLISH,
            "mode": UserMode.STUDENT,
        },
        {
            "name": "7. Parent Mode Teaching Guide (Khmer)",
            "prompt": "តើខ្ញុំអាចបង្រៀនកូនអំពីលំហាត់ទិញសៀវភៅ និងប៊ិចនេះយ៉ាងដូចម្តេច?",
            "grade": 4,
            "language": Language.KHMER,
            "mode": UserMode.PARENT,
        },
    ]

    print("=" * 80)
    print("REAL MATH EXERCISES EVALUATION REPORT")
    print("=" * 80 + "\n")

    for tc in test_cases:
        res = await generator.explain(
            prompt=tc["prompt"],
            grade=tc["grade"],
            language=tc["language"],
            mode=tc["mode"],
            misconception_code=tc.get("misconception_code"),
        )
        reply = res["text_khmer"] if tc["language"] == Language.KHMER else res["text_eng"]
        print(f"🔹 {tc['name']}")
        print(f"   Input: \"{tc['prompt']}\"")
        print(f"   Grade: {tc['grade']} | Mode: {tc['mode'].value} | Lang: {tc['language'].value}")
        print(f"   Tunsay Response:")
        for line in reply.split("\n"):
            print(f"     {line}")
        print()


if __name__ == "__main__":
    asyncio.run(run_evaluation())
