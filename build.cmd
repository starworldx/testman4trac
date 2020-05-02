mkdir bin
mkdir docs

cd tracgenericclass
python setup.py bdist_egg
xcopy /y dist\*.egg ..\bin

cd ..\tracgenericworkflow
python setup.py bdist_egg
xcopy /y dist\*.egg ..\bin

cd ..\sqlexecutor
python setup.py bdist_egg
xcopy /y dist\*.egg ..\bin

cd ..\testman4trac

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

python setup.py bdist_egg
xcopy /y dist\*.egg ..\bin

cd ..

xcopy /y *.txt docs

xcopy /y rpc_example.py bin

if "%~1" NEQ "" xcopy /y bin\*.egg %1\plugins
