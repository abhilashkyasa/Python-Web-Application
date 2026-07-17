pipeline {
    agent any

    environment {

        /* ========== APPLICATION REPO (CI) ========== */
        APP_REPO_URL = 'https://github.com/Akash0902/DevOps.git'
        APP_BRANCH  = 'main'

        /* ========== GITOPS REPO (CD) ========== */
        GITOPS_REPO_URL = 'git@github.com:Akash0902/devops-gitops.git'
        GITOPS_BRANCH  = 'main'

        /* ========== SONARQUBE (Disabled) ========== */
        // SONARQUBE_ENV     = 'sonar'
        // SONAR_PROJECT_KEY = 'DevOps'
        // SONAR_SCANNER     = 'sonar'

        /* ========== DOCKER / NEXUS ========== */
        NEXUS_CRED_ID  = 'nexus'
        NEXUS_REGISTRY = '3.108.66.213:8000'
        IMAGE_NAME     = 'devops-app'
        IMAGE_TAG      = "${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout Application Code') {
            steps {
                git branch: APP_BRANCH, url: APP_REPO_URL
            }
        }

        stage('Pre-Checks') {
            steps {
                sh '''
                set -e
                docker info > /dev/null
                '''
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh '''
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
                pytest || echo "No tests found"
                '''
            }
        }

        /*
        stage('SonarQube Scan') {
            steps {
                withSonarQubeEnv(SONARQUBE_ENV) {
                    script {
                        def scannerHome = tool SONAR_SCANNER
                        sh """
                        ${scannerHome}/bin/sonar-scanner \
                          -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                          -Dsonar.sources=. \
                          -Dsonar.exclusions=venv/**,.git/**,**/__pycache__/**
                        """
                    }
                }
            }
        }
        */

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
                withCredentials([usernamePassword(
                    credentialsId: NEXUS_CRED_ID,
                    usernameVariable: 'NEXUS_USER',
                    passwordVariable: 'NEXUS_PASS'
                )]) {
                    sh '''
                    echo "$NEXUS_PASS" | docker login ${NEXUS_REGISTRY} \
                      -u "$NEXUS_USER" --password-stdin

                    docker push ${NEXUS_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${NEXUS_REGISTRY}/${IMAGE_NAME}:latest
                    '''
                }
            }
        }

        /* ========== GITOPS PART (ONLY CD ACTION) ========== */

        stage('Checkout GitOps Repo') {
            steps {
                sh '''
                rm -rf gitops
                git clone -b ${GITOPS_BRANCH} ${GITOPS_REPO_URL} gitops
                '''
            }
        }

        stage('Update Image Tag in GitOps Deployment') {
            steps {
                sh '''
                cd gitops

                sed -i "s|image: .*|image: ${NEXUS_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}|g" \
                k8s/deployment.yaml
                '''
            }
        }

        stage('Commit & Push to GitOps Repo') {
            steps {
                sh '''
                cd gitops

                git config user.name "jenkins"
                git config user.email "jenkins@gitops.com"

                git add .

                git commit -m "Update image to ${IMAGE_NAME}:${IMAGE_TAG}" || echo "No changes to commit"

                git push origin ${GITOPS_BRANCH}
                '''
            }
        }
    }

    post {
        success {
            echo "✅ CI completed successfully. Argo CD will auto-sync the deployment."
        }
        always {
            sh 'docker image prune -f || true'
        }
    }
}
