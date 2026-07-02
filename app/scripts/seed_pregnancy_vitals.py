import asyncio
import os
import sys

# Add the root directory to the python path so 'app' can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import AsyncSessionLocal
from app.models.cycle import FormTemplate, FormContext

async def seed_pregnancy_vitals():
    async with AsyncSessionLocal() as db:
        # Check if it already exists
        from sqlalchemy import select
        stmt = select(FormTemplate).filter_by(slug="tmpl_preg_vitals_v1")
        result = await db.execute(stmt)
        existing = result.scalars().first()
        
        if existing:
            print("Template tmpl_preg_vitals_v1 already exists.")
            return

        print("Seeding PREGNANCY_VITALS template...")
        
        schema = {
            "type": "object",
            "properties": {
                "bloodPressureSystolic": {"type": "integer"},
                "bloodPressureDiastolic": {"type": "integer"},
                "weightKg": {"type": "number"},
                "temperatureCelsius": {"type": "number"},
                "symptoms": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "fetalMovementCount": {"type": "integer"},
                "notes": {"type": "string"}
            }
        }
        
        ui_schema = {
            "symptoms": {"ui:widget": "checkboxes"},
            "notes": {"ui:widget": "textarea"}
        }

        template = FormTemplate(
            slug="tmpl_preg_vitals_v1",
            context=FormContext.PREGNANCY_VITALS,
            fields=schema,
            is_active=True,
            version="v1"
        )
        
        db.add(template)
        await db.commit()
        print("Successfully seeded PREGNANCY_VITALS template.")

if __name__ == "__main__":
    asyncio.run(seed_pregnancy_vitals())
