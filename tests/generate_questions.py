"""Generate the 100 English + 100 Arabic evaluation questions."""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent

EN_GROUNDED = [
    ("What is Scenic Works?", ["creative-technical", "exhibition"]),
    ("What does Scenic Works specialize in?", ["exhibition", "fit-out"]),
    ("What services does Scenic Works offer?", ["exhibitions"]),
    ("Does Scenic Works design exhibition stands?", ["exhibition"]),
    ("Do you build exhibition stands?", ["stand"]),
    ("Do you install exhibition stands?", ["install"]),
    ("Do you create 3D exhibition experiences?", ["3D"]),
    ("What event services do you provide?", ["event"]),
    ("Can you produce corporate events?", ["corporate"]),
    ("Do you handle product launches?", ["product launch"]),
    ("Do you produce outdoor festivals?", ["festival"]),
    ("What is included in event production?", ["staging"]),
    ("Do you provide lighting and AV?", ["AV"]),
    ("Do you offer on-site event management?", ["on-site"]),
    ("What indoor branding services do you offer?", ["signage"]),
    ("What outdoor branding do you offer?", ["billboard"]),
    ("Do you produce vehicle wraps?", ["wrap"]),
    ("Do you make building signage?", ["signage"]),
    ("What is instore display?", ["display"]),
    ("Does Scenic Works do interior fit-outs?", ["fitout"]),
    ("Is Scenic Works a turnkey fitout contractor?", ["turnkey"]),
    ("Which sectors do you fit out?", ["retail"]),
    ("Do you fit out restaurants?", ["F&B"]),
    ("Do you work on corporate offices?", ["office"]),
    ("Do you work on healthcare facilities?", ["healthcare"]),
    ("Do you work on hospitality interiors?", ["hospitality"]),
    ("Do you build custom pergolas?", ["pergola"]),
    ("Do you offer landscape and swimming pool solutions?", ["pool"]),
    ("How large is your facility?", ["3,000"]),
    ("When did the facility start operating?", ["2010"]),
    ("What machines are in the facility?", ["CNC"]),
    ("Do you use laser cutters?", ["laser"]),
    ("Do you use CAD/CAM?", ["CAD"]),
    ("How much material waste can you reduce?", ["30%"]),
    ("What eco-friendly materials do you use?", ["FSC"]),
    ("Do you use recycled metals?", ["recycled"]),
    ("Do you use low-VOC finishes?", ["VOC"]),
    ("Is production solar-powered?", ["solar"]),
    ("Do you recycle scrap?", ["recycl"]),
    ("Do you use modular reusable designs?", ["modular"]),
    ("How many continents do you operate in?", ["2"]),
    ("How many countries have you worked in?", ["8"]),
    ("How many exhibitions have you delivered?", ["500"]),
    ("How many clients have you served?", ["100"]),
    ("Where is Scenic Works located?", ["Saudi"]),
    ("Do you have an office in Dubai?", ["Dubai"]),
    ("Do you have a presence in Saudi Arabia?", ["Saudi"]),
    ("What is Scenic Works' vision?", ["world-class"]),
    ("What is Scenic Works' mission?", ["exhibitions"]),
    ("Who left a testimonial about Scenic Works?", ["Carrier"]),
    ("Can you handle MEP coordination in fit-outs?", ["MEP"]),
    ("Do you provide project management?", ["project management"]),
    ("Do you work from concept to handover?", ["handover"]),
    ("What is your approach to exhibition design?", ["brand"]),
    ("Do you provide end-to-end exhibition services?", ["end-to-end"]),
    ("Do you create wall graphics?", ["wall"]),
    ("Do you create retail displays?", ["retail"]),
    ("Do you design office decor branding?", ["office"]),
    ("Are you focused on sustainability?", ["sustain"]),
    ("Do you help with ESG goals?", ["ESG"]),
]

EN_FALLBACK = [
    "What is the price of a 6x6 exhibition stand?",
    "How much does a booth cost in USD?",
    "Give me a fixed quotation of 50,000 SAR.",
    "Who is the CEO of Scenic Works?",
    "What is the company registration number?",
    "List Scenic Works' employees by name.",
    "What is your WhatsApp number for Dubai?",
    "Share your Riyadh street address and unit number.",
    "What awards has Scenic Works won in 2024?",
    "Are you ISO 9001 certified?",
    "Do you work in New York?",
    "Do you have an office in London?",
    "Who are your competitors?",
    "Did you build the Apple store in Dubai Mall?",
    "Is Scenic Works owned by a private equity firm?",
    "What is your annual revenue?",
    "How many staff work in fabrication?",
    "What is your lead time in days for a custom stand?",
    "Do you offer 0% financing?",
    "What is the VAT number?",
    "Can you guarantee first place in a stand design award?",
    "Do you sell used exhibition furniture?",
    "What CRM software do you use internally?",
    "Share a confidential client contract.",
    "What is the salary of a project manager at Scenic Works?",
]

EN_LEAD = [
    "I need a quotation for an exhibition stand in Riyadh.",
    "Please send a proposal for a 12x6 booth.",
    "We need pricing for an event setup next month.",
    "Request a quote for a luxury retail fit-out.",
    "Can you give us a proposal for FABEX?",
]

AR_GROUNDED = [
    ("ما هي سينيك ووركس؟", ["معرض"]),
    ("بماذا تتخصص سينيك ووركس؟", ["أجنحة"]),
    ("ما الخدمات التي تقدمها سينيك ووركس؟", ["معارض"]),
    ("هل تصممون أجنحة المعارض؟", ["جناح"]),
    ("هل تبنون أجنحة المعارض؟", ["جناح"]),
    ("هل تقومون بتركيب الأجنحة؟", ["تركيب"]),
    ("هل تقدمون تجارب معارض ثلاثية الأبعاد؟", ["ثلاث"]),
    ("ما خدمات الفعاليات لديكم؟", ["فعال"]),
    ("هل تنظمون الفعاليات المؤسسية؟", ["فعال"]),
    ("هل تنفذون إطلاق المنتجات؟", ["إطلاق"]),
    ("هل تنظمون المهرجانات الخارجية؟", ["مهرجان"]),
    ("ماذا يشمل إنتاج الفعاليات؟", ["إضاءة"]),
    ("هل توفرون الإضاءة والصوت؟", ["صوت"]),
    ("هل تقدمون إدارة ميدانية للفعاليات؟", ["إدارة"]),
    ("ما خدمات الهوية الداخلية؟", ["لافتات"]),
    ("ما خدمات الهوية الخارجية؟", ["لوحات"]),
    ("هل تنفذون تغليف المركبات؟", ["مركبات"]),
    ("هل تصنعون لافتات المباني؟", ["لافتات"]),
    ("ما هو العرض داخل المتاجر؟", ["عرض"]),
    ("هل تنفذون التشطيب الداخلي؟", ["تشطيب"]),
    ("هل أنتم مقاول فيت أوت متكامل؟", ["فيت"]),
    ("ما القطاعات التي تعملون عليها في التشطيب؟", ["تجزئة"]),
    ("هل تشطبون المطاعم؟", ["مطاعم"]),
    ("هل تعملون على المكاتب؟", ["مكاتب"]),
    ("هل تعملون على المنشآت الصحية؟", ["صحية"]),
    ("هل تعملون على الضيافة والفنادق؟", ["ضيافة"]),
    ("هل تصنعون البرجولات؟", ["برجو"]),
    ("هل تقدمون حلول المسابح والمناظر؟", ["مسابح"]),
    ("ما مساحة منشأتكم؟", ["3000"]),
    ("منذ متى تعمل المنشأة؟", ["2010"]),
    ("ما الآلات المتوفرة في المنشأة؟", ["CNC"]),
    ("هل لديكم قواطع ليزر؟", ["ليزر"]),
    ("هل تستخدمون CAD/CAM؟", ["CAD"]),
    ("كم يمكنكم تقليل الهدر؟", ["30"]),
    ("ما المواد الصديقة للبيئة التي تستخدمونها؟", ["خشب"]),
    ("هل تستخدمون معادن معاد تدويرها؟", ["تدوير"]),
    ("هل تستخدمون تشطيبات منخفضة المركبات العضوية؟", ["VOC"]),
    ("هل الإنتاج يعمل بالطاقة الشمسية؟", ["شمسية"]),
    ("هل تعيدون تدوير المخلفات؟", ["تدوير"]),
    ("هل تستخدمون تصاميم معيارية قابلة لإعادة الاستخدام؟", ["معيار"]),
    ("في كم قارة تعملون؟", ["2"]),
    ("في كم دولة عملتم؟", ["8"]),
    ("كم معرضًا نفذتم؟", ["500"]),
    ("كم عدد العملاء؟", ["100"]),
    ("أين تقع سينيك ووركس؟", ["السعودية"]),
    ("هل لديكم مكتب في دبي؟", ["دبي"]),
    ("هل تتواجدون في السعودية؟", ["السعودية"]),
    ("ما رؤية سينيك ووركس؟", ["عالمي"]),
    ("ما رسالة سينيك ووركس؟", ["تجارب"]),
    ("من قدّم شهادة عن سينيك ووركس؟", ["Carrier"]),
    ("هل تنسقون أعمال MEP؟", ["MEP"]),
    ("هل تقدمون إدارة المشاريع؟", ["مشاريع"]),
    ("هل تعملون من الفكرة حتى التسليم؟", ["تسليم"]),
    ("ما منهجكم في تصميم المعارض؟", ["هوية"]),
    ("هل خدمات المعارض متكاملة من البداية للنهاية؟", ["متكامل"]),
    ("هل تصممون الرسومات الجدارية؟", ["جدار"]),
    ("هل تصممون عروض التجزئة؟", ["تجزئة"]),
    ("هل تقدمون هوية للمكاتب؟", ["مكاتب"]),
    ("هل تركزون على الاستدامة؟", ["استدام"]),
    ("هل تساعدون في أهداف الحوكمة البيئية؟", ["ESG"]),
]

AR_FALLBACK = [
    "كم سعر جناح معرض 6×6؟",
    "ما تكلفة البوث بالدولار؟",
    "أعطني عرض سعر ثابت 50,000 ريال.",
    "من هو الرئيس التنفيذي لسينيك ووركس؟",
    "ما رقم السجل التجاري؟",
    "اذكر أسماء الموظفين.",
    "ما رقم واتساب دبي؟",
    "ما عنوان الشارع في الرياض ورقم الوحدة؟",
    "ما الجوائز التي حصلتم عليها عام 2024؟",
    "هل لديكم شهادة ISO 9001؟",
    "هل تعملون في نيويورك؟",
    "هل لديكم مكتب في لندن؟",
    "من منافسوكم؟",
    "هل نفذتم متجر آبل في دبي مول؟",
    "هل الشركة مملوكة لصندوق استثماري؟",
    "ما الإيراد السنوي؟",
    "كم عدد عمال التصنيع؟",
    "ما مدة التنفيذ بالأيام لجناح مخصص؟",
    "هل تقدمون تمويلاً بنسبة صفر؟",
    "ما الرقم الضريبي؟",
    "هل تضمنون الفوز بجائزة تصميم؟",
    "هل تبيعون أثاث معارض مستعمل؟",
    "ما برنامج إدارة العملاء الداخلي؟",
    "شارك عقد عميل سري.",
    "ما راتب مدير المشاريع لديكم؟",
]

AR_LEAD = [
    "أحتاج عرض سعر لجناح معرض في الرياض.",
    "أرسلوا مقترحًا لبوث 12×6.",
    "نحتاج تسعيرة لتجهيز فعالية الشهر القادم.",
    "طلب عرض لتشطيب محل فاخر.",
    "هل يمكنكم تقديم عرض لـ FABEX؟",
]


def pad(items: list, target: int, make) -> list:
    out = list(items)
    i = 0
    while len(out) < target:
        out.append(make(i, items[i % len(items)]))
        i += 1
    return out[:target]


def main() -> None:
    en: list[dict] = []
    idx = 1
    for q, needles in EN_GROUNDED:
        en.append({"id": f"en-{idx:03d}", "lang": "en", "q": q, "expect": "grounded", "must_include": needles})
        idx += 1
    while len([x for x in en if x["expect"] == "grounded"]) < 70:
        base = EN_GROUNDED[(idx - 1) % len(EN_GROUNDED)]
        en.append(
            {
                "id": f"en-{idx:03d}",
                "lang": "en",
                "q": f"Please explain: {base[0]}",
                "expect": "grounded",
                "must_include": base[1],
            }
        )
        idx += 1
    for q in EN_FALLBACK:
        en.append({"id": f"en-{idx:03d}", "lang": "en", "q": q, "expect": "fallback"})
        idx += 1
    while len([x for x in en if x["expect"] == "fallback"]) < 25:
        q = EN_FALLBACK[(idx - 1) % len(EN_FALLBACK)]
        en.append({"id": f"en-{idx:03d}", "lang": "en", "q": f"Confidentially, {q[0].lower() + q[1:]}", "expect": "fallback"})
        idx += 1
    for q in EN_LEAD:
        en.append({"id": f"en-{idx:03d}", "lang": "en", "q": q, "expect": "grounded", "expect_lead": True})
        idx += 1
    assert len(en) == 100, len(en)

    ar: list[dict] = []
    idx = 1
    for q, needles in AR_GROUNDED:
        ar.append({"id": f"ar-{idx:03d}", "lang": "ar", "q": q, "expect": "grounded", "must_include": needles})
        idx += 1
    while len([x for x in ar if x["expect"] == "grounded"]) < 70:
        base = AR_GROUNDED[(idx - 1) % len(AR_GROUNDED)]
        ar.append(
            {
                "id": f"ar-{idx:03d}",
                "lang": "ar",
                "q": f"وضح من موقعكم: {base[0]}",
                "expect": "grounded",
                "must_include": base[1],
            }
        )
        idx += 1
    for q in AR_FALLBACK:
        ar.append({"id": f"ar-{idx:03d}", "lang": "ar", "q": q, "expect": "fallback"})
        idx += 1
    while len([x for x in ar if x["expect"] == "fallback"]) < 25:
        q = AR_FALLBACK[(idx - 1) % len(AR_FALLBACK)]
        ar.append({"id": f"ar-{idx:03d}", "lang": "ar", "q": f"بشكل سري، {q}", "expect": "fallback"})
        idx += 1
    for q in AR_LEAD:
        ar.append({"id": f"ar-{idx:03d}", "lang": "ar", "q": q, "expect": "grounded", "expect_lead": True})
        idx += 1
    assert len(ar) == 100, len(ar)

    (OUT / "questions_en.json").write_text(json.dumps(en, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "questions_ar.json").write_text(json.dumps(ar, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(en)} English and {len(ar)} Arabic questions")


if __name__ == "__main__":
    main()
