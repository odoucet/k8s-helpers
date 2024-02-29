# Compare several kubernets clusters as gitops subfolders.
# Folder organisation:
#   kubernetescluster1/system/helmfile.yaml
#   kubernetescluster2/system/helmfile.yaml
#   kubernetescluster3/system/helmfile.yaml


import os
import yaml
import glob
from tabulate import tabulate
import requests
import ruamel.yaml
import subprocess
import sys
import datetime



def get_helm_version(chart):
    # helm search repo cilium/cilium -o yaml
    info = ruamel.yaml.YAML().load(subprocess.run(["helm", "search", "repo", chart, "-o", "yaml"], stdout=subprocess.PIPE).stdout)
    if info and info[0]:
        return info[0].get('version')
    else:
        return None

def parse_helmfile(helmfile_path):
    with open(helmfile_path, 'r') as file:
        helmfile = yaml.safe_load(file)
        releases = {}
        for release in helmfile.get('releases', []):
            chart = release.get("chart")
            # if chart is defined and does not start with "oci:"
            if chart:
                name = release.get('chart')
                version = release.get('version')
                if name and version:
                    releases[name] = version
        return releases

def compare_helmfiles(helmfile_paths):
    all_releases = {}
    for path in helmfile_paths:
        if os.path.isfile(path) and path.endswith('.yaml'):
            releases = parse_helmfile(path)
            # replace 'oci://ghcr.io/actions/' in keys:
            releases = {k.replace('oci://ghcr.io/actions/', ''): v for k, v in releases.items()}
            all_releases[path.split('/')[0]] = releases
    return all_releases

def color_cell(value, latest_version, htmlOutput=False):
    if value != latest_version:
        if htmlOutput:
            return f"<span style='color:red'>{value}</span>"
        else:
            return f"\033[91m{value}\033[0m"  # Use red color for different versions
    else:
        return value

# Provide the paths to the helmfile.yaml files you want to compare
all_releases = compare_helmfiles(glob.glob("*/system/helmfile.yaml"))
all_releases = dict(sorted(all_releases.items(), key=lambda x: x[0]))


if len(sys.argv) > 1 and sys.argv[1] == "--html":
    htmlOutput = True
else:
    htmlOutput = False

# Prepare the data for the table
header = ['Name', 'Latest Version'] + list(all_releases.keys())
rows = []

# add a first row with last modification date of system/helmfile.yaml
row = ["Last modified"]
for helmfile, releases in all_releases.items():
    modifDate = datetime.datetime.fromtimestamp(os.path.getmtime(f"{helmfile}/system/helmfile.yaml"))
    # append "X days ago"
    row.append(f"{(datetime.datetime.now() - modifDate).days} days")
rows.append(row)

for release in sorted(set(release for releases in all_releases.values() for release in releases)):
    row =[release]
    latest_version = get_helm_version(release)
    if not latest_version:
        latest_version = None
    row.append(latest_version)
    for helmfile, releases in all_releases.items():
        row.append(color_cell(releases.get(release, '-'), latest_version, htmlOutput))
    rows.append(row)

# Generate and print the table
# if script is called with "--html", generate html table
if htmlOutput:
    table = tabulate(rows, headers=header, tablefmt='unsafehtml')
    # print minimal header
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    print("<html><head>")
    print('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/purecss@3.0.0/build/pure-min.css" integrity="sha384-X38yfunGUhNzHpBaEBsWLO+A0HDYOQi8ufWDkZ0k9e0eXz/tH3II7uKZ9msv++Ls" crossorigin="anonymous">')
    print('<meta name="viewport" content="width=device-width, initial-scale=1">')
    print(f"<title>Kubernetes system helm versions used (last update {date})</title></head><body>")
    print(f"<h1>Kubernetes system helm versions used (last update {date})</h1>")
    print(table.replace('<table>', '<table class="pure-table pure-table-bordered pure-table-horizontal pure-table-striped">'))
    print("</body></html>")
else:
    print(tabulate(rows, headers=header, tablefmt='github'))

