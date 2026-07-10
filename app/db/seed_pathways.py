import asyncio
from sqlalchemy import select

from app.db.base import AsyncSessionLocal
from app.models.pregnancy import CarePathwayTemplate

MOH_ANC_PATHWAY_ID = "path_anc_moh_v1"
MOH_PNC_PATHWAY_ID = "path_postnatal_moh_v1"

PATHWAYS = [
    {
        "id": MOH_ANC_PATHWAY_ID,
        "name": "Standard Antenatal Care (MOH)",
        "description": "Ministry of Health standard 8-contact ANC model",
        "is_active": True,
        "milestones": [
            {"order": 1, "triggerWeek": 12, "label": "1st ANC Contact (12 Weeks)"},
            {"order": 2, "triggerWeek": 20, "label": "2nd ANC Contact (20 Weeks)"},
            {"order": 3, "triggerWeek": 26, "label": "3rd ANC Contact (26 Weeks)"},
            {"order": 4, "triggerWeek": 30, "label": "4th ANC Contact (30 Weeks)"},
            {"order": 5, "triggerWeek": 34, "label": "5th ANC Contact (34 Weeks)"},
            {"order": 6, "triggerWeek": 36, "label": "6th ANC Contact (36 Weeks)"},
            {"order": 7, "triggerWeek": 38, "label": "7th ANC Contact (38 Weeks)"},
            {"order": 8, "triggerWeek": 40, "label": "8th ANC Contact (40 Weeks)"}
        ]
    },
    {
        "id": MOH_PNC_PATHWAY_ID,
        "name": "Standard Postnatal Care (MOH)",
        "description": "Ministry of Health standard PNC model",
        "is_active": True,
        "milestones": [
            {"order": 1, "triggerDays": 1, "label": "PNC Day 1 (Within 24 Hours)"},
            {"order": 2, "triggerDays": 3, "label": "PNC Day 3 (48-72 Hours)"},
            {"order": 3, "triggerDays": 7, "label": "PNC Week 1 (7-14 Days)"},
            {"order": 4, "triggerDays": 42, "label": "PNC Week 6 (6 Weeks Comprehensive)"}
        ]
    }
]

async def seed_pathways():
    print("Seeding System Default Care Pathway Templates...")
    async with AsyncSessionLocal() as session:
        for p_data in PATHWAYS:
            stmt = select(CarePathwayTemplate).where(CarePathwayTemplate.id == p_data["id"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"Pathway Template {p_data['id']} already exists. Skipping.")
                continue
                
            new_pathway = CarePathwayTemplate(
                id=p_data["id"],
                name=p_data["name"],
                description=p_data["description"],
                milestones=p_data["milestones"],
                is_active=p_data["is_active"]
            )
            session.add(new_pathway)
            print(f"Added pathway template {p_data['id']}")
            
        await session.commit()
        print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_pathways())
