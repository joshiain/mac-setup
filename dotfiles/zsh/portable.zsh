# Portable fragment; keep existing frameworks/host settings outside the repo.
[[ -o interactive ]] || return 0
if ! command -v brew >/dev/null 2>&1; then
  if [[ -x /opt/homebrew/bin/brew && $(uname -m) == arm64 ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
fi
typeset -U path PATH
[[ ! -d "$HOME/.local/bin" ]] || path=("$HOME/.local/bin" $path)
# New small aliases; review/remove during refinement.
alias g='git'
alias gs='git status --short'
alias gd='git diff'
# The optional shell.zsh profile manages Oh My Zsh and plugin ordering.
