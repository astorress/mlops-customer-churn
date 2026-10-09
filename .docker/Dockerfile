######## BASE IMAGE ########
FROM python:3.13-slim-bookworm AS python-base
FROM node:24-bookworm-slim AS img-base

# Arguments
ARG USER=data-science
ARG USER_HOME=/home/$USER
ARG VOLUME=/app
ARG SHELL=/bin/bash

COPY --from=python-base /usr/local/ /usr/local/
RUN ldconfig
RUN pip3 install --upgrade pip

RUN apt-get update
RUN npm install -g npm

# Inital OS configuration
RUN apt-get install -y locales \
    && sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen \
    && locale-gen
RUN apt-get install -y sudo lsb-release git git-lfs curl zip unzip jq

# Install VSCode extensions dependencies
RUN pip3 install cfn-lint cfn-lint-serverless
RUN npm install -g @anthropic-ai/claude-code \
    && node "$(npm root -g)/@anthropic-ai/claude-code/install.cjs" \
    && claude --version

# Install CLI utilities
RUN case "$(dpkg --print-architecture)" in \
        "amd64") AWSCLI_ARCH="x86_64" ;; \
        "arm64"|"aarch64") AWSCLI_ARCH="aarch64" ;; \
        *) echo "Unsupported architecture" && exit 1 ;; \
    esac; \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-${AWSCLI_ARCH}.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && apt-get install -y less

# Install Serverless framework
RUN npm install -g serverless

# Set up non root user
RUN echo "$USER ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN useradd -ms $SHELL $USER
RUN mkdir -p $VOLUME \
    && chown -R $USER:$USER $VOLUME

# Set up SSH keys
RUN mkdir -p $USER_HOME/.ssh
RUN ln -s /run/secrets/gitlab_ssh_private_key $USER_HOME/.ssh/gitlab
RUN chown -R $USER:$USER $USER_HOME/.ssh

# Preserve bash history
RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
    && echo $SNIPPET >> "/root/.bashrc" \
    && mkdir /commandhistory \
    && touch /commandhistory/.bash_history \
    && chown -R $USER /commandhistory \
    && echo $SNIPPET >> "$USER_HOME/.bashrc"

# Let non-root user self-update global npm packages (serverless, claude-code) at runtime
RUN chown -R $USER:$USER /usr/local/lib/node_modules /usr/local/bin


######## ML BASE IMAGE ########
# Shared tooling of every MLOps project: tests, linters, notebooks, AWS SDK
# and the Docker CLI (builds/pushes the project's model image through the
# host's Docker daemon, mounted as /var/run/docker.sock). ML libraries are
# NOT installed here: each project pins its own in container/requirements.txt,
# shared with its SageMaker model image.
FROM img-base AS img-ml-base

# Install Docker CLI + buildx (Docker's official Debian repository)
RUN install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
        > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y docker-ce-cli docker-buildx-plugin

# Install OS utilities (libsqlite3: pytest-cov / coverage)
RUN apt-get install -y libsqlite3-0

# Install VSCode extensions dependencies
RUN pip3 install pylint yapf isort

# Install Dev utilities
RUN pip3 install boto3 jupyterlab

# Install Test utilities
RUN pip3 install pytest pytest-cov pytest-env pytest-mock moto


######## ROOT IMAGE ########
FROM img-base AS img-root
USER $USER

######## INFRASTRUCTURE IMAGE ########
FROM img-base AS img-infrastructure
USER $USER

######## CUSTOMER CHURN IMAGE ########
# Build context: customer-churn/ (see its .docker/docker-compose.yml).
FROM img-ml-base AS img-customerchurn

# Same pinned ML runtime as the model image (customer-churn/container)
COPY container/requirements.txt /tmp/customer-churn-requirements.txt
RUN pip3 install -r /tmp/customer-churn-requirements.txt

USER $USER
