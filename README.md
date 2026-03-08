# ACEest Fitness & Gym – CI/CD Pipeline Implementation

## Project Overview

This project demonstrates the implementation of a **modern DevOps CI/CD pipeline** for a Flask-based Gym Management application. The objective of the project is to automate the development lifecycle from **local development to automated build validation using Jenkins and GitHub Actions**.

The application simulates a simple **fitness and gym management system** that allows retrieval and management of gym members through REST API endpoints.

The DevOps pipeline ensures:

* Code version control using **Git and GitHub**
* Automated testing using **Pytest**
* Environment consistency using **Docker containerization**
* Continuous Integration using **GitHub Actions**
* Automated build validation using **Jenkins**

This setup ensures that every code change is automatically tested and verified before being considered stable.

---

# Technologies Used

| Technology     | Purpose                         |
| -------------- | ------------------------------- |
| Python (Flask) | Web application framework       |
| Git            | Version control system          |
| GitHub         | Remote repository hosting       |
| Pytest         | Unit testing framework          |
| Docker         | Containerization of application |
| GitHub Actions | Continuous Integration pipeline |
| Jenkins        | Automated build server          |
| VS Code        | Development environment         |

---

# Project Structure

```
ACEest-Fitness-Gym
│
├── app.py
├── requirements.txt
├── Dockerfile
├── README.md
├── .gitignore
│
├── tests
│   └── test_app.py
│
└── .github
    └── workflows
        └── main.yml
```

Description of key files:

* **app.py** – Flask web application
* **requirements.txt** – Python dependencies
* **Dockerfile** – Container configuration
* **tests/test_app.py** – Unit tests for API endpoints
* **main.yml** – GitHub Actions CI/CD pipeline
* **README.md** – Project documentation

---

# Application Features

The Flask application provides the following endpoints:

| Endpoint   | Method | Description           |
| ---------- | ------ | --------------------- |
| `/`        | GET    | Home endpoint         |
| `/members` | GET    | Retrieve gym members  |
| `/members` | POST   | Add new member        |
| `/health`  | GET    | Health check endpoint |

Example response:

```
GET /members

[
 { "id": 1, "name": "Rahul", "plan": "Premium" },
 { "id": 2, "name": "Anita", "plan": "Basic" }
]
```

---

# Local Development Setup

## 1. Clone the Repository

```
git clone https://github.com/ngratnakumar/aceest-fitness-cicd-pipeline.git
cd aceest-fitness-cicd-pipeline
```

---

## 2. Install Dependencies

```
pip install -r requirements.txt
```

---

## 3. Run the Flask Application

```
python app.py
```

The application will start on:

```
http://localhost:5000
```

---

# Running Unit Tests

This project uses **Pytest** for automated testing.

Run the test suite with:

```
pytest
```

Expected output:

```
3 passed in X seconds
```

The tests verify:

* Home endpoint response
* Members API functionality
* Health check endpoint

---

# Docker Containerization

Docker is used to package the application with all dependencies to ensure consistent execution across different environments.

## Build Docker Image

```
docker build -t aceest-fit-app .
```

## Run Docker Container

```
docker run -p 5000:5000 aceest-fit-app
```

Access the application:

```
http://localhost:5000
```

---

# Continuous Integration with GitHub Actions

The CI pipeline is implemented using **GitHub Actions**.

Pipeline configuration is located at:

```
.github/workflows/main.yml
```

The pipeline is triggered on:

* Push to repository
* Pull requests

## Pipeline Stages

1. Checkout source code
2. Setup Python environment
3. Install project dependencies
4. Execute Pytest test suite
5. Build Docker container

Example pipeline workflow:

```
Developer Push Code
        ↓
GitHub Repository
        ↓
GitHub Actions CI Pipeline
        ↓
Install Dependencies
        ↓
Run Unit Tests
        ↓
Build Docker Image
```

This ensures that every code change is validated automatically.

---

# Jenkins Build Integration

Jenkins is used as an additional **build validation layer**.

Jenkins performs the following steps:

1. Pull the latest code from GitHub
2. Install dependencies
3. Execute Pytest test suite
4. Build Docker image

Example Jenkins build script:

```
python3 -m pip install -r requirements.txt
python3 -m pytest
docker build -t aceest-fit-app .
```

This ensures that the application builds successfully in a **controlled CI environment**.

---

# DevOps Workflow Architecture

```
Developer (VS Code)
        │
        │ git push
        ▼
GitHub Repository
        │
        │ triggers
        ▼
GitHub Actions CI Pipeline
        │
        ├── Install Dependencies
        ├── Run Pytest Tests
        └── Build Docker Image
        │
        ▼
Jenkins Build Server
        │
        ├── Pull latest code
        ├── Install dependencies
        ├── Run tests
        └── Build Docker image
        │
        ▼
Validated Application Build
```

---

# Version Control Strategy

The project follows structured Git commits.

Examples:

```
feat: add flask gym management API
test: add pytest unit tests
docker: add Docker container configuration
ci: add GitHub Actions pipeline
docs: add README documentation
```

This approach improves traceability and maintainability.

---

# Future Improvements

Possible enhancements to the project include:

* Add user authentication
* Integrate a database (PostgreSQL / MySQL)
* Implement Docker Compose
* Deploy application to a cloud platform (AWS / Azure / GCP)
* Add code quality checks (Flake8, Black)

---

# Author

**BOLLAPRAGADA NAGA RATNA KUMAR**
**2025HT66015**
Introduction to DevOps (Assignment 1)

---

# License

This project is created for educational purposes as part of a DevOps CI/CD assignment.
