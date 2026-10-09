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

echo "$COLOR_BLUE"

GIT_CFN_VIRTUAL_PRIVATE_CLOUD_BRANCH_NAME="${GIT_CFN_VIRTUAL_PRIVATE_CLOUD_BRANCH_NAME:=master}"
REPOSITORY_PATH=$HOME_PATH/customlib/cloud-formation/virtual-private-cloud
if [ ! "$(ls -A $REPOSITORY_PATH)" ]; then
    echo "${COLOR_MAGENTA}${STEP}/$STEP_COUNT:${COLOR_GREEN} Installing ${COLOR_BLUE}${REPOSITORY_PATH}${COLOR_GREEN} dependency.${COLOR_DEFAULT}"
    git clone $GIT_CFN_VIRTUAL_PRIVATE_CLOUD_REPOSITORY $REPOSITORY_PATH
    cd $REPOSITORY_PATH
    git checkout $GIT_CFN_VIRTUAL_PRIVATE_CLOUD_BRANCH_NAME
    sh dist.sh
    cd $EXEC_PATH
else
    echo "${COLOR_MAGENTA}${STEP}/$STEP_COUNT:${COLOR_GREEN} Folder ${COLOR_BLUE}${REPOSITORY_PATH}${COLOR_GREEN} found! Skipping installation.${COLOR_DEFAULT}"
fi
let STEP++

cd $HOME_PATH
if [ ! -d "$HOME_PATH/node_modules" ]; then
    echo "${COLOR_MAGENTA}${STEP}/$STEP_COUNT:${COLOR_GREEN} Installing ${COLOR_BLUE}$HOME_PATH/package.json${COLOR_GREEN} dependencies.${COLOR_DEFAULT}"
    npm install
else
    echo "${COLOR_MAGENTA}${STEP}/$STEP_COUNT:${COLOR_GREEN} Folder ${COLOR_BLUE}$HOME_PATH/node_modules${COLOR_GREEN} found! Skipping npm installation.${COLOR_DEFAULT}"
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
