#!/bin/bash
npm install -g aws-cdk
# Note: zsh users need to use ""
pip install -e ".[deploy]"

# Bootstrap the AWS accont
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity | jq .Account -r)
export AWS_REGION=$(aws configure get region)
cdk bootstrap aws://$AWS_ACCOUNT_ID/$AWS_REGION --all
