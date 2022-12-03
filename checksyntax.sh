#!/bin/env bash
###############################################
# Check kustomize and helmfiles are correct   #
# 2022-12-03 - github.com/odoucet/k8s-helpers #
###############################################

if [ -f "kustomization.yaml" ]; then
  echo -n "Check kustomize syntax ... "
  kubectl kustomize . --enable-alpha-plugins | kubectl apply -f - --dry-run=client >/dev/null && echo -e "\e[32mOK\e[0m" || echo "FAILURE"
fi

for helmfile in $(/bin/ls -- helmfile.yaml */helmfile.yaml 2>/dev/null); do
  echo -n "Check helmfile '$helmfile' ... "
  helmfile --log-level warn -f "$helmfile" lint && echo -e "\e[32mOK\e[0m" || echo "FAILURE"
done

if [ "$(kubeaudit version)" ]; then
  echo "Checking security with kubeaudit ..."
  kubectl kustomize . --enable-alpha-plugins |kubeaudit all -p logrus -f - && echo -e "\e[32mOK\e[0m"
  
  for helmfile in $(/bin/ls -- helmfile.yaml */helmfile.yaml 2>/dev/null); do
    helmfile --log-level warn -f "$helmfile" template |kubeaudit all -p logrus -f - && echo -e "\e[32mOK\e[0m"
  done
else
  echo "Please install kubeaudit (https://github.com/Shopify/kubeaudit) to perform security checks"
fi
