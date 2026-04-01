pipeline {
  agent any
  options { timestamps() }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Install Dependencies') {
      steps {
        sh 'python3 --version'
        sh 'pip3 --version'
        sh 'pip3 install --upgrade pip'
        sh 'pip3 install -r requirements.txt'
      }
    }

    stage('Run Tests') {
      steps {
        sh 'pytest -q'
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