# Mac setup

Two installation paths share the same development tools:

- **personal** — the existing workstation setup: desktop apps, CLI tools,
  shell conveniences, Zsh/Git/Ghostty configs, and editor settings.
- **server** — a remote development Mac / home server: shared CLI tools,
  FFmpeg, OrbStack, Tailscale, ChatGPT, Paper, Cursor, full Xcode (with Icon
  Composer), and Zsh/Git configs. Desktop tools support interactive coding-agent
  work. Personal media apps, editor settings templates, and Ghostty config are
  excluded. Shell conveniences remain opt-in.

This repo prepares a Mac. Service deployments belong in `~/dev/homelab`;
mac-setup does not deploy containers, Komodo, or SSO, configure SSH/Tailscale,
change macOS preferences/security/login behavior, or set up credentials.

## Choose a path from an existing checkout

```sh
cd ~/dev/mac-setup
./bootstrap.sh --profile personal              # preview full personal setup
./bootstrap.sh --profile server                # preview remote dev/home server
./bootstrap.sh --apply --profile server        # install the reviewed server selection
./bootstrap.sh --check --profile server        # check installed packages; report config plans
./bootstrap.sh --help
```

Preview is always the default; applying requires `--apply`. Use one mode:
`--dry-run`, `--apply`, or `--check`. Preview does not run Homebrew, download
Oh My Zsh, or write configs. Check runs read-only Homebrew bundle checks and
reports planned config changes (it does not verify the contents of existing configs).

### Package inventory

| Layer | Packages |
| --- | --- |
| Shared base (`Brewfile.cli`) | Node, Bun (`oven-sh/bun/bun`), uv, gh, ripgrep, fd, jq, Claude Code, Codex CLI |
| Server additions (`Brewfile.server`) | FFmpeg, OrbStack, Tailscale, ChatGPT, Paper, Cursor; mas helper and full Xcode; Icon Composer supplied by Xcode |
| Personal apps (`Brewfile`) | Google Chrome, Safari Technology Preview, ChatGPT, Claude, Discord, Spotify, Figma, Shapr3D, Paper, Cursor, OrbStack, Ghostty, GitHub Desktop, Zed, IINA, Stremio, Tailscale |
| Personal App Store (`Brewfile`) | mas helper; AdGuard for Safari, Pages, Xcode |
| Optional shell (`Brewfile.optional`) | fzf-tab, zsh-autosuggestions, zsh-syntax-highlighting, fzf, bat, zoxide |

Paper and Xcode are conditional on Apple Silicon in both profiles; the server's
mas helper is installed with Xcode. Icon Composer follows the Xcode installation.
On Intel, these guarded entries are skipped; choose a compatible Apple toolchain
manually if needed. Package requirements and App Store availability still apply;
review the manifests before installing.
The shared base includes coding CLIs, not their desktop applications. Git comes
from the Command Line Tools prerequisite. OrbStack supplies Docker/Compose;
there is no Docker Desktop or Apple container runtime installation.

Keep new common CLI tools in `Brewfile.cli`; put personal apps in `Brewfile`
and server additions in `Brewfile.server`. Apps needed by both profiles are
present in both app manifests so each remains usable with `brew bundle`
independently. Bootstrap selects only one app manifest per run. FFmpeg stays in
the server manifest so the personal package inventory remains unchanged.
`Brewfile` retains its name and app inventory for existing workflows.

### Narrow a selection or add shell conveniences

Explicit selections **replace** a profile's defaults; combine them as needed:

```sh
./bootstrap.sh --profile server --cli                    # shared packages only
./bootstrap.sh --profile server --apps                   # all server additions, including FFmpeg/Xcode
./bootstrap.sh --profile server --dotfiles               # Zsh/Git configs only
./bootstrap.sh --profile server --all                    # server + optional shell/Oh My Zsh
./bootstrap.sh --profile server --cli --apps --optional  # packages only, no config changes
```

| Selection | Includes |
| --- | --- |
| `--apps` | Profile's additions: `Brewfile` for personal, `Brewfile.server` for server (including FFmpeg and mas) |
| `--cli` | Shared tools in `Brewfile.cli` |
| `--optional` | Packages in `Brewfile.optional`; no activation |
| `--dotfiles` | Zsh/Git configs; personal also includes Ghostty |
| `--editors` | VS Code, Cursor, and Zed settings; rejected for server |
| `--oh-my-zsh` | Oh My Zsh, optional packages, and profile-appropriate dotfiles |
| `--all` | All applicable sections for the selected profile; server excludes desktop configs and the personal app manifest |

Existing commands keep their behavior: no profile or selections previews
`--cli --dotfiles` with personal config templates, and `--apply --all` still
applies the full personal setup. An explicit `--profile personal` without
selections is shorthand for that full setup; an explicit `--profile server`
defaults to `--apps --cli --dotfiles`.

Packages use `--no-upgrade`; unlisted packages are kept. Profiles are additive
install plans, not uninstall or migration tools: running server on an existing
personal Mac leaves its apps/configs in place. Configs-only setup needs no Homebrew.

## Prerequisites and a new Mac

Install Xcode Command Line Tools with `xcode-select --install`. Wait for the
installation to finish, then install [Homebrew](https://brew.sh/):

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow Homebrew's printed PATH instructions. Command Line Tools are the initial
bootstrap prerequisite; the full server profile also installs Xcode later.
Before applying either profile's App Store entries, sign in to the App Store
and acquire the apps there, including Xcode for the server. The manifests use
`mas`; App Store authentication or administrator prompts may still be required.
See [mas requirements](https://github.com/mas-cli/mas#app-store-apple-account-requirements).
Shared CLI-only or configs-only selections do not need an App Store login.

The public installer downloads `main` to `~/dev/mac-setup` and forwards the
profile selection:

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/joshiain/mac-setup/main/install.sh)" -- --dry-run --profile server
```

Review the preview, then run `./bootstrap.sh --apply --profile server` from the
downloaded checkout. Use `personal` for the workstation path. The installer
without arguments still downloads and previews the full personal setup.
Its preview downloads files; only the local bootstrap preview is write-free.
No `gh`, GitHub login, or SSH keys are needed. The repo must be public.

The installer leaves existing setup folders untouched. Keep the downloaded
folder in place: dotfile links point to it.

## Remote development / server follow-up

Open OrbStack once and complete its onboarding before using Docker/Compose.
Install packages here; manage service definitions separately in `~/dev/homelab`.

Both profiles include the standalone Tailscale app. The server includes it for
planned remote access and exit-node use; sign-in, permissions, and exit-node
activation remain manual steps. Neither profile enables an exit node, remote
login, automatic login, or unattended startup. To install only Tailscale outside
the profile, the command is `brew install --cask tailscale-app`.

Cursor is installed on the server for interactive agent work; its settings are
left to the user. The personal VS Code/Cursor/Zed templates remain personal-only.
FFmpeg supplies host-side media processing. Credentials, service secrets, and
machine-specific settings stay outside this repo.

Full Xcode uses the same App Store ID (`497799835`) and Apple Silicon guard as
the personal manifest. Check [Apple's current Xcode system requirements](https://developer.apple.com/xcode/system-requirements)
before applying. After installation, open Xcode, review and accept its license
yourself, and finish first-launch component installation. Select Xcode's Command
Line Tools in its settings if the active developer directory still points at
standalone Command Line Tools. Install only the additional SDK/platform support
and simulator runtimes your projects need in Xcode's Components settings;
see [Apple's component setup instructions](https://developer.apple.com/documentation/xcode/downloading-and-installing-additional-xcode-components).
Bootstrap does not accept licenses, select a developer directory, download extra
runtimes, configure signing, or sign in on your behalf.

**Icon Composer comes with current Xcode**: open **Xcode > Open Developer Tool >
Icon Composer**, as described in [Apple's instructions](https://developer.apple.com/documentation/xcode/creating-your-app-icon-using-icon-composer).
The [Homebrew `icon-composer` cask](https://formulae.brew.sh/cask/icon-composer)
also exists and downloads Apple's standalone distribution. It is deliberately
omitted from this profile to avoid a second copy alongside Xcode. If you choose
to skip Xcode, use [Apple's standalone download](https://developer.apple.com/icon-composer/)
or that cask after checking the version's macOS requirements; the standalone
release may differ from the version bundled with Xcode.

There are no per-app `--xcode`, `--cursor`, `--ffmpeg`, or `--tailscale` flags:
these additions are part of the server setup option (`--profile server`).

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

## Validation

These checks use temporary homes and mocked Homebrew/Git; they do not install
packages, access the network, or change this Mac's configuration:

```sh
/bin/bash -n bootstrap.sh
/bin/bash -n install.sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Run on macOS with Python 3 and the system Bash/Zsh/Ruby available. Tests cover legacy
behavior, profile defaults and overrides, server isolation, read-only previews
and checks, failed installs, and preservation of existing configuration.
