import os
from functools import wraps
from pathlib import Path
from sqlalchemy import text

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
os.makedirs(app.instance_path, exist_ok=True)

DB_FILENAME = os.environ.get("ACEEST_DB_FILE", "aceest_fitness.db")
database_path = Path(app.instance_path) / DB_FILENAME

app.config['SECRET_KEY'] = 'aceest_fitness_secret_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + database_path.as_posix()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

ALLOWED_ROLES = {'user', 'trainer', 'admin'}

# --- DATABASE MODELS ---

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='user')
    trainer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_trainer = db.relationship(
        'User',
        remote_side=[id],
        foreign_keys=[trainer_id],
        backref=db.backref('assigned_users', lazy='dynamic'),
        lazy='joined',
    )

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    plan = db.Column(db.String(50), nullable=False)

class Trainer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    user = db.relationship('User', backref=db.backref('trainer_profile', uselist=False), foreign_keys=[user_id])

class WorkoutPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    details = db.Column(db.Text, nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    trainer = db.relationship('User', foreign_keys=[trainer_id], backref='created_workout_plans')
    user = db.relationship('User', foreign_keys=[user_id], backref='workout_plans')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def role_required(*roles):
    def decorator(view_function):
        @wraps(view_function)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('dashboard'))
            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator


def _ensure_user_trainer_id_column():
    # SQLite schema patch for old DBs
    cols = db.session.execute(text('PRAGMA table_info("user")')).fetchall()
    col_names = {row[1] for row in cols}  # row[1] = column name
    if "trainer_id" not in col_names:
        db.session.execute(text('ALTER TABLE "user" ADD COLUMN trainer_id INTEGER'))
        db.session.commit()

def initialize_database():
    with app.app_context():
        db.create_all()
        _ensure_user_trainer_id_column()  # must run BEFORE any User query

        default_admin = User.query.filter_by(username='admin').first()
        if not default_admin:
            default_admin = User(
                username='admin',
                password=generate_password_hash('admin123', method='pbkdf2:sha256'),
                role='admin'
            )
            db.session.add(default_admin)
            db.session.commit()


def _dashboard_endpoint_for(user):
    if user.role == 'admin':
        return 'admin_dashboard'
    if user.role == 'trainer':
        return 'trainer_dashboard'
    return 'dashboard'

# --- ROUTES ---

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'user').strip().lower()

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return redirect(url_for('register'))

        if role not in ALLOWED_ROLES:
            role = 'user'

        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_pw, role=role)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            if user.role == 'trainer':
                return redirect(url_for('trainer_dashboard'))
            return redirect(url_for('dashboard'))
        
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    if current_user.role == 'trainer':
        return redirect(url_for('trainer_dashboard'))

    workout_plans = WorkoutPlan.query.filter_by(user_id=current_user.id).order_by(WorkoutPlan.id.desc()).all()
    return render_template(
        'dashboard.html',
        assigned_trainer=current_user.assigned_trainer,
        workout_plans=workout_plans,
    )

@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    users = User.query.filter_by(role='user').order_by(User.username).all()
    trainers = User.query.filter_by(role='trainer').order_by(User.username).all()
    trainer_profiles = Trainer.query.join(User, Trainer.user_id == User.id).order_by(User.username).all()
    return render_template(
        'admin_dashboard.html',
        users=users,
        trainers=trainers,
        trainer_profiles=trainer_profiles,
    )


@app.route('/admin/trainers', methods=['POST'])
@login_required
@role_required('admin')
def create_trainer():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    name = request.form.get('name', '').strip()
    specialization = request.form.get('specialization', '').strip()

    if not all([username, password, name, specialization]):
        flash('Fill in all trainer fields.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if User.query.filter_by(username=username).first():
        flash('Trainer username already exists!', 'danger')
        return redirect(url_for('admin_dashboard'))

    trainer_user = User(
        username=username,
        password=generate_password_hash(password, method='pbkdf2:sha256'),
        role='trainer',
    )
    db.session.add(trainer_user)
    db.session.flush()

    trainer_profile = Trainer(
        user_id=trainer_user.id,
        name=name,
        specialization=specialization,
    )
    db.session.add(trainer_profile)
    db.session.commit()

    flash('Trainer added successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/assign-trainer', methods=['POST'])
@login_required
@role_required('admin')
def assign_trainer():
    user_id = request.form.get('user_id', type=int)
    trainer_id = request.form.get('trainer_id', type=int)

    user = db.session.get(User, user_id)
    trainer = db.session.get(User, trainer_id)

    if user is None or trainer is None:
        flash('User or trainer not found.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if user.role != 'user' or trainer.role != 'trainer':
        flash('Pick a normal user and a trainer account.', 'danger')
        return redirect(url_for('admin_dashboard'))

    user.assigned_trainer = trainer
    db.session.commit()

    flash(f'{user.username} is now assigned to {trainer.username}.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/trainers/<int:trainer_user_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_trainer(trainer_user_id):
    trainer_user = User.query.get_or_404(trainer_user_id)

    if trainer_user.role != 'trainer':
        flash('That account is not a trainer.', 'danger')
        return redirect(url_for('admin_dashboard'))

    assigned_users = User.query.filter_by(trainer_id=trainer_user.id).all()
    for assigned_user in assigned_users:
        assigned_user.assigned_trainer = None

    Trainer.query.filter_by(user_id=trainer_user.id).delete()
    db.session.delete(trainer_user)
    db.session.commit()

    flash('Trainer removed.', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/trainer')
@login_required
@role_required('trainer')
def trainer_dashboard():
    trainer_profile = Trainer.query.filter_by(user_id=current_user.id).first()
    assigned_users = User.query.filter_by(
        trainer_id=current_user.id,
        role='user'
    ).order_by(User.username).all()

    user_search = request.args.get('user', '').strip().lower()

    plans_query = WorkoutPlan.query.filter_by(trainer_id=current_user.id)

    if user_search:
        matching_user_ids = [u.id for u in assigned_users if user_search in u.username.lower()]
        plans_query = plans_query.filter(WorkoutPlan.user_id.in_(matching_user_ids or [-1]))

    workout_plans = plans_query.order_by(WorkoutPlan.id.desc()).all()
    assigned_user_map = {u.id: u.username for u in assigned_users}

    return render_template(
        'trainer_dashboard.html',
        trainer_profile=trainer_profile,
        assigned_users=assigned_users,
        workout_plans=workout_plans,
        assigned_user_map=assigned_user_map,
        user_search=user_search,
    )

@app.route('/trainer/workout-plans', methods=['POST'])
@login_required
@role_required('trainer')
def create_workout_plan():
    title = request.form.get('title', '').strip()
    details = request.form.get('details', '').strip()
    user_id = request.form.get('user_id', type=int)

    if not title or not details or not user_id:
        flash('All fields are required.', 'danger')
        return redirect(url_for('trainer_dashboard'))

    user = User.query.filter_by(id=user_id, role='user', trainer_id=current_user.id).first()
    if not user:
        flash('Selected user is not assigned to you.', 'danger')
        return redirect(url_for('trainer_dashboard'))

    plan = WorkoutPlan(
        title=title,
        details=details,
        trainer_id=current_user.id,
        user_id=user.id,
    )
    db.session.add(plan)
    db.session.commit()

    flash('Workout plan created successfully.', 'success')
    return redirect(url_for('trainer_dashboard'))

@app.route('/trainer/workout-plans/<int:plan_id>/delete', methods=['POST'])
@login_required
@role_required('trainer')
def delete_workout_plan(plan_id):
    plan = WorkoutPlan.query.filter_by(id=plan_id, trainer_id=current_user.id).first_or_404()
    db.session.delete(plan)
    db.session.commit()
    flash('Workout plan deleted successfully.', 'success')
    return redirect(url_for('trainer_dashboard'))

@app.route('/trainer/workout-plans/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('trainer')
def edit_workout_plan(plan_id):
    plan = WorkoutPlan.query.filter_by(id=plan_id, trainer_id=current_user.id).first_or_404()
    assigned_users = User.query.filter_by(trainer_id=current_user.id, role='user').order_by(User.username).all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        details = request.form.get('details', '').strip()
        user_id = request.form.get('user_id', type=int)

        if not title or not details or not user_id:
            flash('All fields are required.', 'danger')
            return redirect(url_for('edit_workout_plan', plan_id=plan.id))

        selected_user = User.query.filter_by(
            id=user_id, role='user', trainer_id=current_user.id
        ).first()
        if not selected_user:
            flash('Selected user is not assigned to you.', 'danger')
            return redirect(url_for('edit_workout_plan', plan_id=plan.id))

        plan.title = title
        plan.details = details
        plan.user_id = selected_user.id
        db.session.commit()

        flash('Workout plan updated successfully.', 'success')
        return redirect(url_for('trainer_dashboard'))

    return render_template(
        'edit_workout_plan.html',
        plan=plan,
        assigned_users=assigned_users
    )

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# --- API ROUTES (Your existing Gym logic) ---

@app.route('/members', methods=['GET'])
def get_members():
    members = Member.query.all()
    return jsonify([{"id": m.id, "name": m.name, "plan": m.plan} for m in members])


@app.route('/members', methods=['POST'])
def add_member():
    payload = request.get_json(silent=True) or request.form
    name = payload.get('name', '').strip()
    plan = payload.get('plan', '').strip()

    if not name or not plan:
        return jsonify({'error': 'name and plan are required'}), 400

    member = Member(name=name, plan=plan)
    db.session.add(member)
    db.session.commit()

    return jsonify({"id": member.id, "name": member.name, "plan": member.plan}), 201

@app.route('/trainers')
def get_trainers():
    trainers = Trainer.query.join(User, Trainer.user_id == User.id).all()
    return jsonify([
        {
            "id": trainer.id,
            "name": trainer.name,
            "spec": trainer.specialization,
            "username": trainer.user.username,
        }
        for trainer in trainers
    ])


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not current_password or not new_password or not confirm_password:
            flash('All password fields are required.', 'danger')
            return redirect(url_for('change_password'))

        if not check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('change_password'))

        if new_password != confirm_password:
            flash('New password and confirm password do not match.', 'danger')
            return redirect(url_for('change_password'))

        if len(new_password) < 6:
            flash('New password must be at least 6 characters.', 'danger')
            return redirect(url_for('change_password'))

        current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()

        flash('Password updated successfully.', 'success')
        return redirect(url_for(_dashboard_endpoint_for(current_user)))

    return render_template('change_password.html')

@app.route('/health')
def health():
    return {"status": "running", "database": "connected"}

# --- INITIALIZATION ---

with app.app_context():
    initialize_database()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
