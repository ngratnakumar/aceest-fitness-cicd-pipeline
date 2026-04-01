import os
from functools import wraps
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
os.makedirs(app.instance_path, exist_ok=True)
database_path = Path(app.instance_path) / f'aceest_fitness_{os.getpid()}.db'

# --- CONFIGURATION ---
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


def initialize_database():
    db.create_all()

    default_admin = User.query.filter_by(username='admin').first()
    if default_admin is None:
        db.session.add(
            User(
                username='admin',
                password=generate_password_hash('admin123', method='pbkdf2:sha256'),
                role='admin',
            )
        )
        db.session.commit()

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
    return render_template('dashboard.html', assigned_trainer=current_user.assigned_trainer)


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
    assigned_users = User.query.filter_by(trainer_id=current_user.id, role='user').order_by(User.username).all()
    trainer_profile = current_user.trainer_profile
    return render_template(
        'trainer_dashboard.html',
        assigned_users=assigned_users,
        trainer_profile=trainer_profile,
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

@app.route('/health')
def health():
    return {"status": "running", "database": "connected"}

# --- INITIALIZATION ---

with app.app_context():
    initialize_database()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
