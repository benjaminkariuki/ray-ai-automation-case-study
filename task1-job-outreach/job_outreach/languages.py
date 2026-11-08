"""Rule-based language-requirement extraction, applied to EVERY scraped posting (no AI cost).

A language counts as required when its name appears near a requirement word, e.g.
"Fluent English and Spanish", "Bilingual (English/Portuguese)", "German at C1 level is a must".
The AI check later produces a more precise version for the jobs it validates.
"""
import re

LANGUAGES = ["English", "Spanish", "French", "German", "Portuguese", "Italian", "Dutch", "Polish", "Swedish",
             "Norwegian", "Danish", "Finnish", "Russian", "Ukrainian", "Turkish", "Arabic", "Hebrew", "Hindi",
             "Urdu", "Mandarin", "Cantonese", "Chinese", "Japanese", "Korean", "Tagalog", "Filipino", "Vietnamese",
             "Thai", "Indonesian", "Malay", "Greek", "Czech", "Slovak", "Hungarian", "Romanian", "Bulgarian", "Swahili"]
CUES = re.compile(r"fluen|proficien|native|bilingual|speak|spoken|written|verbal|language|\b[ABC][12]\b|"
                  r"business[- ]level|working knowledge|command of|required|must|preferred|plus|communicat", re.I)
NAMES = re.compile(r"\b(" + "|".join(LANGUAGES) + r")\b", re.I)


def detect_languages(text, window=80):
    """Return 'English, Spanish'-style text for languages mentioned as requirements, or '' if none stated."""
    found = []
    text = str(text or "")
    for m in NAMES.finditer(text):
        name = m.group(1).title()
        around = text[max(0, m.start() - window): m.end() + window]
        if CUES.search(around) and name not in found:
            found.append(name)
    if "English" in found:  # English first: it is the language the brief cares about
        found.insert(0, found.pop(found.index("English")))
    return ", ".join(found)
