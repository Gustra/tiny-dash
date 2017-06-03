#!/usr/bin/env bash

# Installs the documentation in a git repository. Since the project is (was) located on Github, the default is to
# install the documentation there. This can be overridden by the environment vvariables:
#
# TINY_DASH_DOCS_GIT_URL: Git URL to close
# TINY_DASH_DOCS_SUBDIR: subdirectory in the clone, default is repo root
# TINY_DASH_DOCS_BRANCH: branch to install docs on, default "master"
#
# Any local "docs-installation" branch will be forcibly moved.
#
# Guess this program should have been written in Python for portability. Oh, well.

set -euo pipefail

# Configurations
git_url=${TINY_DASH_DOCS_GIT_URL:-https://github.com/Gustra/tiny-dash.wiki.git}
subdir=${TINY_DASH_DOCS_SUBDIR:-.}
dbranch=${TINY_DASH_DOCS_BRANCH:-master}
remote_branch=origin/${dbranch}
branch=docs-installation

# Globals
name=$(basename $git_url .git)
src=$(readlink -f $(dirname ${BASH_SOURCE[0]})/../docs)
dest="$name/$subdir"

if [[ ! -e $name ]]; then
    git clone "$git_url" "$name"
fi

cd $name

git fetch
git checkout -B $branch $remote_branch

mkdir -p "$dest/images"
mkdir -p "$dest/shots"

rm -f $dest/images/*
rm -f $dest/shots/*
rm -f $dest/*.md

cp $src/*.md "$dest"
cp $src/images/* "$dest/images/"
cp $src/shots/* "$dest/shots/"

git add .

if git diff --cached --quiet; then
    echo No new changes
else
    hash=$(cd $src; git rev-parse --short HEAD)
    git commit -m "Updated to tiny-dash $hash"
    if [[ ${1-} && ${1} = --push ]]; then
        if [[ ${DRY_RUN-} ]]; then
            echo git push origin HEAD:$dbranch
        else
            git push origin HEAD:$dbranch
        fi
    fi
fi

echo Done.