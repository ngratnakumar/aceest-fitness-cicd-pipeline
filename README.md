# ACEest Fitness & Gym - DevOps CI/CD Assignment

## Project Overview
Flask-based fitness management app with role-based access for:
- Admin
- Trainer
- User

Features:
- Login/logout
- User registration
- Trainer assignment
- Workout plan create/edit/delete
- User dashboard
- Trainer dashboard
- Seeded demo data
- Pytest coverage
- Docker containerization
- Jenkins pipeline
- GitHub Actions workflow

---

## Tech Stack
- Python 3.10+
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-Admin
- Pytest
- Docker
- Jenkins
- GitHub Actions

---

## Repository Structure
- `app.py` - Flask app
- `templates/` - HTML templates
- `tests/` - Pytest suite
- `seed_data.py` - Demo data seeder
- `Dockerfile` - App container image
- `jenkins.Dockerfile` - Jenkins container image
- `Jenkinsfile` - Jenkins pipeline
- `.github/workflows/main.yml` - GitHub Actions workflow
- `notes/` - Release notes

---

## Local Setup

### 1) Create virtual environment
```powershell
python -m venv venv
venv\Scripts\activate
```

### 2) Install dependencies
```powershell
pip install -r requirements.txt
```

### 3) Run application
```powershell
python app.py
```

Open:
- `http://127.0.0.1:5000`

---

## Seed Demo Data

Seeder creates:
- 10 trainers
- 10 users
- trainer-user mappings
- workout plans

Run:
```powershell
python seed_data.py
```

Default credentials:
- Admin: `admin / admin123`
- Trainer password: `trainer123`
- User password: `user123`

---

## Run Tests
```powershell
pytest -q
```

---

## Docker: Run Application

### Build image
```powershell
docker build -t aceest-fitness .
```

### Run container
```powershell
docker run -p 5000:5000 aceest-fitness
```

---

## Jenkins Setup Using Docker

### 1) Build Jenkins image
```powershell
docker build -f jenkins.Dockerfile -t jenkins-custom:latest .
```

### 2) Create Jenkins volume
```powershell
docker volume create jenkins_home
```

### 3) Run Jenkins container
```powershell
docker run -d --name jenkins `
  -p 8080:8080 -p 50000:50000 `
  -v jenkins_home:/var/jenkins_home `
  -v /var/run/docker.sock:/var/run/docker.sock `
  --restart unless-stopped `
  jenkins-custom:latest
```

### 4) Get Jenkins admin password
```powershell
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

### 5) Open Jenkins
Go to:
- `http://localhost:8080`

### 6) Initial Jenkins setup
- Paste admin password
- Install suggested plugins
- Create admin user
- Finish setup

---

## Jenkins Pipeline Execution

### Jenkinsfile
The repository includes `Jenkinsfile` in the root directory.

### Jenkins job setup
1. Open Jenkins dashboard
2. Click **New Item**
3. Enter job name, select **Pipeline**
4. Under **Pipeline**
   - Definition: `Pipeline script from SCM`
   - SCM: `Git`
   - Repository URL: your GitHub repo URL
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`
5. Save
6. Click **Build Now**

### Jenkins pipeline stages
- Checkout
- Setup Virtual Environment
- Install Dependencies
- Run Tests
- Docker Build

### Expected result
Pipeline should finish with:
- `Finished: SUCCESS`

---

## GitHub Actions
Workflow file:
- `.github/workflows/main.yml`

It should run on:
- `push`
- `pull_request`

Typical stages:
- Build / lint
- Docker image build
- Pytest execution

---

## Release Notes
Release notes are maintained in:
- `notes/v3.0.0.md`
- `notes/v3.1.0.md`
- `notes/v3.1.1.md`
- `notes/v3.1.2.md`
- `notes/v3.1.3.md`

---

## Validation Checklist
- App runs locally
- Seeder works
- Pytest passes
- Docker build succeeds
- Jenkins pipeline succeeds
- GitHub Actions workflow succeeds
- README and release notes are present

---

## Demo Credentials
- Admin: `admin / admin123`
- Trainer: `trainer123`
- User: `user123`

---
