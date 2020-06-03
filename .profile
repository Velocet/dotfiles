# ~/.profile: executed by the command interpreter for login shells.
#  Not read by bash, if ~/.bash_profile or ~/.bash_login exists.

# XDG Base Directory Specification
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_CACHE_HOME="$HOME/.local/.cache"

export WGETRC="$XDG_CONFIG_HOME/.wgetrc"
export VIMINIT='source "$XDG_CONFIG_HOME/vim/vimrc"'
export PYTHONSTARTUP="$XDG_CONFIG_HOME/.pythonrc.py"

# default umask is set in /etc/profile
#umask 022

# if running bash
if [ -n "$BASH_VERSION" ]; then
    # include .bashrc if it exists
    if [ -f "$HOME/.bashrc" ]; then
	. "$HOME/.bashrc"
    fi
fi

# if running zsh
#if [ -n "$ZSH" ]; then
    # do something
#fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/bin" ] ; then
    PATH="$HOME/bin:$PATH"
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi

# Uses (in that order):
# .oh-my-zsh
#  powerline10k
#  powerline10k-nerdfonts (Sauce Code Pro)
#  LS_COLORS https://github.com/trapd00r/LS_COLORS
# neofetch
# micro

# Aliases - Put all additions into ~/.profile_aliases
if [ -f $XDG_CONFIG_HOME/.profile_aliases ]; then
    . $XDG_CONFIG_HOME/.profile_aliases
fi

# dircolors - enable color support
if [ -x /usr/bin/dircolors ]; then
    test -r $XDG_CONFIG_HOME/.dircolors && eval "$(dircolors -b $XDG_CONFIG_HOME/.dircolors)" || eval "$(dircolors -b)"
fi

# Enviroment
export CLICOLOR=1
## colored GCC warnings and errors
export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'
## Editor
if [[ -n $EDITOR ]]; then
  export EDITOR='nano'
fi
## True Color Terminal
if [[ -n $WSLENV ]]; then
  export COLORTERM='truecolor'
fi

# PS2SDK
export PS2DEV=/usr/local/ps2dev
export PS2SDK=$PS2DEV/ps2sdk
export GSKIT=$PS2DEV/gsKit
export PATH=$PATH:$PS2DEV/bin:$PS2DEV/ee/bin:$PS2DEV/iop/bin:$PS2DEV/dvp/bin:$PS2SDK/bin

# MOTD
neofetch

alias dotfiles='/usr/bin/git --git-dir=$HOME/.dfiles/ --work-tree=$HOME'
