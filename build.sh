#!/bin/bash

# Initialize variables
build_catalogs=1
do_install=0
project_path=""

# Functions

show_help ()
{
	echo Usage:
	echo     . ./build.sh [-f] [-i your/trac/env/path]
	echo
	echo     -f :    fast: do not generate localized message catalogs
	echo     -i :    install the built plugins into your trac environment
	echo
	
	return 0
}

make_catalogs ()
{
    python setup.py extract_messages
    python setup.py extract_messages_js
    python setup.py update_catalog -l it
    python setup.py update_catalog_js -l it
    python setup.py compile_catalog -f -l it
    python setup.py compile_catalog_js -f -l it
    python setup.py update_catalog -l es
    python setup.py update_catalog_js -l es
    python setup.py compile_catalog -f -l es
    python setup.py compile_catalog_js -f -l es
    python setup.py update_catalog -l de
    python setup.py update_catalog_js -l de
    python setup.py compile_catalog -f -l de
    python setup.py compile_catalog_js -f -l de
    python setup.py update_catalog -l fr
    python setup.py update_catalog_js -l fr
    python setup.py compile_catalog -f -l fr
    python setup.py compile_catalog_js -f -l fr
    python setup.py update_catalog -l ko
    python setup.py update_catalog_js -l ko
    python setup.py compile_catalog -f -l ko
    python setup.py compile_catalog_js -f -l ko
    python setup.py update_catalog -l ru
    python setup.py update_catalog_js -l ru
    python setup.py compile_catalog -f -l ru
    python setup.py compile_catalog_js -f -l ru

    return 0
}

# Parse args
OPTIND=1
while getopts "h?fi:" opt; do
    case "$opt" in
        h|\?)
            show_help
            exit 0
            ;;
        f)  build_catalogs=0
            ;;
        i)  
            do_install=1
            project_path=$OPTARG
            ;;
    esac
done
shift $((OPTIND-1)) # Shift off the options and optional --.

#echo "build_catalogs=$build_catalogs, project_path='$project_path', Leftovers: $@"

mkdir bin
mkdir docs

cd tracgenericclass
python setup.py bdist_egg
cp -f dist/*.egg ../bin

cd ../tracgenericworkflow
python setup.py bdist_egg
cp -f dist/*.egg ../bin

cd ../sqlexecutor
python setup.py bdist_egg
cp -f dist/*.egg ../bin

cd ../testman4trac

if [ $build_catalogs -eq 1 ]
then
    make_catalogs
fi

python setup.py bdist_egg
cp -f dist/*.egg ../bin

cd ..

cp -f *.txt docs

cp -f rpc_example.py bin

if [ $do_install -eq 1 ]
then
    echo Installing the plugins to $project_path/plugins
    cp -f bin/*.egg $project_path/plugins
fi
