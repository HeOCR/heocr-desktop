#!/usr/bin/env bash
# Entrypoint for the disposable buildserver container in fdroid-buildserver.yml.
set -euo pipefail

commit=${1:?expected the GitHub checkout SHA}
[[ $commit =~ ^[0-9a-f]{40}$ ]]
source /etc/profile.d/bsenv.sh
export GIT_TERMINAL_PROMPT=0

# Use the fdroidserver revision that provisioned the pinned image.
fdroid_revision=8f52ae3ce287bc28964db544b970b88dce9c38bf
fdroid_source=https://gitlab.com/fdroid/fdroidserver.git
echo "F-Droid source: $fdroid_source @ $fdroid_revision"
git init -q "$fdroidserver"
git -C "$fdroidserver" -c transfer.fsckObjects=true fetch --depth=1 "$fdroid_source" "$fdroid_revision"
git -C "$fdroidserver" checkout -q --detach FETCH_HEAD
export PATH="$fdroidserver:$PATH"
fdroid --version

# Match the SDK basics in fdroiddata's build job. The recipe and Gradle request the rest.
sdkmanager "platform-tools" "build-tools;31.0.0"

app_id=io.github.heocr.heocr_mobile
work="$home_vagrant/build-probe"
mkdir -p "$work/metadata"
cd "$work"
printf 'sdk_path: %s\n' "$ANDROID_HOME" > config.yml
chmod 0600 config.yml

python3 - "$app_id" "$commit" <<'PY'
import sys
import tomllib
from pathlib import Path

from ruamel.yaml import YAML

app_id, commit = sys.argv[1:]
app = tomllib.loads(Path("/source/pyproject.toml").read_text())["tool"]["briefcase"]
version = app["version"]
major, minor, patch = map(int, version.split("."))
version_code = int(f"{major}{minor:02d}{patch:02d}00")

recipe = Path("metadata", f"{app_id}.yml")
yaml = YAML(typ="safe")
metadata = yaml.load(Path("/source/docs/stores/fdroid", recipe.name))
build, = metadata["Builds"]
del build["disable"]
build.update(commit=commit, versionName=version, versionCode=version_code)
metadata.update(CurrentVersion=version, CurrentVersionCode=version_code)
yaml.default_flow_style = False
yaml.dump(metadata, recipe)
print(f"Testing {app_id}:{version_code} ({version}) at {commit}")
print(f"App source: {metadata['Repo']}")
PY
cp "metadata/$app_id.yml" /evidence/probe-metadata.yml
chown -R vagrant:vagrant "$work"

# As in fdroiddata CI, let fdroid run the recipe's sudo phase and drop sudo
# before scanning and building. The workspace is inside this one-shot container.
sudo --user vagrant --set-home env \
  PATH="$PATH" ANDROID_HOME="$ANDROID_HOME" PYTHONUNBUFFERED=1 \
  fdroid build --verbose --test --on-server --refresh-scanner --no-tarball "$app_id"
