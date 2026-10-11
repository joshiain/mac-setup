# Mac setup

## Prerequisites

Install Xcode Command Line Tools with `xcode-select --install`. Wait for the
installation to finish, then install
[Homebrew](https://brew.sh/):

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow Homebrew's printed PATH instructions.

## Set up a new Mac

After the prerequisites, review the [Brewfiles](https://github.com/joshiain/mac-setup)
and sign into the Mac App Store. Run this to download the public repo to
`~/dev/mac-setup` and apply the full setup:

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/joshiain/mac-setup/main/install.sh)" -- --apply --all
```

For a preview, replace `--apply` with `--dry-run`: this downloads the files but
does not install packages or change configs. No `gh`, GitHub login, or SSH keys
are needed. The repo must be public and the setup files pushed first.

The installer leaves existing setup folders untouched. Keep the downloaded
folder in place: dotfile links point to it.

## Run from an existing checkout

In Terminal, run `cd ~/dev/mac-setup`, then apply the full bootstrap setup—apps,
CLI tools, Oh My Zsh, dotfiles, and editor configs—with one command:

```sh
./bootstrap.sh --apply --all
```

For previews or individual sections:

```sh
./bootstrap.sh                        # preview CLI + dotfiles
./bootstrap.sh --dry-run --all         # preview everything
./bootstrap.sh --apply --oh-my-zsh      # shell tools + dotfiles + Oh My Zsh
./bootstrap.sh --check --apps --cli    # check installed packages
```

Combine selections as needed:

| Selection | Includes |
| --- | --- |
| `--apps` | GUI and App Store apps; Cursor and Zed terminal commands |
| `--cli` | Core tools in `Brewfile.cli` |
| `--optional` | Shell packages in `Brewfile.optional`; no activation |
| `--dotfiles` | Zsh, Git, and Ghostty configs |
| `--editors` | VS Code, Cursor, and Zed settings |
| `--oh-my-zsh` | Oh My Zsh, optional packages, and dotfiles |
| `--all` | Everything above |

Preview is the default; use one mode: `--dry-run`, `--apply`, or `--check`.
Without selections, defaults to `--cli --dotfiles`. Packages use `--no-upgrade`;
unlisted packages are kept. Configs-only setup needs no Homebrew.

## Oh My Zsh and Ghostty

`--oh-my-zsh` installs into `~/.oh-my-zsh`, preserving existing installations
and `.zshrc` files. Fresh shells get a Git prompt, syntax highlighting, and:

- **Tab:** fuzzy completion; **Ctrl-F / Right Arrow:** accept suggestions.
- **Ctrl-R:** search history; **Ctrl-T:** find files with previews.
- **Left Option-C:** find directories; `z project` / `zi`: jump to frequent directories.

Open a new Ghostty window after setup. Update Oh My Zsh with `omz update`.

## Existing configs

Existing shell, Git, Ghostty, and editor entrypoints are preserved. Merge the
relevant templates manually; managed-fragment conflicts are backed up under
`~/.local/state/mac-setup/backups/`.

For Oh My Zsh, replace existing framework/plugin initialization in `.zshrc`
with this block. Keep your exports and customizations; avoid loading Oh My Zsh,
`compinit`, fzf, autosuggestions, or `zsh-autocomplete` twice.

```zsh
source "$HOME/.config/mac-setup/portable.zsh"
# Set ZSH_THEME or plugins=(git ...) here to override the defaults.
source "$HOME/.config/mac-setup/shell.zsh"
[[ ! -f "$HOME/.zshrc.local" ]] || source "$HOME/.zshrc.local"
# Keep highlighting last, after local widgets and key bindings.
if (( $+functions[mac_setup_highlighting] )); then mac_setup_highlighting; fi
```

For plain `--dotfiles`, only the first source line is needed. For other configs:

- **Git:** include `~/.config/mac-setup/gitconfig` before local overrides.
- **Ghostty:** merge `dotfiles/ghostty/portable.conf` into your active config.
- **Editors:** merge `dotfiles/editor/*-settings.json`; preserve existing Zed
  `auto_install_extensions` entries. Open Zed online to install extensions.

Fresh templates load `.zshrc.local`, `.gitconfig.local`, and Ghostty's
`config.local` for machine-specific overrides. Keep credentials outside this
folder. Open apps to finish sign-ins and permissions.
