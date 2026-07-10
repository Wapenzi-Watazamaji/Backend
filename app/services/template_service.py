from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.cycle import FormTemplate
from app.models.pregnancy import CarePathwayTemplate

async def get_all_form_templates(db: AsyncSession, context: Optional[str] = None) -> list[FormTemplate]:
    stmt = select(FormTemplate)
    if context:
        stmt = stmt.where(FormTemplate.context == context)
    stmt = stmt.order_by(FormTemplate.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def get_all_care_pathways(db: AsyncSession) -> list[CarePathwayTemplate]:
    stmt = select(CarePathwayTemplate).order_by(CarePathwayTemplate.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def get_form_template_by_id(db: AsyncSession, template_id) -> FormTemplate | None:
    stmt = select(FormTemplate).where(FormTemplate.id == template_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def create_form_template(db: AsyncSession, data: dict) -> FormTemplate:
    obj = FormTemplate(**data)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

async def update_form_template(db: AsyncSession, template: FormTemplate, data: dict) -> FormTemplate:
    for key, value in data.items():
        setattr(template, key, value)
    await db.commit()
    await db.refresh(template)
    return template
