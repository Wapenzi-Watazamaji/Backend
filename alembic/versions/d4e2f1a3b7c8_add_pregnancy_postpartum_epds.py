"""feat: Add pregnancy, postpartum, and EPDS models with seed data

Revision ID: d4e2f1a3b7c8
Revises: c06720a2315e
Create Date: 2026-07-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid
import json
from datetime import datetime, timezone

revision = "d4e2f1a3b7c8"
down_revision = ("146b47073f13", "c06720a2315e")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. Extend existing form_context_enum with PREGNANCY_VITALS          #
    # ------------------------------------------------------------------ #
    op.execute("ALTER TYPE form_context_enum ADD VALUE IF NOT EXISTS 'PREGNANCY_VITALS'")
    op.execute("COMMIT")

    # ------------------------------------------------------------------ #
    # 2. New Postgres enum types                                           #
    # ------------------------------------------------------------------ #
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE pregnancy_status_enum AS ENUM ('ACTIVE', 'ENDED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE pregnancy_outcome_enum AS ENUM ('LIVE_BIRTH', 'STILLBIRTH', 'MISCARRIAGE', 'OTHER');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE visit_status_enum AS ENUM ('SCHEDULED', 'COMPLETED', 'MISSED', 'RESCHEDULED');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE risk_level_enum AS ENUM ('LOW', 'MEDIUM', 'HIGH');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE nutrition_category_enum AS ENUM ('IRON', 'FOLIC_ACID', 'HYDRATION', 'FOODS_TO_AVOID', 'HEALTHY_SNACKS');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE baby_gender_enum AS ENUM ('MALE', 'FEMALE', 'OTHER');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE epds_risk_level_enum AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'SELF_HARM_RISK');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # ------------------------------------------------------------------ #
    # 3. Create tables                                                     #
    # ------------------------------------------------------------------ #
    from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
    op.create_table(
        "pregnancy_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("last_menstrual_period", sa.Date, nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("is_first_pregnancy", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("status", PG_ENUM("ACTIVE", "ENDED", name="pregnancy_status_enum", create_type=False), nullable=False, server_default="ACTIVE"),
        sa.Column("outcome", PG_ENUM("LIVE_BIRTH", "STILLBIRTH", "MISCARRIAGE", "OTHER", name="pregnancy_outcome_enum", create_type=False), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_table(
        "care_pathway_templates",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("milestones", JSON, nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "scheduled_visits",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("pregnancy_id", UUID(as_uuid=True), sa.ForeignKey("pregnancy_records.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("pathway_template_id", sa.String, sa.ForeignKey("care_pathway_templates.id"), nullable=True),
        sa.Column("milestone_order", sa.Integer, nullable=True),
        sa.Column("label", sa.String, nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", PG_ENUM("SCHEDULED", "COMPLETED", "MISSED", "RESCHEDULED", name="visit_status_enum", create_type=False), nullable=False, server_default="SCHEDULED"),
        sa.Column("facility_id", UUID(as_uuid=True), nullable=True),
        sa.Column("purpose", sa.Text, nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_table(
        "pregnancy_vitals_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("pregnancy_id", UUID(as_uuid=True), sa.ForeignKey("pregnancy_records.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("form_submissions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("is_flagged", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("flagged_reasons", JSON, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_table(
        "vitals_feedback",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("vitals_entry_id", UUID(as_uuid=True), sa.ForeignKey("pregnancy_vitals_entries.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("clinician_id", UUID(as_uuid=True), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "pregnancy_risk_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("pregnancy_id", UUID(as_uuid=True), sa.ForeignKey("pregnancy_records.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("level", PG_ENUM("LOW", "MEDIUM", "HIGH", name="risk_level_enum", create_type=False), nullable=False, server_default="LOW"),
        sa.Column("factors", JSON, nullable=False, server_default="[]"),
        sa.Column("clinician_override", JSON, nullable=True),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "pregnancy_week_info",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("week_number", sa.Integer, nullable=False, unique=True, index=True),
        sa.Column("trimester", sa.Integer, nullable=False),
        sa.Column("baby_size_comparison", sa.String, nullable=False),
        sa.Column("development_note", sa.Text, nullable=False),
        sa.Column("image_url", sa.String, nullable=True),
    )

    op.create_table(
        "nutrition_guidance",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("category", PG_ENUM("IRON", "FOLIC_ACID", "HYDRATION", "FOODS_TO_AVOID", "HEALTHY_SNACKS", name="nutrition_category_enum", create_type=False), nullable=False, index=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("trimester_relevance", JSON, nullable=False, server_default="[]"),
        sa.Column("icon_url", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "baby_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("pregnancy_id", UUID(as_uuid=True), sa.ForeignKey("pregnancy_records.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("date_of_birth", sa.Date, nullable=False),
        sa.Column("gender", PG_ENUM("MALE", "FEMALE", "OTHER", name="baby_gender_enum", create_type=False), nullable=True),
        sa.Column("birth_weight_kg", sa.Float, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_table(
        "epds_screenings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("answers", JSON, nullable=False),
        sa.Column("total_score", sa.Integer, nullable=False),
        sa.Column("q10_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_self_harm_flagged", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("risk_level", PG_ENUM("LOW", "MEDIUM", "HIGH", "SELF_HARM_RISK", name="epds_risk_level_enum", create_type=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ------------------------------------------------------------------ #
    # 4. Seed: MOH ANC Pathway Template                                   #
    # ------------------------------------------------------------------ #
    anc_milestones = [
        {"order": 1, "label": "1st ANC visit", "triggerWeek": 8, "description": "Initial booking visit — blood tests, history, baseline measurements"},
        {"order": 2, "label": "2nd ANC visit", "triggerWeek": 16, "description": "Review blood results, fetal growth assessment"},
        {"order": 3, "label": "3rd ANC visit", "triggerWeek": 20, "description": "Anatomy scan review, risk stratification"},
        {"order": 4, "label": "4th ANC visit", "triggerWeek": 26, "description": "Glucose tolerance test, blood pressure check"},
        {"order": 5, "label": "5th ANC visit", "triggerWeek": 30, "description": "Fetal position, growth and wellbeing assessment"},
        {"order": 6, "label": "6th ANC visit", "triggerWeek": 34, "description": "Birth plan discussion, Group B strep test"},
        {"order": 7, "label": "7th ANC visit", "triggerWeek": 36, "description": "Presentation check, finalise birth plan"},
        {"order": 8, "label": "8th ANC visit", "triggerWeek": 38, "description": "Pre-labour check, wellbeing assessment"},
    ]
    op.execute(
        sa.text("""
            INSERT INTO care_pathway_templates (id, name, description, milestones, is_active)
            VALUES (:id, :name, :description, CAST(:milestones AS JSON), :is_active)
        """).bindparams(
            id="path_anc_moh_v1",
            name="MOH Standard 8-Visit ANC Pathway",
            description="Kenya Ministry of Health recommended antenatal care schedule covering weeks 8 through 38",
            milestones=json.dumps(anc_milestones),
            is_active=True,
        )
    )    # Form template insertion skipped here to avoid Postgres "unsafe use of new enum value in same transaction" error.

    # ------------------------------------------------------------------ #
    # 6. Seed: Week Info (weeks 1–42)                                     #
    # ------------------------------------------------------------------ #
    week_data = [
        (1,  1, "A poppy seed",          "The fertilised egg has implanted. The placenta and amniotic sac are beginning to form."),
        (2,  1, "A poppy seed",          "Hormonal changes are preparing your body for the journey ahead."),
        (3,  1, "A sesame seed",         "The embryo is forming its basic structures — the neural tube begins to develop."),
        (4,  1, "A peppercorn",          "Your embryo is the size of a peppercorn. The heart and major organs are starting to form."),
        (5,  1, "An apple seed",         "The heart begins to beat. The embryo's face, eyes and ears are taking shape."),
        (6,  1, "A sweet pea",           "The tiny heart is now beating about 100–160 times per minute. Fingers and toes are starting to bud."),
        (7,  1, "A blueberry",           "The brain is growing rapidly. Hands and feet are forming, though they look like paddles for now."),
        (8,  1, "A kidney bean",         "Your baby's fingers and toes are becoming distinct. All major organs are present in early form."),
        (9,  1, "A grape",              "Teeth buds, eyelids and ears are developing. Your baby can make tiny movements."),
        (10, 1, "A strawberry",          "Vital organs are fully formed and starting to work together. The baby is officially a foetus."),
        (11, 1, "A fig",                "Your baby can open and close its fists. Tooth buds are developing beneath the gums."),
        (12, 1, "A lime",               "Your baby's reflexes are developing. The kidneys start producing urine."),
        (13, 2, "A lemon",              "The placenta is now fully functioning. Your baby can smile, frown and even suck its thumb."),
        (14, 2, "A peach",              "Fine, downy hair called lanugo covers your baby's body to keep it warm."),
        (15, 2, "An apple",             "Your baby is now moving regularly, though you may not feel it yet. Bones are hardening."),
        (16, 2, "An avocado",           "Your baby's head is more erect. Its ears are now in their final position — it can hear your voice."),
        (17, 2, "A turnip",             "Your baby is putting on fat stores. The umbilical cord is growing stronger and thicker."),
        (18, 2, "A sweet potato",       "You may start to feel movements — flutters or bubbles — for the first time this week."),
        (19, 2, "A mango",              "Your baby's senses are developing rapidly: hearing, vision, smell, taste and touch."),
        (20, 2, "A banana",             "Halfway there! Your baby has a regular sleep cycle and is practicing breathing movements."),
        (21, 2, "A carrot",             "Your baby can now swallow amniotic fluid and is practicing digestion."),
        (22, 2, "A papaya",             "Your baby's grip is firm enough to grip a finger. Eyebrows and lashes are visible."),
        (23, 2, "A large mango",        "Your baby can hear sounds from outside the womb — try talking or playing music."),
        (24, 2, "An ear of corn",       "Your baby's lungs are developing surfactant, preparing for breathing outside the womb."),
        (25, 2, "A rutabaga",           "Your baby now responds to your touch. Fat is filling in under the skin."),
        (26, 2, "A scallion",           "Your baby's eyes can now open and close. Brain activity is increasing significantly."),
        (27, 3, "A head of cauliflower","Third trimester begins! Your baby sleeps and wakes at regular intervals."),
        (28, 3, "A large eggplant",     "Your baby's brain is developing rapidly, forming the folds and grooves seen in a full-term brain."),
        (29, 3, "A butternut squash",   "Your baby's muscles and lungs are continuing to mature. Movements may feel stronger."),
        (30, 3, "A large cabbage",      "Your baby's bone marrow is fully in charge of producing red blood cells."),
        (31, 3, "A coconut",            "Your baby's bones are hardening, though the skull stays soft and flexible for delivery."),
        (32, 3, "A jicama",             "Your baby is practising breathing by inhaling and exhaling amniotic fluid."),
        (33, 3, "A pineapple",          "Your baby is keeping its eyes open while awake and can detect light changes."),
        (34, 3, "A cantaloupe",         "Your baby's central nervous system is maturing. Most internal systems are ready."),
        (35, 3, "A honeydew melon",     "Your baby is running out of room to move. Movements may feel different — less rolling, more poking."),
        (36, 3, "A head of romaine lettuce", "Your baby sheds its lanugo and vernix as it prepares for birth."),
        (37, 3, "A bunch of Swiss chard", "Your baby is considered early-term. The lungs and brain are nearly fully mature."),
        (38, 3, "A leek",              "Your baby is full-term and ready to be born any day. All organs are fully developed."),
        (39, 3, "A small watermelon",   "Your baby's head may have dropped lower into your pelvis, known as lightening or engagement."),
        (40, 3, "A small pumpkin",      "Your due date is here. Your baby is fully formed and ready for the world."),
        (41, 3, "A pumpkin",            "You're in the 'overdue' zone. Your care team is monitoring both of you closely."),
        (42, 3, "A large pumpkin",      "Post-term pregnancy. Your care team will discuss delivery options with you today."),
    ]

    base_url = "https://cdn.bintic.care/pregnancy"
    for week, trimester, size, note in week_data:
        op.execute(
            sa.text("""
                INSERT INTO pregnancy_week_info (id, week_number, trimester, baby_size_comparison, development_note, image_url)
                VALUES (CAST(:id AS UUID), :week_number, :trimester, :baby_size_comparison, :development_note, :image_url)
            """).bindparams(
                id=str(uuid.uuid4()),
                week_number=week,
                trimester=trimester,
                baby_size_comparison=size,
                development_note=note,
                image_url=f"{base_url}/week{week}.png",
            )
        )

    # ------------------------------------------------------------------ #
    # 7. Seed: Nutrition Guidance                                         #
    # ------------------------------------------------------------------ #
    nutrition_data = [
        ("IRON", "Why iron-rich foods matter this trimester",
         "Iron needs increase significantly in the second and third trimesters. Eat iron-rich foods like dark leafy greens, legumes, lean red meat, and fortified cereals. Pair with vitamin C to boost absorption. Low iron can lead to anaemia, fatigue and increased risk of complications.",
         [1, 2, 3], "https://cdn.bintic.care/nutrition/iron.png"),
        ("IRON", "Overcoming iron-deficiency anaemia through diet",
         "If your iron levels are low, focus on haem iron from animal sources (beef liver, chicken, fish) and non-haem iron from plant sources (lentils, spinach, tofu). Avoid drinking tea or coffee with meals as they block iron absorption.",
         [2, 3], "https://cdn.bintic.care/nutrition/iron2.png"),
        ("FOLIC_ACID", "Folic acid in early pregnancy",
         "Folic acid is critical in the first trimester for preventing neural tube defects. Take a daily 400mcg supplement alongside folate-rich foods like broccoli, fortified breakfast cereals, and asparagus. Continue throughout the pregnancy.",
         [1], "https://cdn.bintic.care/nutrition/folic.png"),
        ("FOLIC_ACID", "Foods rich in folate",
         "Natural folate is found in dark leafy vegetables (kale, spinach), legumes (lentils, black beans), avocado, and fortified grain products. Cooking destroys some folate — eating raw or lightly steamed vegetables preserves more.",
         [1, 2, 3], "https://cdn.bintic.care/nutrition/folate_foods.png"),
        ("HYDRATION", "Staying hydrated throughout pregnancy",
         "Aim for 8–10 glasses of water daily. Proper hydration prevents urinary tract infections, supports amniotic fluid levels, reduces swelling, and prevents constipation. Coconut water and fresh fruit juices also count.",
         [1, 2, 3], "https://cdn.bintic.care/nutrition/hydration.png"),
        ("HYDRATION", "Signs of dehydration to watch for",
         "Dark yellow urine, headaches, dizziness and reduced foetal movement can all be signs of dehydration. Increase your fluid intake immediately and contact your midwife if symptoms persist or if you experience reduced baby movement.",
         [2, 3], "https://cdn.bintic.care/nutrition/dehydration.png"),
        ("FOODS_TO_AVOID", "Foods to avoid during pregnancy",
         "Avoid raw or undercooked meat, fish, and eggs; unpasteurised dairy products; liver in large amounts; high-mercury fish (shark, swordfish, king mackerel); raw sprouts; and unpasteurised juices. These can harbour bacteria or toxins harmful to your baby.",
         [1, 2, 3], "https://cdn.bintic.care/nutrition/avoid.png"),
        ("FOODS_TO_AVOID", "Caffeine and alcohol during pregnancy",
         "Limit caffeine to under 200mg per day (about one cup of coffee). Alcohol has no known safe level during pregnancy — avoid it completely. Both cross the placenta and can affect your baby's development.",
         [1, 2, 3], "https://cdn.bintic.care/nutrition/caffeine.png"),
        ("FOODS_TO_AVOID", "Managing heartburn through diet",
         "Heartburn is common in the third trimester as the baby pushes against your stomach. Avoid spicy, fatty, or acidic foods. Eat smaller meals more frequently, remain upright after eating, and sleep with your head slightly elevated.",
         [3], "https://cdn.bintic.care/nutrition/heartburn.png"),
        ("HEALTHY_SNACKS", "Nutritious snacks for pregnancy energy",
         "Keep your energy up between meals with snacks like mixed nuts and seeds, Greek yoghurt with fruit, whole-grain crackers with hummus, sliced avocado, or a hard-boiled egg. These provide protein, healthy fats and slow-release energy.",
         [1, 2, 3], "https://cdn.bintic.care/nutrition/snacks.png"),
        ("HEALTHY_SNACKS", "Iron and calcium snack combos",
         "Maximise nutrient absorption with strategic snack pairings. Try spinach and cheese omelette strips, nut butter on wholegrain toast with a glass of orange juice, or trail mix with fortified cereal. Avoid pairing calcium-rich foods with iron-rich ones in the same snack.",
         [2, 3], "https://cdn.bintic.care/nutrition/combo_snacks.png"),
        ("HEALTHY_SNACKS", "Snacks to manage nausea in the first trimester",
         "Eat small, frequent snacks to keep your stomach from becoming empty. Ginger biscuits, plain crackers, banana slices and cold fruit can ease nausea. Keep dry crackers by your bedside to eat before getting up in the morning.",
         [1], "https://cdn.bintic.care/nutrition/nausea_snacks.png"),
    ]

    for category, title, summary, trimester_relevance, icon_url in nutrition_data:
        op.execute(
            sa.text("""
                INSERT INTO nutrition_guidance (id, category, title, summary, trimester_relevance, icon_url)
                VALUES (CAST(:id AS UUID), CAST(:category AS nutrition_category_enum), :title, :summary, CAST(:trimester_relevance AS JSON), :icon_url)
            """).bindparams(
                id=str(uuid.uuid4()),
                category=category,
                title=title,
                summary=summary,
                trimester_relevance=json.dumps(trimester_relevance),
                icon_url=icon_url,
            )
        )


def downgrade() -> None:
    op.drop_table("epds_screenings")
    op.drop_table("baby_profiles")
    op.drop_table("nutrition_guidance")
    op.drop_table("pregnancy_week_info")
    op.drop_table("pregnancy_risk_scores")
    op.drop_table("vitals_feedback")
    op.drop_table("pregnancy_vitals_entries")
    op.drop_table("scheduled_visits")
    op.drop_table("care_pathway_templates")
    op.drop_table("pregnancy_records")

    op.execute("DROP TYPE IF EXISTS epds_risk_level_enum")
    op.execute("DROP TYPE IF EXISTS baby_gender_enum")
    op.execute("DROP TYPE IF EXISTS nutrition_category_enum")
    op.execute("DROP TYPE IF EXISTS risk_level_enum")
    op.execute("DROP TYPE IF EXISTS visit_status_enum")
    op.execute("DROP TYPE IF EXISTS pregnancy_outcome_enum")
    op.execute("DROP TYPE IF EXISTS pregnancy_status_enum")
