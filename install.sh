#!/bin/bash
# Download the public repository, then delegate to its local bootstrap.
set -euo pipefail
umask 077

die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
[ "$(uname -s)" = Darwin ] || die 'This setup targets macOS.'
[ -n "${HOME:-}" ] && [ -d "$HOME" ] || die 'HOME must be an existing directory.'
home_dir=$(cd "$HOME" && pwd -P)
[ "$home_dir" != / ] || die 'Refusing HOME=/.'
repo_dir="$home_dir/dev/mac-setup"

[ ! -L "$home_dir/dev" ] || die '~/dev is a symlink; clone and run bootstrap.sh manually.'
if [ -e "$repo_dir" ] || [ -L "$repo_dir" ]; then
  die "Setup folder already exists; run bootstrap.sh from $repo_dir. No files were changed."
fi
xcode-select -p >/dev/null 2>&1 || die 'Finish installing Xcode Command Line Tools first: xcode-select --install'
command -v git >/dev/null 2>&1 || die 'Git is required; install Xcode Command Line Tools first.'
command -v brew >/dev/null 2>&1 || die 'Install Homebrew from brew.sh and follow its PATH instructions first.'

# No flags previews everything. Explicit flags are forwarded to bootstrap.sh.
if [ "$#" -eq 0 ]; then set -- --dry-run --all; fi
mkdir -p "$home_dir/dev"
stage_dir=$(mktemp -d "$home_dir/dev/.mac-setup-download.XXXXXX")
trap 'rm -rf "$stage_dir"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Never prompt for GitHub credentials: this entrypoint requires a public repo.
if ! GIT_TERMINAL_PROMPT=0 git -c credential.helper= clone --depth=1 --branch main \
  https://github.com/joshiain/mac-setup.git "$stage_dir/repo"; then
  die 'Download failed. The repository must be public and reachable.'
fi
[ -f "$stage_dir/repo/bootstrap.sh" ] || die 'The published repository is missing bootstrap.sh; push the setup files first.'
mv "$stage_dir/repo" "$repo_dir"
printf 'Downloaded setup to %s\n' "$repo_dir"
cd "$repo_dir"
/bin/bash ./bootstrap.sh "$@"
