pipeline {
  agent any
  options { timestamps() }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Setup Virtual Environment') {
      steps {
        sh 'python3 -m venv venv'
        sh '. venv/bin/activate && python --version'
      }
    }

    stage('Install Dependencies') {
      steps {
        sh '. venv/bin/activate && python -m pip install --upgrade pip setuptools wheel'
        sh '. venv/bin/activate && python -m pip install -r requirements.txt'
      }
    }

    stage('Run Tests') {
      steps {
        sh '. venv/bin/activate && pytest -q'
      }
    }

    stage('Docker Build') {
      steps {
        sh 'docker build -t aceest-fitness:${BUILD_NUMBER} .'
      }
    }
  }

  post {
    success { echo 'Pipeline passed' }
    failure { echo 'Pipeline failed' }
  }
}