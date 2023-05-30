import requests
import argparse
import ruamel.yaml

ARTIFACTHUB_API_URL = "https://artifacthub.io/api/v1/packages/helm/{}"

def get_latest_version(chart):
    url = ARTIFACTHUB_API_URL.format(chart)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["version"]
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
        if chart:
            current_version = release.get("version")
            latest_version = get_latest_version(chart)
            if latest_version and current_version != latest_version:
                release["version"] = latest_version
        updated_releases.append(release)

    updated_helmfile = {
        "repositories": repositories,
        "helmDefaults": helm_defaults,
        "releases": updated_releases,
    }

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
