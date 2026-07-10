import asyncio
from sqlalchemy import select

from app.db.base import AsyncSessionLocal
from app.models.cycle import FormTemplate, FormContext

TEMPLATES = [
    {
        "slug": "system-pregnancy-vitals-v1",
        "context": FormContext.PREGNANCY_VITALS,
        "version": "v1",
        "fields": {
            "fields": [
                {"key": "systolic_bp", "label": "Systolic Blood Pressure", "type": "NUMBER", "unit": "mmHg", "required": True},
                {"key": "diastolic_bp", "label": "Diastolic Blood Pressure", "type": "NUMBER", "unit": "mmHg", "required": True},
                {"key": "weight", "label": "Weight", "type": "NUMBER", "unit": "kg", "required": True},
                {"key": "fundal_height", "label": "Fundal Height", "type": "NUMBER", "unit": "cm", "required": False},
                {"key": "fetal_heart_rate", "label": "Fetal Heart Rate", "type": "NUMBER", "unit": "bpm", "required": False},
                {
                    "key": "fetal_presentation", 
                    "label": "Fetal Presentation", 
                    "type": "SINGLE_SELECT", 
                    "required": False, 
                    "options": ["Cephalic", "Breech", "Transverse"]
                },
                {
                    "key": "urinalysis_protein", 
                    "label": "Urinalysis Protein", 
                    "type": "SINGLE_SELECT", 
                    "required": False, 
                    "options": ["Negative", "Trace", "+", "++", "+++"],
                    "flaggingOptions": ["++", "+++"]
                }
            ]
        }
    },
    {
        "slug": "system-maternal-checkin-v1",
        "context": FormContext.MATERNAL_CHECKIN,
        "version": "v1",
        "fields": {
            "fields": [
                {"key": "vaginal_bleeding", "label": "Vaginal Bleeding?", "type": "BOOLEAN", "required": True, "flaggingOptions": ["true"]},
                {"key": "severe_headache", "label": "Severe Headache or Blurred Vision?", "type": "BOOLEAN", "required": True, "flaggingOptions": ["true"]},
                {"key": "severe_abdominal_pain", "label": "Severe Abdominal Pain?", "type": "BOOLEAN", "required": True, "flaggingOptions": ["true"]},
                {"key": "reduced_fetal_movement", "label": "Reduced Fetal Movement?", "type": "BOOLEAN", "required": False, "flaggingOptions": ["true"]},
                {"key": "fever_chills", "label": "Fever / Chills?", "type": "BOOLEAN", "required": True, "flaggingOptions": ["true"]},
                {"key": "swelling", "label": "Swelling of hands/face?", "type": "BOOLEAN", "required": False, "flaggingOptions": ["true"]}
            ]
        }
    },
    {
        "slug": "system-baby-vitals-v1",
        "context": FormContext.BABY_VITALS,
        "version": "v1",
        "fields": {
            "fields": [
                {"key": "temperature", "label": "Temperature", "type": "NUMBER", "unit": "°C", "required": True},
                {"key": "weight", "label": "Weight", "type": "NUMBER", "unit": "kg", "required": False},
                {"key": "breathing_rate", "label": "Breathing Rate", "type": "NUMBER", "unit": "breaths/min", "required": False},
                {"key": "feeding_well", "label": "Feeding Well?", "type": "BOOLEAN", "required": True, "flaggingOptions": ["false"]},
                {"key": "jaundice", "label": "Yellowing of eyes/skin (Jaundice)?", "type": "BOOLEAN", "required": True, "flaggingOptions": ["true"]},
                {"key": "umbilical_cord_dry", "label": "Umbilical cord clean/dry?", "type": "BOOLEAN", "required": False, "flaggingOptions": ["false"]}
            ]
        }
    },
    {
        "slug": "system-cycle-entry-v1",
        "context": FormContext.CYCLE_ENTRY,
        "version": "v1",
        "fields": {
            "fields": [
                {
                    "key": "flow", 
                    "label": "Bleeding Flow", 
                    "type": "SINGLE_SELECT", 
                    "required": False, 
                    "options": ["None", "Spotting", "Light", "Medium", "Heavy"]
                },
                {
                    "key": "pain", 
                    "label": "Pain/Cramps Level", 
                    "type": "SINGLE_SELECT", 
                    "required": False, 
                    "options": ["None", "Mild", "Moderate", "Severe"]
                },
                {
                    "key": "mood", 
                    "label": "Mood", 
                    "type": "MULTI_SELECT", 
                    "required": False, 
                    "options": ["Happy", "Sad", "Anxious", "Irritable", "Normal"]
                }
            ]
        }
    },
    {
        "slug": "system-cycle-symptom-v1",
        "context": FormContext.CYCLE_SYMPTOM,
        "version": "v1",
        "fields": {
            "fields": [
                {
                    "key": "symptom_type", 
                    "label": "Symptom Type", 
                    "type": "SINGLE_SELECT", 
                    "required": True, 
                    "options": ["Pelvic Pain", "Unusual Discharge", "Itching", "Odor", "Breakthrough Bleeding"]
                },
                {
                    "key": "severity", 
                    "label": "Severity", 
                    "type": "SINGLE_SELECT", 
                    "required": True, 
                    "options": ["Mild", "Moderate", "Severe"]
                },
                {"key": "duration_days", "label": "Duration (Days)", "type": "NUMBER", "required": False}
            ]
        }
    }
]

async def seed_templates():
    print("Seeding System Default Form Templates...")
    async with AsyncSessionLocal() as session:
        for t_data in TEMPLATES:
            stmt = select(FormTemplate).where(FormTemplate.slug == t_data["slug"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"Template {t_data['slug']} already exists. Skipping.")
                continue
                
            new_template = FormTemplate(
                slug=t_data["slug"],
                context=t_data["context"],
                version=t_data["version"],
                fields=t_data["fields"],
                facility_id=None,
                is_active=True
            )
            session.add(new_template)
            print(f"Added template {t_data['slug']}")
            
        await session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_templates())
