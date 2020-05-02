#!/bin/sh

VER=$1

. ./clean.sh

svn checkout --username=seccanj svn+ssh://seccanj@svn.code.sf.net/p/testman4trac/code/ testman4trac.$VER.SVN
git clone ssh://seccanj@git.code.sf.net/p/testman4trac/git testman4trac.$VER.GIT
cd testman4trac.$VER.GIT
cp -R ../testman4trac.$VER/* .
git status
git add .
#git commit -m "Release $VER"
#git push

#cd ..

