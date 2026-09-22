import os
import glob

replacements = [
    ("MedFront Health Clinic (AuraCare Health Clinic)", "MedFront"),
    ("MedFront Health Clinic", "MedFront"),
    ("MedFront AI Health Clinic", "MedFront"),
    ("MedFront Health", "MedFront"),
    ("AuraCare Health Clinic", "MedFront"),
    ("AuraCare", "MedFront"),
]

search_patterns = [
    "frontend/src/**/*.tsx",
    "src/**/*.py",
    "tests/**/*.py",
]

base_dir = "/home/allen20306/allen/Azure_VoiceAI"

for pattern in search_patterns:
    for filepath in glob.glob(os.path.join(base_dir, pattern), recursive=True):
        if not os.path.isfile(filepath):
            continue
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        original_content = content
        for old_text, new_text in replacements:
            content = content.replace(old_text, new_text)
        
        if content != original_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated: {filepath}")

print("Renaming completed.")
