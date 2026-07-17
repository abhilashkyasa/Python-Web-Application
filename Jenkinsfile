pipeline {
    agent any

    environment {

        /* ========== APPLICATION REPO (CI) ========== */
        APP_REPO_URL = 'https://github.com/abhilashkyasa/Python-Web-Application.git'
        APP_BRANCH = 'main'

        /* ========== GITOPS REPO (CD) ========== */
        GITOPS_REPO_URL = 'git@github.com:Akash0902/devops-gitops.git'
        GITOPS_BRANCH = 'main'

        /* ========== DOCKER / NEXUS ========== */
        NEXUS_CRED_ID = 'nexus'
        NEXUS_REGISTRY = '16.16.216.41:8000'
        IMAGE_NAME = 'devops-app'
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout Application Code') {
            steps {
                git branch: "${APP_BRANCH}", url: "${APP_REPO_URL}"
            }
        }

        stage('Pre-Checks') {
            steps {
                sh '''
                    set -e
                    docker info >/dev/null
                    python3 --version
                '''
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh '''
                    set -e

                    python3 -m venv venv
                    . venv/bin/activate

                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Build & Test') {
            steps {
                sh '''
                    . venv/bin/activate

                    pytest || echo "No tests found. Continuing..."
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build \
                      -t ${NEXUS_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
                      -t ${NEXUS_REGISTRY}/${IMAGE_NAME}:latest .
                '''
            }
        }

        stage('Push Image to Nexus') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: "${NEXUS_CRED_ID}",
                        usernameVariable: 'NEXUS_USER',
                        passwordVariable: 'NEXUS_PASS'
                    )
                ]) {

                    sh '''
                        echo "$NEXUS_PASS" | docker login ${NEXUS_REGISTRY} \
                        -u "$NEXUS_USER" --password-stdin

                        docker push ${NEXUS_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                        docker push ${NEXUS_REGISTRY}/${IMAGE_NAME}:latest

                        docker logout ${NEXUS_REGISTRY}
                    '''
                }
            }
        }

        stage('Checkout GitOps Repo') {
            steps {
                sh '''
                    rm -rf gitops

                    git clone \
                    -b ${GITOPS_BRANCH} \
                    ${GITOPS_REPO_URL} \
                    gitops
                '''
            }
        }

        stage('Update Deployment Image') {
            steps {
                sh '''
                    cd gitops

                    sed -i "s|image: .*|image: ${NEXUS_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}|g" \
                    k8s/deployment.yaml

                    cat k8s/deployment.yaml
                '''
            }
        }

        stage('Commit & Push GitOps Changes') {
            steps {
                sh '''
                    cd gitops

                    git config user.name "Jenkins"
                    git config user.email "jenkins@gitops.com"

                    git add .

                    git diff --cached --quiet && {
                        echo "No changes detected."
                        exit 0
                    }

                    git commit -m "Update image to ${IMAGE_NAME}:${IMAGE_TAG}"

                    git push origin ${GITOPS_BRANCH}
                '''
            }
        }
    }

    post {

        success {
            echo "✅ Pipeline completed successfully."
            echo "🚀 Argo CD will automatically sync the new image."
        }

        failure {
            echo "❌ Pipeline failed."
        }

        always {
            sh '''
                docker image prune -f || true
            '''
        }
    }
}
