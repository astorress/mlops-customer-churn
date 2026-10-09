#!/bin/bash

COLOR_GREEN=$(tput setaf 2)
COLOR_BLUE=$(tput setaf 4)
COLOR_MAGENTA=$(tput setaf 5)
COLOR_DEFAULT=$(tput sgr0)

EXEC_PATH=$(dirname $(readlink -f "$0"))
HOME_PATH=$EXEC_PATH/..
STEP=1
STEP_COUNT=4

echo "${COLOR_MAGENTA}${STEP}/$STEP_COUNT:${COLOR_GREEN} Configuring Git & Git LFS.${COLOR_DEFAULT}"
GIT_SCRIPT_PATH=$HOME_PATH/../.docker/git.sh
chmod +x $GIT_SCRIPT_PATH
. $GIT_SCRIPT_PATH
let STEP++

cd $HOME_PATH
if [ ! -d "$HOME_PATH/node_modules" ]; then
    echo "${COLOR_MAGENTA}${STEP}/$STEP_COUNT:${COLOR_GREEN} Installing ${COLOR_BLUE}$HOME_PATH/package.json${COLOR_GREEN} dependencies.${COLOR_DEFAULT}"
    npm install
else
    echo "${COLOR_MAGENTA}${STEP}/$STEP_COUNT:${COLOR_GREEN} Folder ${COLOR_BLUE}$HOME_PATH/node_modules${COLOR_GREEN} found! Skipping npm installation.${COLOR_DEFAULT}"
fi
let STEP++

echo "${COLOR_MAGENTA}${STEP}/$STEP_COUNT:${COLOR_GREEN} Granting access to the host Docker daemon.${COLOR_DEFAULT}"
if [ -S /var/run/docker.sock ]; then
    sudo chmod 666 /var/run/docker.sock
    docker version --format 'INFO: Docker server {{.Server.Version}}'
else
    echo "WARNING: /var/run/docker.sock not mounted; npm run image:push won't work."
fi
let STEP++

echo "${COLOR_MAGENTA}${STEP}/$STEP_COUNT:${COLOR_GREEN} Configuring AWS credentials.${COLOR_DEFAULT}"
AWS_SCRIPT_PATH=$HOME_PATH/../.docker/aws.sh
chmod +x $AWS_SCRIPT_PATH
$AWS_SCRIPT_PATH

ACCOUNT_ALIASES=$(aws iam list-account-aliases)
ACCOUNT_ALIAS=$(echo $ACCOUNT_ALIASES | jq -r '.AccountAliases[0]')
echo -e "${COLOR_GREEN}INFO: The AWS account alias you are using is: ${ACCOUNT_ALIAS}${COLOR_DEFAULT}"

DEVELOPER_INFO=$(env | grep DEVELOPER)
echo -e "${COLOR_GREEN}INFO: Developer environment variable: ${DEVELOPER_INFO}${COLOR_DEFAULT}"

echo "$COLOR_DEFAULT"
