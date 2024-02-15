import requests
import argparse
import ruamel.yaml
from ruamel.yaml.comments import CommentedMap
import datetime
import re
import subprocess

def get_helm_version(chart):
    # helm search repo cilium/cilium -o yaml
    info = ruamel.yaml.YAML().load(subprocess.run(["helm", "search", "repo", chart, "-o", "yaml"], stdout=subprocess.PIPE).stdout)
    return info[0].get('version')

def update_helmfile(helmfile_path):
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True

    with open(helmfile_path, "r") as f:
        helmfile = yaml.load(f)

    repositories = helmfile.get("repositories", [])
    helm_defaults = helmfile.get("helmDefaults", {})
    updated_releases = []

    for release in helmfile.get("releases", []):
        chart = release.get("chart")
        # if chart is defined and does not start with "oci:"
        if chart and not chart.startswith("oci:"):
            current_version = release.get("version")
            latest_version = get_helm_version(chart)
            if not latest_version:
                latest_version = None

            if latest_version and current_version != latest_version:
                #datetime_object = datetime.datetime.fromtimestamp(latest_ts)
                release = CommentedMap(release)
                release.yaml_set_comment_before_after_key("version", before=f"Latest version: {latest_version}", indent=2) # - released on {datetime_object.strftime('%Y-%m-%d')}", indent=2)
                print("Updating {:50} from {:>8} to {:>8}".format(chart, current_version, latest_version))
        updated_releases.append(release)

    updated_helmfile = {
        "repositories": repositories,
        "helmDefaults": helm_defaults,
        "releases": updated_releases,
    }

    updated_helmfile = CommentedMap(updated_helmfile)
    datetime_object = datetime.datetime.now()
    updated_helmfile.yaml_add_eol_comment(f"Last version scan: {datetime_object.strftime('%Y-%m-%d')}", key="releases", column=0)

    with open(helmfile_path, "w") as f:
        yaml.dump(updated_helmfile, f)

def main():
    parser = argparse.ArgumentParser(description="Check Helm charts for updates and update helmfile.")
    parser.add_argument("helmfile", help="Path to the helmfile")
    args = parser.parse_args()

    helmfile_path = args.helmfile
    update_helmfile(helmfile_path)

    print("Helmfile updated successfully.")

def version_to_tuple(version: str) -> tuple:
    """
    Convertit une chaîne de numéro de version en un tuple d'entiers.
    Les parties non numériques sont ignorées.
    Par exemple: '1.12.4-alpha' devient (1, 12, 4).
    """
    # Extraction des segments numériques à l'aide d'une expression régulière
    version_numbers = re.findall(r'\d+', version)
    return tuple(map(int, version_numbers))

def compare_versions(version1: str, version2: str) -> int:
    """
    Compare deux numéros de versions. 
    Retourne:
    - 1 si version1 > version2
    - 0 si version1 == version2
    - -1 si version1 < version2
    """
    v1_tuple = version_to_tuple(version1)
    v2_tuple = version_to_tuple(version2)

    # Comparaison des tuples
    if v1_tuple > v2_tuple:
        return 1
    elif v1_tuple < v2_tuple:
        return -1
    else:
        return 0

if __name__ == "__main__":
    main()
