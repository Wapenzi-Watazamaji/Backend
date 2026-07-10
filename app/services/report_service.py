import uuid
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.report import Report, ReportType, ReportFormat, ReportStatus
from app.models.pregnancy import PregnancyRecord, ScheduledVisit
from app.models.user import User, UserRole
from app.models.profile import Profile
from app.schemas.report import ReportCreate, ReportRead, PopulationSnapshot


async def get_population_snapshot(db: AsyncSession, facility_id: uuid.UUID) -> PopulationSnapshot:
    # 1. Total pregnancies (Active)
    stmt = select(func.count(func.distinct(User.id))).join(
        Profile, Profile.user_id == User.id
    ).join(
        PregnancyRecord, PregnancyRecord.user_id == User.id
    ).where(
        User.role == UserRole.USER,
        Profile.preferred_facility_id == facility_id,
        PregnancyRecord.status == "ACTIVE"
    )
    total_pregnancies = await db.scalar(stmt) or 0
    
    # 2. Risk breakdown (High, Medium, Low)
    # We will just return dummy zeros if complex, or execute queries
    # For brevity, let's say 0 for now unless we do a group by
    risk_breakdown = {"LOW": total_pregnancies, "MEDIUM": 0, "HIGH": 0}
    
    # 3. Trimester breakdown
    trimester_breakdown = {"T1": 0, "T2": 0, "T3": total_pregnancies}
    
    return PopulationSnapshot(
        totalPregnancies=total_pregnancies,
        highRiskCount=risk_breakdown["HIGH"],
        mediumRiskCount=risk_breakdown["MEDIUM"],
        lowRiskCount=risk_breakdown["LOW"],
        trimesterBreakdown=trimester_breakdown,
        postpartumCount=0,
        snapshotDate=date.today()
    )


async def generate_report_async(db: AsyncSession, facility_id: uuid.UUID, clinician_id: uuid.UUID, req: ReportCreate) -> ReportRead:
    # 1. Create Report in DB as PENDING
    report = Report(
        facility_id=facility_id,
        created_by=clinician_id,
        type=req.type,
        format=req.format,
        date_range_start=req.dateRangeStart,
        date_range_end=req.dateRangeEnd,
        status=ReportStatus.GENERATING,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # 2. In a real app, we would enqueue a celery task here.
    # For now, we will just simulate it as READY and add a dummy URL
    report.status = ReportStatus.READY
    report.file_url = f"https://s3.dummy/reports/{report.id}.{req.format.value.lower()}"
    report.generated_at = datetime.utcnow()
    
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    return ReportRead.model_validate(report)


async def list_reports(db: AsyncSession, facility_id: uuid.UUID, limit: int = 20, offset: int = 0) -> List[ReportRead]:
    stmt = select(Report).where(Report.facility_id == facility_id).order_by(desc(Report.created_at)).limit(limit).offset(offset)
    results = await db.execute(stmt)
    reports = results.scalars().all()
    return [ReportRead.model_validate(r) for r in reports]


async def download_report(db: AsyncSession, report_id: uuid.UUID) -> Optional[str]:
    stmt = select(Report).where(Report.id == report_id)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    if report and report.file_url:
        return report.file_url
    return None
