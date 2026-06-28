from detection import stylometric_detect

samples = [
    (
        "human",
        "So I finally tried that new ramen place downtown and honestly it was way better than I expected. "
        "The broth had this smoky depth that I couldn't quite place, and the noodles were perfectly chewy. "
        "I went with my roommate and we ended up staying way longer than planned just talking.",
    ),
    (
        "ai",
        "Artificial intelligence has fundamentally transformed the landscape of modern industries by enabling "
        "unprecedented levels of automation and data analysis. Through the application of machine learning "
        "algorithms, organizations can now extract actionable insights from vast datasets, optimizing "
        "operational efficiency and driving strategic decision-making processes.",
    ),
    (
        "borderline",
        "The meeting went well. We discussed the quarterly targets and agreed on next steps. "
        "Everyone seemed aligned on the priorities. I will follow up with the summary by end of week.",
    ),
]

for label, text in samples:
    result = stylometric_detect(text)
    print(f"[{label}]")
    print(f"  stylometric_score : {result['stylometric_score']}")
    print()
