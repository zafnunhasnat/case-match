
import json
import random
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from string import Template

from faker import Faker


# --------------------------------------------------
# Configuration
# --------------------------------------------------

SEED = 42
NOTE_COUNT = 200

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "data" / "synthetic_cases"

# Seed both random generators so every run is repeatable.
Faker.seed(SEED)
random.seed(SEED)
fake = Faker("en_US")


# --------------------------------------------------
# 1. Generate eight fictional doctors
# --------------------------------------------------

DOCTOR_ROLES = {
    "Emergency Medicine": [
        "Attending Physician",
        "Resident Physician",
    ],
    "Internal Medicine": [
        "Attending Physician",
        "Resident Physician",
    ],
    "Pediatrics": [
        "Attending Physician",
        "Pediatric Resident",
    ],
    "Cardiology": [
        "Cardiology Fellow",
        "Attending Cardiologist",
    ],
}


def generate_doctors():
    doctors = []

    for department, roles in DOCTOR_ROLES.items():
        for role in roles:
            doctors.append({
                "id": f"DOC-{len(doctors) + 1:03d}",
                "name": fake.name(),
                "department": department,
                "role": role,
            })

    return doctors


# --------------------------------------------------
# 2. Clinical wording variations
# --------------------------------------------------

RESPIRATORY_TERMS = [
    "dyspnea",
    "shortness of breath",
    "SOB",
    "trouble breathing",
]

CHEST_TERMS = [
    "chest discomfort",
    "CP",
    "chest tightness",
]

HTN_TERMS = [
    "HTN",
    "high blood pressure",
]


def get_wording_variation(note_number):
    """Cycle through terminology so every variation appears."""

    group = note_number % 3
    variation_number = note_number // 3

    if group == 0:
        term = RESPIRATORY_TERMS[
            variation_number % len(RESPIRATORY_TERMS)
        ]
        return f"Prior documentation describes {term}."

    if group == 1:
        term = CHEST_TERMS[
            variation_number % len(CHEST_TERMS)
        ]
        return f"Previous records mention {term}."

    term = HTN_TERMS[
        variation_number % len(HTN_TERMS)
    ]
    return f"Medical history references {term}."


# --------------------------------------------------
# 3. Four clinical note template groups
# --------------------------------------------------

TEMPLATE_GROUPS = {
    "respiratory": {
        "chief_complaint": [
            "$resp_term for approximately $duration.",
            "Reports $resp_term, worse with exertion.",
            "Here for evaluation of $resp_term x $duration.",
        ],
        "history": [
            "Patient $patient_name (MRN $mrn) reports symptoms "
            "beginning $duration ago. Works as a $occupation "
            "and lives in $town. Recently attended $event. $variation",
            "$patient_name presents with respiratory complaints. "
            "Symptoms have been intermittent. Patient is a "
            "$occupation from $town. $variation",
        ],
        "assessment": [
            "Possible pneumonia versus viral respiratory illness. "
            "Correlate with examination and imaging.",
            "Respiratory symptoms of unclear etiology. "
            "Further evaluation recommended.",
        ],
    },

    "cardiac": {
        "chief_complaint": [
            "$chest_term for approximately $duration.",
            "Reports intermittent $chest_term.",
            "Evaluation requested for $chest_term x $duration.",
        ],
        "history": [
            "Patient $patient_name (MRN $mrn) describes episodes "
            "of discomfort. Works as a $occupation in $town. "
            "Recently attended $event. $variation",
            "$patient_name reports symptoms occurring at rest "
            "and occasionally with activity. $variation",
        ],
        "assessment": [
            "Chest discomfort; cardiac etiology cannot be excluded. "
            "Consider further cardiac evaluation.",
            "Possible cardiac-related symptoms. "
            "Clinical correlation recommended.",
        ],
    },

    "gi": {
        "chief_complaint": [
            "Abdominal discomfort x $duration.",
            "Reports nausea and intermittent abdominal pain.",
            "Here for evaluation of GI symptoms.",
        ],
        "history": [
            "Patient $patient_name (MRN $mrn) reports symptoms "
            "over the past $duration. Works as a $occupation "
            "and lives in $town. Recently attended $event. $variation",
            "$patient_name reports decreased appetite with "
            "intermittent nausea. No clear trigger identified. "
            "$variation",
        ],
        "assessment": [
            "Possible gastritis versus other gastrointestinal process.",
            "Abdominal symptoms of uncertain cause. "
            "Further evaluation may be necessary.",
        ],
    },

    "neurological": {
        "chief_complaint": [
            "Headache and dizziness x $duration.",
            "Reports intermittent headache.",
            "Here for evaluation of neurological symptoms.",
        ],
        "history": [
            "Patient $patient_name (MRN $mrn) reports symptoms "
            "beginning $duration ago. Works as a $occupation "
            "in $town. Recently attended $event. $variation",
            "$patient_name describes intermittent headaches "
            "without a consistent pattern. $variation",
        ],
        "assessment": [
            "Possible migraine; additional causes should be considered.",
            "Neurological symptoms without a definitive diagnosis "
            "at this time.",
        ],
    },
}


# --------------------------------------------------
# 4. Deliberately planted hard cases
# --------------------------------------------------

HARD_CASES = {
    "negation": (
        "Patient denies chest pain, fever, and new focal weakness. "
        "No acute symptoms reported in those areas."
    ),

    "history": (
        "History of migraines documented several years ago. "
        "This is historical information and does not necessarily "
        "indicate an active condition."
    ),

    "family_history": (
        "Family history: mother had an MI in her early 50s; "
        "father has HTN. No additional details available."
    ),

    "uncertainty": (
        "Possible pneumonia remains on the differential. "
        "Available findings are suggestive but not conclusive."
    ),
}

HARD_CASE_TAGS = list(HARD_CASES.keys())


# --------------------------------------------------
# 5. Subtle identifiers for privacy testing
# --------------------------------------------------

RARE_OCCUPATIONS = [
    "historical map restorer",
    "organ tuner",
    "lichen surveyor",
    "bellfounder",
    "meteorite cataloguer",
    "hand papermaker",
    "ornamental plaster conservator",
    "maritime ropework specialist",
]

SMALL_TOWNS = [
    "Leverett, Massachusetts",
    "Shutesbury, Massachusetts",
    "Wendell, Massachusetts",
    "Plainfield, Massachusetts",
    "Warwick, Massachusetts",
    "Goshen, Massachusetts",
    "Heath, Massachusetts",
    "Colrain, Massachusetts",
]

SPECIFIC_EVENTS = [
    "the 2025 Mill River Winter Lantern Walk",
    "the 2026 Franklin County Maple Weekend",
    "the 2025 North County Heritage Fair",
    "the 2026 Pioneer Valley Harvest Festival",
    "the 2025 Hilltown Historical Society Open House",
    "the 2026 Connecticut River Cleanup Day",
]


def generate_patient_identifiers():
    """Generate fictional identifiers and return their answer key."""

    patient_name = fake.name()
    dob = fake.date_between(
        start_date=datetime(1935, 1, 1).date(),
        end_date=datetime(2006, 12, 31).date(),
    ).isoformat()

    phone = fake.phone_number()
    mrn = fake.bothify(text="MRN-########")
    address = (
        f"{fake.street_address()}, "
        f"{fake.city()}, "
        f"{fake.state_abbr()} "
        f"{fake.postcode()}"
    )

    occupation = random.choice(RARE_OCCUPATIONS)
    town = random.choice(SMALL_TOWNS)
    event = random.choice(SPECIFIC_EVENTS)

    identifiers = [
        {"type": "patient_name", "value": patient_name},
        {"type": "date_of_birth", "value": dob},
        {"type": "phone_number", "value": phone},
        {"type": "medical_record_number", "value": mrn},
        {"type": "address", "value": address},
        {"type": "rare_occupation", "value": occupation},
        {"type": "small_town", "value": town},
        {"type": "specific_event", "value": event},
    ]

    return {
        "patient_name": patient_name,
        "dob": dob,
        "phone": phone,
        "mrn": mrn,
        "address": address,
        "occupation": occupation,
        "town": town,
        "event": event,
        "answer_key": identifiers,
    }


# --------------------------------------------------
# 6. Generate individual clinical notes
# --------------------------------------------------

NOTE_SKELETON = Template(
    """CHIEF COMPLAINT
$chief_complaint

HISTORY
$history

ASSESSMENT
$assessment
"""
)


def generate_note(note_number, doctors, typo_indices):
    note_id = f"NOTE-{note_number + 1:04d}"

    # Rotate through all four clinical template groups.
    group_name = list(TEMPLATE_GROUPS.keys())[
        note_number % len(TEMPLATE_GROUPS)
    ]
    group = TEMPLATE_GROUPS[group_name]

    # Rotate through all eight doctors.
    doctor = doctors[note_number % len(doctors)]

    identifiers = generate_patient_identifiers()

    duration = random.choice([
        "2 days",
        "3 days",
        "one week",
        "several hours",
        "approximately 2 weeks",
    ])

    respiratory_term = random.choice(RESPIRATORY_TERMS)
    chest_term = random.choice(CHEST_TERMS)
    variation = get_wording_variation(note_number)

    substitutions = {
        "patient_name": identifiers["patient_name"],
        "mrn": identifiers["mrn"],
        "occupation": identifiers["occupation"],
        "town": identifiers["town"],
        "event": identifiers["event"],
        "duration": duration,
        "resp_term": respiratory_term,
        "chest_term": chest_term,
        "variation": variation,
    }

    chief_complaint = Template(
        random.choice(group["chief_complaint"])
    ).safe_substitute(substitutions)

    history = Template(
        random.choice(group["history"])
    ).safe_substitute(substitutions)

    assessment = random.choice(group["assessment"])

    # Every note deliberately contains one hard case.
    hard_case_tag = HARD_CASE_TAGS[note_number % len(HARD_CASE_TAGS)]
    history += "\n" + HARD_CASES[hard_case_tag]

    # Add a little messy, realistic chart wording.
    history += (
        "\nMedication reconciliation reviewed. "
        "Outside records may contain additional details."
    )

    note_text = (
        "SYNTHETIC RECORD - NOT A REAL PATIENT\n"
        f"Patient: {identifiers['patient_name']}\n"
        f"DOB: {identifiers['dob']}\n"
        f"Phone: {identifiers['phone']}\n"
        f"MRN: {identifiers['mrn']}\n"
        f"Address: {identifiers['address']}\n"
        f"Documented by: {doctor['name']}\n\n"
        + NOTE_SKELETON.substitute(
            chief_complaint=chief_complaint,
            history=history,
            assessment=assessment,
        )
    )

    tags = [group_name, hard_case_tag]

    # Exactly 5% of notes receive a deliberate typo.
    if note_number in typo_indices:
        note_text = note_text.replace(
            "Medication reconciliation reviewed.",
            "Medication reconcilation reviewed.",
            1,
    )
        tags.append("typo")

    # Deterministic dates between 2024 and 2026.
    created_at = (
        datetime(2024, 1, 1, 8, 0)
        + timedelta(minutes=random.randint(0, 1000 * 24 * 60))
    )

    note = {
        "id": note_id,
        "author_id": doctor["id"],
        "department": doctor["department"],
        "document_type": random.choice([
            "Progress Note",
            "Clinical Note",
            "Consultation Note",
            "Follow-up Note",
        ]),
        "created_at": created_at.isoformat(),
        "text": note_text,
        "tags": sorted(set(tags)),
    }

    return note, identifiers["answer_key"]


# --------------------------------------------------
# 7. Save JSON files
# --------------------------------------------------

def save_json(filename, data):
    output_path = OUTPUT_DIR / filename

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        file.write("\n")

    print(f"Saved: {output_path.relative_to(BASE_DIR)}")


# --------------------------------------------------
# 8. Generate the complete dataset
# --------------------------------------------------

def generate_dataset():
    # Reset seeds each time the generator runs.
    Faker.seed(SEED)
    random.seed(SEED)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    doctors = generate_doctors()

    # Select exactly 5% of notes for deliberate typos.
    typo_count = round(NOTE_COUNT * 0.05)
    typo_indices = set(
        random.sample(range(NOTE_COUNT), typo_count)
    )

    notes = []
    planted_identifiers = {}

    for note_number in range(NOTE_COUNT):
        note, identifiers = generate_note(
            note_number,
            doctors,
            typo_indices,
        )

        notes.append(note)
        planted_identifiers[note["id"]] = identifiers

    save_json("doctors.json", doctors)
    save_json("notes.json", notes)
    save_json("planted_identifiers.json", planted_identifiers)

    # Print coverage statistics.
    department_counts = Counter(
        note["department"] for note in notes
    )

    tag_counts = Counter(
        tag
        for note in notes
        for tag in note["tags"]
    )

    print("\n========== DATASET SUMMARY ==========")
    print(f"Doctors generated: {len(doctors)}")
    print(f"Clinical notes generated: {len(notes)}")
    print(f"Notes with deliberate typos: {typo_count}")

    print("\nNotes per department:")
    for department, count in sorted(department_counts.items()):
        print(f"  {department}: {count}")

    print("\nNotes per tag:")
    for tag, count in sorted(tag_counts.items()):
        print(f"  {tag}: {count}")

    print("\nHard-case coverage:")
    for tag in HARD_CASE_TAGS:
        count = tag_counts[tag]
        print(f"  {tag}: {count}")

    print("\nAll files generated successfully.")


if __name__ == "__main__":
    generate_dataset()
