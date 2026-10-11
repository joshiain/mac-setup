# Refined app setup, 2026-10-10. Original inventory retained; review README.md.
# Install current releases; historical inventory is kept separately. See README.md.
# App Store helper; the only CLI formula needed by this app-focused file.
brew "mas"

# Browsers
cask "google-chrome"
cask "safari-technology-preview" # Separate developer browser; current cask needs macOS 26+.

# AI, communication, and music
cask "chatgpt" # Matches ChatGPT.app and com.openai.codex; replaces obsolete codex-app mapping.
cask "claude"
cask "discord"
cask "spotify"

# Design
cask "figma"
cask "shapr3d" # Approved cask edition; no duplicate Mac App Store entry.
if Hardware::CPU.arm?
  cask "paper-design" # Paper interface design tool, Apple Silicon only.
end

# Development and terminals
cask "cursor"
cask "orbstack" # Replaces Docker Desktop in this list; macOS 14+, ARM and Intel.
cask "ghostty"
cask "github" # GitHub Desktop, distinct from the gh CLI.
cask "zed"

# Video and utilities
cask "iina"
cask "stremio" # Current stable product; installed 2.0.8 -> current 5.x, review migration.
cask "tailscale-app" # Standalone GUI distribution; matches io.tailscale.ipn.macsys.

# App Store editions: IDs verified against Apple's metadata and installed bundle IDs.
# mas is the App Store CLI: sign in first; install restores acquired apps, get acquires free apps.
# Availability and paid purchases depend on the account/region. See README.md.
mas "AdGuard for Safari", id: 1440147259 # Now listed as AdGuard Mini / Ad Blocker for Safari.
mas "Pages", id: 361309726 # Pages Creator Studio.app, com.apple.Pages; requires macOS 26+.
if Hardware::CPU.arm?
  mas "Xcode", id: 497799835 # Current 27.0 requires Apple M1+ and macOS 26.6+.
end

# Manual apps: Pica and ReverseImageSearch. See README.md; no guessed packages.
