import os
import random
import re
from pathlib import Path
from werkzeug.security import generate_password_hash
import logging
from datetime import datetime
from sqlalchemy.sql.schema import Column

# ---- Step 1: delete existing sqlite DB files before importing app ----
PROJECT_ROOT = Path(__file__).resolve().parent
INSTANCE_DIR = PROJECT_ROOT / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

# ---- Logger setup ----
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOGS_DIR / f"{timestamp}_seed.log"

logger = logging.getLogger("seed_logger")
logger.setLevel(logging.INFO)
logger.handlers.clear()

file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.info("Seeder started")
logger.info("Log file: %s", log_file.as_posix())

for db_file in INSTANCE_DIR.glob("*.db"):
    try:
        db_file.unlink()
        logger.info("Deleted old DB: %s", db_file.name)
    except Exception:
        logger.exception("Could not delete DB: %s", db_file.name)

# enforce a single stable DB filename
os.environ["ACEEST_DB_FILE"] = "aceest_fitness.db"

# ---- Step 2: import app/models after cleanup ----
from app import app, db, User, Trainer, Member, WorkoutPlan  # noqa: E402

random.seed(42)

USER_NAMES = [
    "Aarav Sharma", "Vivaan Patel", "Aditya Verma", "Arjun Reddy", "Sai Krishna",
    "Rohan Mehta", "Karthik Iyer", "Nikhil Joshi", "Rahul Nair", "Siddharth Rao",
]

TRAINERS = [
    ("Yasmin Karachiwala", "Strength & Conditioning"),
    ("Namrata Purohit", "Pilates"),
    ("Prashant Sawant", "Weight Loss"),
    ("Vinod Channa", "Bodybuilding"),
    ("Deanne Pandey", "Functional Fitness"),
    ("Sahil Khan", "Muscle Gain"),
    ("Rujuta Diwekar", "Nutrition Coaching"),
    ("Mickey Mehta", "Holistic Fitness"),
    ("Sangeeta Sharma", "Yoga & Mobility"),
    ("Shivoham", "HIIT & Endurance"),
]

WORKOUTS = [
    ("Fat Loss Starter", "Walk 30 min, squats 3x12, pushups 3x10, plank 3x30s"),
    ("Strength Foundation", "Squat, deadlift, bench; 3 sets each"),
    ("Mobility Flow", "Hip opener, shoulder mobility, hamstring stretch"),
    ("HIIT Blast", "20 min intervals: burpees, jump squats, mountain climbers"),
    ("Home Full Body", "Lunges, pushups, glute bridge, core circuit"),
]

def uname(name: str, prefix: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]", "", name.lower())  # no spaces
    value = f"{prefix}{base}"
    i = 1
    while value in used:
        i += 1
        value = f"{prefix}{base}{i}"
    used.add(value)
    return value

def model_columns(model):
    return {c.name for c in model.__table__.columns}

def model_required_columns(model):
    req = []
    for c in model.__table__.columns:  # type: Column
        if c.primary_key:
            continue
        if not c.nullable and c.default is None and c.server_default is None:
            req.append(c.name)
    return set(req)

def safe_kwargs(model, data: dict) -> dict:
    cols = model_columns(model)
    return {k: v for k, v in data.items() if k in cols}

def ensure_required_fields(model, payload: dict, full_name: str, username: str, trainer_id=None, user_id=None):
    required = model_required_columns(model)
    cols = model_columns(model)

    # smart defaults for common required fields
    defaults = {
        "name": full_name,
        "username": username,
        "email": f"{username}@example.com",
        "plan": "Starter Plan",  # fixes NOT NULL member.plan
        "trainer_id": trainer_id,
        "user_id": user_id,
    }

    for key in required:
        if key not in payload or payload[key] is None or payload[key] == "":
            if key in defaults and key in cols:
                payload[key] = defaults[key]
            elif key in cols:
                payload[key] = "N/A"

    return payload

def create_member_for_user(user_obj, trainer_obj, full_name: str):
    # Build a flexible payload; only valid keys will be used.
    candidate = {
        "user_id": user_obj.id,
        "trainer_id": trainer_obj.id,
        "name": full_name,
        "username": user_obj.username,
        "email": f"{user_obj.username}@example.com",
    }
    kwargs = safe_kwargs(Member, candidate)
    if kwargs:
        db.session.add(Member(**kwargs))

def seed():
    with app.app_context():
        try:
            logger.info("Dropping all tables")
            db.drop_all()
            logger.info("Creating all tables")
            db.create_all()

            used = set()

            logger.info("Creating admin user")
            admin_data = {
                "username": "admin",
                "password": generate_password_hash("admin123", method="pbkdf2:sha256"),
                "role": "admin",
            }
            db.session.add(User(**safe_kwargs(User, admin_data)))
            db.session.flush()
            used.add("admin")

            trainer_users = []
            for name, spec in TRAINERS:
                t_user_data = {
                    "username": uname(name, "trainer_", used),
                    "password": generate_password_hash("trainer123", method="pbkdf2:sha256"),
                    "role": "trainer",
                }
                t_user = User(**safe_kwargs(User, t_user_data))
                db.session.add(t_user)
                db.session.flush()

                t_profile_data = {
                    "user_id": t_user.id,
                    "name": name,
                    "specialization": spec,
                }
                db.session.add(Trainer(**safe_kwargs(Trainer, t_profile_data)))
                trainer_users.append(t_user)

            logger.info("Created trainers: %d", len(trainer_users))

            user_cols = model_columns(User)
            user_pairs = []

            for full_name in USER_NAMES:
                t = random.choice(trainer_users)

                u_data = {
                    "username": uname(full_name, "user_", used),
                    "password": generate_password_hash("user123", method="pbkdf2:sha256"),
                    "role": "user",
                    "trainer_id": t.id if "trainer_id" in user_cols else None,
                }
                u = User(**safe_kwargs(User, u_data))
                db.session.add(u)
                db.session.flush()

                member_data = {
                    "user_id": u.id,
                    "trainer_id": t.id,
                    "name": full_name,
                    "username": u.username,
                    "email": f"{u.username}@example.com",
                    "plan": random.choice(WORKOUTS)[0],  # required in your schema
                }
                member_data = ensure_required_fields(
                    Member, member_data, full_name=full_name, username=u.username, trainer_id=t.id, user_id=u.id
                )
                member_kwargs = safe_kwargs(Member, member_data)
                if member_kwargs:
                    db.session.add(Member(**member_kwargs))

                user_pairs.append((u, t))

            logger.info("Created users: %d", len(user_pairs))

            plan_count = 0
            for u, t in user_pairs:
                for _ in range(random.randint(1, 3)):
                    title, details = random.choice(WORKOUTS)
                    wp_data = {
                        "title": title,
                        "details": details,
                        "trainer_id": t.id,
                        "user_id": u.id,
                    }
                    wp_kwargs = safe_kwargs(WorkoutPlan, wp_data)
                    if wp_kwargs:
                        db.session.add(WorkoutPlan(**wp_kwargs))
                        plan_count += 1

            db.session.commit()
            logger.info("Seed complete")
        except Exception:
            db.session.rollback()
            logger.exception("Seeder failed")
            raise

if __name__ == "__main__":
    seed()