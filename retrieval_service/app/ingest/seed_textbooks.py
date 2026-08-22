"""Pre-seeded MoEYS curriculum textbook chunks for Grades 3-6."""

from __future__ import annotations

from app.core.textbook_chunker import TextbookChunk

DEFAULT_CHUNKS: list[TextbookChunk] = [
    # Grade 4 Math: Fractions
    TextbookChunk(
        id="tb-g4-math-fractions-1",
        grade=4,
        subject="math",
        topic="fractions",
        title_khmer="ប្រភាគ និងការបូកប្រភាគភាគបែងដូចគ្នា",
        title_eng="Fractions and Adding Like Denominators",
        text_khmer="ដើម្បីបូកប្រភាគដែលមានភាគបែងដូចគ្នា យើងត្រូវបូកភាគយក និងរក្សាភាគបែងទុកនៅដដែល។ ឧទាហរណ៍៖ ១/៤ + ២/៤ = ៣/៤។",
        text_eng="To add fractions with the same denominator, add the numerators and keep the denominator the same. For example: 1/4 + 2/4 = 3/4.",
    ),
    # Grade 4 Math: Multiplication & Division
    TextbookChunk(
        id="tb-g4-math-mult-1",
        grade=4,
        subject="math",
        topic="multiplication",
        title_khmer="វិធីគុណ និងវិធីចែកចំនួនគត់",
        title_eng="Multiplication and Division of Whole Numbers",
        text_khmer="វិធីគុណគឺជាការបូកចំនួនដដែលៗច្រើនដង។ វិធីចែកគឺជាការបែងចែកចំនួនសរុបជាចំណែកស្មើៗគ្នា។",
        text_eng="Multiplication is repeated addition of the same number. Division is splitting a total amount into equal groups.",
    ),
    # Grade 4 Science: Water Cycle
    TextbookChunk(
        id="tb-g4-sci-water-1",
        grade=4,
        subject="science",
        topic="water_cycle",
        title_khmer="វដ្តទឹកក្នុងធម្មជាតិ",
        title_eng="The Water Cycle in Nature",
        text_khmer="ទឹកហួតពីទន្លេនិងសមុទ្រឡើងទៅលើអាកាស បង្កើតជាពពក (រំហួត)។ នៅពេលត្រជាក់ ពពកកកកុញហើយធ្លាក់មកវិញជាទឹកភ្លៀង (កំណកទឹក)។",
        text_eng="Water evaporates from rivers and oceans into the air to form clouds (evaporation). When cooled, it condenses and falls as rain (precipitation).",
    ),
    # Grade 5 Science: Photosynthesis
    TextbookChunk(
        id="tb-g5-sci-plants-1",
        grade=5,
        subject="science",
        topic="photosynthesis",
        title_khmer="ដំណើរការរស្មីសំយោគរបស់រុក្ខជាតិ",
        title_eng="Plant Photosynthesis Process",
        text_khmer="រុក្ខជាតិប្រើពន្លឺព្រះអាទិត្យ ទឹក និងឧស្ម័នកាបូនិច ដើម្បីផលិតចំណីអាហារ (គ្លុយកូស) និងបញ្ចេញឧស្ម័នអុកស៊ីសែន។",
        text_eng="Plants use sunlight, water, and carbon dioxide to produce food (glucose) and release oxygen.",
    ),
    # Grade 6 Math: Ratios
    TextbookChunk(
        id="tb-g6-math-ratio-1",
        grade=6,
        subject="math",
        topic="ratios",
        title_khmer="ផលធៀប និងសមាមាត្រ",
        title_eng="Ratios and Proportions",
        text_khmer="ផលធៀបបង្ហាញពីការប្រៀបធៀបបរិមាណពីរ។ ប្រសិនបើយើងគុណ ឬចែកតួទាំងពីរនៃផលធៀបដោយចំនួនដូចគ្នា តម្លៃនៃផលធៀបមិនផ្លាស់ប្តូរទេ។",
        text_eng="A ratio compares two quantities. If you multiply or divide both terms by the same number, the proportion remains equal.",
    ),
    # Grade 6 Science: Food Chains
    TextbookChunk(
        id="tb-g6-sci-ecosystem-1",
        grade=6,
        subject="science",
        topic="ecosystems",
        title_khmer="ខ្សែច្រវាក់អាហារ និងប្រព័ន្ធអេកូឡូស៊ី",
        title_eng="Food Chains and Ecosystems",
        text_khmer="អ្នកផលិត (រុក្ខជាតិ) បង្កើតថាមពលពីព្រះអាទិត្យ។ សត្វស៊ីរុក្ខជាតិជាអ្នកទទួលទានបឋម ហើយសត្វស៊ីសាច់ជាអ្នកទទួលទានបន្ទាប់។",
        text_eng="Producers (plants) create energy from the sun. Herbivores are primary consumers, and carnivores are secondary consumers.",
    ),
]
