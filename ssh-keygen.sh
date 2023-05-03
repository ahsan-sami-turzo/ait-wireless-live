#!/bin/bash

mkdir -p /root/.ssh

cd ~/.ssh

echo -n "Enter your email: "

read email

ssh-keygen -f 'nf-github-actions' -t rsa -b 4096 -C "$email" -P ""

cat nf-github-actions.pub >> ~/.ssh/authorized_keys

cat nf-github-actions