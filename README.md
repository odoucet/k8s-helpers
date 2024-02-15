# k8s-helpers
Some scripts to help with k8s development

* checksyntax.sh : check syntax of all yaml files in a directory
* helmupdate.py: Python script to update helm charts in a directory
* helmcompare.py: compare */system/helmfile.yaml all together


Updates
------
*2024-02-15* now, helmupdate.py uses "helm repo search" to find the latest version of a chart (instead of artifacthub.io API, that was not always reliable)
