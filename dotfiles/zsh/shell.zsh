# Opt-in interactive profile, installed by --oh-my-zsh.
[[ -o interactive ]] || return 0
[[ -z ${_MAC_SETUP_SHELL_LOADED:-} ]] || return 0

# portable.zsh initializes Homebrew's PATH before this file is loaded.
typeset -g _mac_setup_brew_prefix=${HOMEBREW_PREFIX:-}
if [[ -z $_mac_setup_brew_prefix ]] && (( $+commands[brew] )); then
  _mac_setup_brew_prefix=$(brew --prefix)
fi
if [[ -d "$_mac_setup_brew_prefix/share/zsh/site-functions" ]]; then
  fpath=("$_mac_setup_brew_prefix/share/zsh/site-functions" $fpath)
fi

# Source this profile instead of a separate Oh My Zsh initialization block.
export ZSH=${ZSH:-$HOME/.oh-my-zsh}
if [[ ! -r "$ZSH/oh-my-zsh.sh" ]]; then
  print -u2 'mac-setup: Oh My Zsh is missing; run bootstrap.sh --apply --oh-my-zsh.'
  return 0
fi
typeset -g _MAC_SETUP_SHELL_LOADED=1
ZSH_THEME=${ZSH_THEME-robbyrussell}
if (( ! ${+plugins} )); then plugins=(git); fi
# Updates are explicit (omz update); shell startup never prompts or updates.
zstyle ':omz:update' mode disabled
source "$ZSH/oh-my-zsh.sh"

HISTFILE=${HISTFILE:-$HOME/.zsh_history}
HISTSIZE=50000
SAVEHIST=50000
setopt extended_history share_history hist_ignore_all_dups hist_save_no_dups
setopt hist_ignore_space
bindkey -e
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'
zstyle ':completion:*:descriptions' format '[%d]'

if (( $+commands[fzf] )); then
  # fzf initializes Ctrl-R history, Ctrl-T files, and Alt-C directories.
  source <(fzf --zsh)
  if (( $+commands[bat] )); then
    export FZF_CTRL_T_OPTS="${FZF_CTRL_T_OPTS:-} --preview 'bat --color=always --style=numbers --line-range=:200 -- {}'"
  fi
  if [[ -r "$_mac_setup_brew_prefix/opt/fzf-tab/share/fzf-tab/fzf-tab.zsh" ]]; then
    zstyle ':completion:*' menu no
    source "$_mac_setup_brew_prefix/opt/fzf-tab/share/fzf-tab/fzf-tab.zsh"
  fi
fi
if (( $+commands[zoxide] )); then eval "$(zoxide init zsh)"; fi

# fzf-tab must precede plugins that wrap ZLE widgets.
if [[ -r "$_mac_setup_brew_prefix/share/zsh-autosuggestions/zsh-autosuggestions.zsh" ]]; then
  source "$_mac_setup_brew_prefix/share/zsh-autosuggestions/zsh-autosuggestions.zsh"
  bindkey '^F' autosuggest-accept
fi
# Invoked at the end of .zshrc, after local customizations.
mac_setup_highlighting() {
  if [[ -r "$_mac_setup_brew_prefix/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]]; then
    source "$_mac_setup_brew_prefix/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
  fi
  unfunction mac_setup_highlighting
}
