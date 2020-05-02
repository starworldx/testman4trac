mkdir bin

cd tracgenericclass
python setup.py bdist_wininst
xcopy /y dist\*.exe ..\bin

cd ..\tracgenericworkflow
python setup.py bdist_wininst
xcopy /y dist\*.exe ..\bin

cd ..\sqlexecutor
python setup.py bdist_wininst
xcopy /y dist\*.exe ..\bin

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

python setup.py bdist_wininst
xcopy /y dist\*.exe ..\bin

cd ..

xcopy /y rpc_example.py bin
