# dotfiles

Inspired by this post: https://news.ycombinator.com/item?id=11070797

# Usage

## First Time Setup

### Initial Steps
git init --bare $HOME/.dotfiles
alias dotfiles='/usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
dotfiles config status.showUntrackedFiles no

### Usage

dotfiles add FILE
dotfiles commit -m "COMMIT MESSAGE"

dotfiles status

dotfiles remote add dotfiles <REMOTEREPO>
HOWTO SET THE CORRECT BRANCH SO PUSH WILL WORK WITHOUT DEFINING A BRANCH???
dotfiles push --set-upstream
dotfiles push dotfiles <LOCALBRANCH>:<REMOTEBRANCH> --force
  
## Usage

# setting up the alias prior to using
alias dotfiles='/usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
# ignore the folder where we clone it, avoiding recursion problem
echo ".dotfiles" >> .gitignore
git clone --bare -depth=1 -branch <REMOTEBRANCH> <REMOTEREPO> $HOME/.dotfiles
dotfiles checkout
# Back up pre-existing files if they exist
if [ $? != 0 ]; then
  mkdir -p .dotfiles-backup
  dotfiles checkout 2>&1 | egrep "\s+\." | awk {'print $1'} | xargs -I{} mv {} .dotfiles-backup/{}
  dotfiles checkout
fi;
dotfiles config --local status.showUntrackedFiles no

## Links

https://www.atlassian.com/git/tutorials/dotfiles
