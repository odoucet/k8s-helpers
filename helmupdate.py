import requests
import argparse
import ruamel.yaml
from ruamel.yaml.comments import CommentedMap
import datetime

ARTIFACTHUB_API_URL = "https://artifacthub.io/api/v1/packages/helm/{}"

def get_package_info(chart):
    url = ARTIFACTHUB_API_URL.format(chart)
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

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
            packageInfo = get_package_info(chart)
            if packageInfo:
                latest_version = packageInfo["version"]
            else:
                latest_version = None

            if latest_version and current_version != latest_version:
                datetime_object = datetime.datetime.fromtimestamp(packageInfo['ts'])
                release = CommentedMap(release)
                release.yaml_set_comment_before_after_key("version", before=f"Latest version: {latest_version} - released on {datetime_object.strftime('%Y-%m-%d')}", indent=2)
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

if __name__ == "__main__":
    main()
