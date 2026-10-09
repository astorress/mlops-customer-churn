#!/bin/bash

COLOR_BLUE=$(tput setaf 4)
COLOR_DEFAULT=$(tput sgr0)

export GIT_SSH_COMMAND='ssh -i ~/.ssh/gitlab -o StrictHostKeyChecking=no -o LogLevel=ERROR'
git config --global --add safe.directory /app
