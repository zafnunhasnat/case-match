
import csv
from pathlib import Path

CSV_PATH = Path("data/terminology/terms.csv")

# Additional patient-friendly clinical terminology.
# Codes are left blank until verified against SNOMED CT.
terms = {
    "dyspnea": [
        "breathlessness",
        "hard to breathe",
        "can't catch my breath",
        "breathing difficulty",
        "labored breathing",
    ],
    "chest pain": [
        "pain in chest",
        "tightness in chest",
        "chest pressure",
        "chest soreness",
        "aching chest",
    ],
    "fever": [
        "feeling feverish",
        "body temperature elevated",
        "hot and feverish",
        "running a temperature",
        "feeling unusually hot",
    ],
    "cough": [
        "dry cough",
        "wet cough",
        "persistent coughing",
        "hacking cough",
        "frequent coughing",
    ],
    "fatigue": [
        "low energy",
        "feeling worn out",
        "extreme tiredness",
        "lack of energy",
        "feeling drained",
    ],
    "nausea": [
        "upset stomach",
        "queasy feeling",
        "feeling like throwing up",
        "sick to my stomach",
        "stomach queasiness",
    ],
    "vomiting": [
        "throwing up",
        "being sick",
        "bringing up food",
        "repeated vomiting",
        "stomach contents coming up",
    ],
    "headache": [
        "head pain",
        "pain in head",
        "throbbing head",
        "pressure in head",
        "pounding headache",
    ],
    "dizziness": [
        "feeling faint",
        "unsteady feeling",
        "spinning sensation",
        "feeling off balance",
        "room spinning",
    ],
    "abdominal pain": [
        "stomach pain",
        "pain in belly",
        "cramping stomach",
        "lower stomach pain",
        "upper abdominal discomfort",
    ],
    "back pain": [
        "pain in back",
        "lower back pain",
        "upper back pain",
        "aching back",
        "back soreness",
    ],
    "diarrhea": [
        "loose stools",
        "watery stool",
        "frequent loose bowel movements",
        "runny stool",
        "frequent diarrhea",
    ],
    "constipation": [
        "difficulty passing stool",
        "hard stools",
        "infrequent bowel movements",
        "trouble having a bowel movement",
        "unable to pass stool",
    ],
    "sore throat": [
        "throat pain",
        "painful throat",
        "scratchy throat",
        "throat irritation",
        "difficulty swallowing due to throat pain",
    ],
    "nasal congestion": [
        "stuffy nose",
        "blocked nose",
        "nasal blockage",
        "nose feels congested",
        "difficulty breathing through nose",
    ],
    "runny nose": [
        "nose running",
        "nasal discharge",
        "dripping nose",
        "excess mucus from nose",
        "watery nasal discharge",
    ],
    "palpitations": [
        "racing heart",
        "heart pounding",
        "fluttering heartbeat",
        "irregular heartbeat sensation",
        "heart beating rapidly",
    ],
    "edema": [
        "swelling",
        "swollen ankles",
        "swollen feet",
        "fluid swelling",
        "puffiness",
    ],
    "rash": [
        "skin eruption",
        "red skin spots",
        "skin redness",
        "skin breakout",
        "patchy skin irritation",
    ],
    "pruritus": [
        "itchy skin",
        "skin itching",
        "constant itching",
        "itchiness",
        "itchy patches",
    ],
    "arthralgia": [
        "joint pain",
        "aching joints",
        "painful joints",
        "sore joints",
        "joint soreness",
    ],
    "myalgia": [
        "muscle pain",
        "aching muscles",
        "sore muscles",
        "muscle soreness",
        "body muscle aches",
    ],
    "weakness": [
        "feeling weak",
        "lack of strength",
        "general weakness",
        "reduced muscle strength",
        "body weakness",
    ],
    "dysuria": [
        "painful urination",
        "burning when urinating",
        "burning urination",
        "pain while passing urine",
        "urination discomfort",
    ],
    "urinary frequency": [
        "frequent urination",
        "needing to pee often",
        "urinating frequently",
        "constant need to urinate",
        "passing urine often",
    ],
    "blurred vision": [
        "blurry eyesight",
        "unclear vision",
        "fuzzy vision",
        "vision out of focus",
        "difficulty seeing clearly",
    ],
}

# Read existing synonyms so we do not add duplicates.
with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)
    existing = list(reader)

    existing_synonyms = {
        row["synonym"].strip().casefold()
        for row in existing
    }

added = 0

with open(CSV_PATH, "a", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "preferred_term",
            "synonym",
            "abbreviation",
            "terminology_code",
        ],
    )

    for preferred_term, synonyms in terms.items():
        for synonym in synonyms:
            if synonym.casefold() in existing_synonyms:
                continue

            writer.writerow({
                "preferred_term": preferred_term,
                "synonym": synonym,
                "abbreviation": "",
                "terminology_code": "",
            })

            existing_synonyms.add(synonym.casefold())
            added += 1

print(f"New terminology entries added: {added}")
print(f"Total CSV rows: {len(existing) + added}")

