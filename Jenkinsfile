pipeline {
  agent any

  environment {
    DOCKERHUB_USER = 'saifn7
    IMAGE_NAME     = "${DOCKERHUB_USER}/devops-webapp"
    IMAGE_TAG      = "${env.BUILD_NUMBER}"
    IMAGE          = "${IMAGE_NAME}:${IMAGE_TAG}"
    APP_URL        = 'http://localhost:30080'
  }

  triggers {
    githubPush()                  // webhook from GitHub (7.5)
    pollSCM('H/2 * * * *')        // fallback: check GitHub every 2 minutes
  }

  options {
    timestamps()
    buildDiscarder(logRotator(numToKeepStr: '10'))
    disableConcurrentBuilds()
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'git log -1 --oneline'
      }
    }

    stage('Unit tests') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install -q -r requirements.txt -r requirements-dev.txt
          mkdir -p reports
          pytest -v --junitxml=reports/junit.xml
        '''
      }
      post {
        always { junit 'reports/junit.xml' }
      }
    }

    stage('Build image') {
      steps {
        sh 'docker build --build-arg APP_VERSION=${IMAGE_TAG} -t ${IMAGE} -t ${IMAGE_NAME}:latest .'
      }
    }

    stage('Security scan (Trivy)') {
      steps {
        sh '''
          mkdir -p reports
          # full report of HIGH and CRITICAL findings, kept with the build
          trivy image --no-progress --severity HIGH,CRITICAL --format table -o reports/trivy-report.txt ${IMAGE}
          # quality gate: fail the build on any fixable CRITICAL vulnerability
          trivy image --no-progress --exit-code 1 --severity CRITICAL --ignore-unfixed ${IMAGE}
        '''
      }
      post {
        always { archiveArtifacts artifacts: 'reports/trivy-report.txt', allowEmptyArchive: true }
      }
    }

    stage('Push image') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                          usernameVariable: 'DH_USER',
                                          passwordVariable: 'DH_PASS')]) {
          sh '''
            echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
            docker push ${IMAGE}
            docker push ${IMAGE_NAME}:latest
          '''
        }
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        withCredentials([file(credentialsId: 'kind-kubeconfig', variable: 'KUBECONFIG')]) {
          sh '''
            kubectl apply -f k8s/namespace.yaml
            kubectl apply -f k8s/service.yaml
            sed "s|IMAGE_PLACEHOLDER|${IMAGE}|g" k8s/deployment.yaml | kubectl apply -f -
            kubectl -n webapp rollout status deployment/webapp --timeout=180s
            kubectl -n webapp get pods -o wide
          '''
        }
      }
    }

    stage('Smoke test') {
      steps {
        sh '''
          for i in 1 2 3 4 5 6; do
            if curl -fsS ${APP_URL}/health; then
              echo "\nSmoke test passed"
              curl -fsS ${APP_URL}/
              exit 0
            fi
            sleep 5
          done
          echo "Smoke test failed"
          exit 1
        '''
      }
    }
  }

  post {
    failure {
      withCredentials([file(credentialsId: 'kind-kubeconfig', variable: 'KUBECONFIG')]) {
        sh 'kubectl -n webapp rollout undo deployment/webapp || true'
      }
      echo "Build ${BUILD_NUMBER} failed; deployment rolled back if it had changed."
    }
    success {
      echo "Build ${BUILD_NUMBER} deployed ${IMAGE} to ${APP_URL}"
    }
    always {
      sh 'docker logout || true'
    }
  }
}
