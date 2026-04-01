FROM jenkins/jenkins:lts-jdk17

USER root

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    docker.io \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN usermod -aG docker jenkins

USER jenkins

# Install minimal essential Jenkins plugins (no version conflicts)
RUN jenkins-plugin-cli --plugins \
    workflow-aggregator \
    github-branch-source \
    blueocean-core-js