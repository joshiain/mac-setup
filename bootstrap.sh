#!/bin/bash
# macOS /bin/bash 3.2 compatible. Preview is default; --apply is explicit.
set -euo pipefail
umask 077

usage() {
  cat <<'HELP'
Usage: ./bootstrap.sh [--dry-run | --apply | --check] [selections]
Selections: --apps --cli --optional --dotfiles --editors --oh-my-zsh --all
No selections: --cli --dotfiles. No mode: --dry-run.
--oh-my-zsh includes optional tools and dotfiles, plus Oh My Zsh.
--all includes Oh My Zsh and editor templates; review before applying.
--check runs read-only brew bundle checks and reports config plans.
Existing shell/Git/Ghostty/editor entrypoints are preserved. Managed-fragment
conflicts are backed up under ~/.local/state/mac-setup/backups before linking.
HELP
}
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
mode=dry-run
mode_selected=0
apps=0 cli=0 optional=0 dotfiles=0 editors=0 oh_my_zsh=0 selected=0
for argument in "$@"; do
  case "$argument" in
    --help|-h) usage; exit 0 ;;
    --dry-run|--apply|--check)
      [ "$mode_selected" -eq 0 ] || die 'Select only one mode.'
      mode=${argument#--}; mode_selected=1 ;;
    --apps) apps=1; selected=1 ;;
    --cli) cli=1; selected=1 ;;
    --optional) optional=1; selected=1 ;;
    --dotfiles) dotfiles=1; selected=1 ;;
    --editors) editors=1; selected=1 ;;
    --oh-my-zsh) oh_my_zsh=1; optional=1; dotfiles=1; selected=1 ;;
    --all) apps=1; cli=1; optional=1; dotfiles=1; editors=1; oh_my_zsh=1; selected=1 ;;
    *) die "Unknown option: $argument" ;;
  esac
done
if [ "$selected" -eq 0 ]; then cli=1; dotfiles=1; fi
[ "$(uname -s)" = Darwin ] || die 'This setup targets macOS.'
[ -n "${HOME:-}" ] && [ -d "$HOME" ] || die 'HOME must be an existing directory.'
repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
home_dir=$(cd "$HOME" && pwd -P)
[ "$home_dir" != / ] || die 'Refusing HOME=/.'
backup_root="$home_dir/.local/state/mac-setup/backups"
backup_dir="$backup_root/$(date -u +%Y%m%dT%H%M%SZ)-$$"
manifests=()
[ "$apps" -eq 0 ] || manifests+=(Brewfile)
[ "$cli" -eq 0 ] || manifests+=(Brewfile.cli)
[ "$optional" -eq 0 ] || manifests+=(Brewfile.optional)
for manifest in ${manifests[@]+"${manifests[@]}"}; do
  [ -f "$repo_dir/$manifest" ] || die "Missing manifest: $manifest"
done

# Refuse directory symlinks/non-directories instead of traversing other locations.
# A symlink at the final target itself is handled by the link policy.
safe_parent() {
  local parent
  parent=$(dirname "$1")
  while [ "$parent" != "$home_dir" ]; do
    case "$parent" in "$home_dir"/*) ;; *) die 'Config target escaped HOME.' ;; esac
    [ ! -L "$parent" ] || die "Parent is a symlink; handle manually: $parent"
    if [ -e "$parent" ] && [ ! -d "$parent" ]; then die "Parent is not a directory: $parent"; fi
    parent=$(dirname "$parent")
  done
}
sources=() targets=() policies=()
add_link() {
  [ -f "$repo_dir/$1" ] || die "Missing config template: $1"
  sources+=("$repo_dir/$1"); targets+=("$home_dir/$2"); policies+=("$3")
  safe_parent "$home_dir/$2"
}
if [ "$dotfiles" -eq 1 ]; then
  add_link dotfiles/zsh/portable.zsh .config/mac-setup/portable.zsh managed
  add_link dotfiles/git/portable.gitconfig .config/mac-setup/gitconfig managed
  add_link dotfiles/ghostty/portable.conf .config/mac-setup/ghostty.conf managed
  add_link dotfiles/zsh/zshrc .zshrc preserve
  add_link dotfiles/git/gitconfig .gitconfig preserve
  if [ -e "$home_dir/.config/ghostty/config" ] || [ -L "$home_dir/.config/ghostty/config" ] ||
     [ -e "$home_dir/.config/ghostty/config.ghostty" ] || [ -L "$home_dir/.config/ghostty/config.ghostty" ] ||
     { [ -n "${XDG_CONFIG_HOME:-}" ] && [ -e "$XDG_CONFIG_HOME/ghostty/config.ghostty" ]; }; then
    printf 'Preserved existing Ghostty XDG configuration; integrate the fragment manually.\n'
  else
    add_link dotfiles/ghostty/config 'Library/Application Support/com.mitchellh.ghostty/config' preserve
  fi
fi
if [ "$editors" -eq 1 ]; then
  add_link dotfiles/editor/vscode-settings.json 'Library/Application Support/Code/User/settings.json' preserve
  add_link dotfiles/editor/cursor-settings.json 'Library/Application Support/Cursor/User/settings.json' preserve
  add_link dotfiles/editor/zed-settings.json .config/zed/settings.json preserve
fi
omz_dir="$home_dir/.oh-my-zsh"
if [ "$oh_my_zsh" -eq 1 ]; then
  add_link dotfiles/zsh/shell.zsh .config/mac-setup/shell.zsh managed
  safe_parent "$omz_dir/oh-my-zsh.sh"
  if [ -e "$omz_dir" ] && [ ! -f "$omz_dir/oh-my-zsh.sh" ]; then
    die "Existing Oh My Zsh directory is incomplete; inspect manually: $omz_dir"
  fi
  if [ "$mode" = apply ]; then
    command -v git >/dev/null 2>&1 || die 'Git is required to clone Oh My Zsh.'
  fi
fi
if [ "$mode" = apply ] && [ "${#sources[@]}" -gt 0 ]; then safe_parent "$backup_dir/item"; fi

printf 'Mode: %s\nRepository: %s\n' "$mode" "$repo_dir"
if [ "${#manifests[@]}" -gt 0 ] && [ "$mode" != dry-run ]; then
  command -v brew >/dev/null 2>&1 || die 'Install Homebrew from brew.sh and put it on PATH first.'
  command -v xcode-select >/dev/null 2>&1 || die 'Install Xcode Command Line Tools first.'
  xcode-select -p >/dev/null 2>&1 || die 'Install/select Xcode Command Line Tools first.'
  export HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_ANALYTICS=1
  brew --version >/dev/null
fi
check_failed=0
for manifest in ${manifests[@]+"${manifests[@]}"}; do
  if [ "$mode" = dry-run ]; then
    printf 'Would run: brew bundle install --file=%q --no-upgrade\n' "$repo_dir/$manifest"
  elif [ "$mode" = check ]; then
    if ! brew bundle check "--file=$repo_dir/$manifest" --no-upgrade; then check_failed=1; fi
  else
    brew bundle install "--file=$repo_dir/$manifest" --no-upgrade
  fi
done

if [ "$oh_my_zsh" -eq 1 ]; then
  if [ -f "$omz_dir/oh-my-zsh.sh" ]; then
    printf 'Preserved existing Oh My Zsh: %s\n' "$omz_dir"
  elif [ "$mode" = dry-run ]; then
    printf 'Would clone https://github.com/ohmyzsh/ohmyzsh.git into %s\n' "$omz_dir"
  elif [ "$mode" = check ]; then
    printf 'Missing Oh My Zsh: %s\n' "$omz_dir"
    check_failed=1
  else
    # Stage the clone so a network failure leaves no incomplete installation.
    omz_stage=$(mktemp -d "$home_dir/.mac-setup-omz.XXXXXX")
    if ! git clone --depth=1 https://github.com/ohmyzsh/ohmyzsh.git "$omz_stage/repo"; then
      rm -rf "$omz_stage"
      die 'Oh My Zsh clone failed; no config files were changed.'
    fi
    if [ ! -f "$omz_stage/repo/oh-my-zsh.sh" ]; then
      rm -rf "$omz_stage"
      die 'Oh My Zsh clone is missing its entrypoint.'
    fi
    mv "$omz_stage/repo" "$omz_dir"
    rmdir "$omz_stage"
    printf 'Installed Oh My Zsh: %s\n' "$omz_dir"
  fi
fi

index=0
while [ "$index" -lt "${#sources[@]}" ]; do
  source_file=${sources[$index]}; target=${targets[$index]}; policy=${policies[$index]}
  if [ -L "$target" ] && [ "$(readlink "$target")" = "$source_file" ]; then
    printf 'Already linked: %s\n' "$target"
  elif { [ -e "$target" ] || [ -L "$target" ]; } && [ "$policy" = preserve ]; then
    printf 'Preserved existing entrypoint: %s (see README.md)\n' "$target"
  elif [ "$mode" != apply ]; then
    if [ -e "$target" ] || [ -L "$target" ]; then printf 'Would back up managed conflict: %s\n' "$target"; fi
    if [ "$policy" = preserve ]; then
      printf 'Would create entrypoint from template: %s\n' "$target"
    else
      printf 'Would link: %s -> %s\n' "$target" "$source_file"
    fi
  else
    if [ -e "$target" ] || [ -L "$target" ]; then
      backup_target="$backup_dir/${target#"$home_dir"/}"
      mkdir -p "$(dirname "$backup_target")"
      mv "$target" "$backup_target"
      printf 'Backed up: %s -> %s\n' "$target" "$backup_target"
    fi
    mkdir -p "$(dirname "$target")"
    if [ "$policy" = preserve ]; then
      cp "$source_file" "$target"
      printf 'Created entrypoint from template: %s\n' "$target"
    else
      ln -s "$source_file" "$target"
      printf 'Linked: %s -> %s\n' "$target" "$source_file"
    fi
  fi
  index=$((index + 1))
done
if [ "$oh_my_zsh" -eq 1 ]; then
  printf 'Existing .zshrc files need manual integration; see README.md, Oh My Zsh and Ghostty.\n'
fi
printf 'Review README.md for remaining setup steps.\n'
if [ "$mode" = check ] && [ "$check_failed" -ne 0 ]; then exit 1; fi
