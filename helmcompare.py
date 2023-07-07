# Compare several helmfiles

import os
import yaml
import glob
from tabulate import tabulate
import requests

ARTIFACTHUB_API_URL = "https://artifacthub.io/api/v1/packages/helm/{}"

def get_latest_version(chart):
    url = ARTIFACTHUB_API_URL.format(chart)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["version"]
    return None

def parse_helmfile(helmfile_path):
    with open(helmfile_path, 'r') as file:
        helmfile = yaml.safe_load(file)
        releases = {}
        for release in helmfile.get('releases', []):
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
            all_releases[path.split('/')[0]] = releases
    return all_releases

def color_cell(value, latest_version):
    if value != latest_version:
        return f"\033[91m{value}\033[0m"  # Use red color for different versions
    else:
        return value
    
# Provide the paths to the helmfile.yaml files you want to compare
all_releases = compare_helmfiles(glob.glob("*/system/helmfile.yaml"))
all_releases = dict(sorted(all_releases.items(), key=lambda x: x[0]))

# Prepare the data for the table
header = ['Latest Version'] + list(all_releases.keys())
rows = []
for release in sorted(set(release for releases in all_releases.values() for release in releases)):
    row =[release]
    latest_version = get_latest_version(release)
    row.append(latest_version)
    for helmfile, releases in all_releases.items():
        row.append(color_cell(releases.get(release, '-'), latest_version))
    rows.append(row)

# Generate and print the table
table = tabulate(rows, headers=header, tablefmt='github')
print(table)