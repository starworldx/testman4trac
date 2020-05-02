rmdir /s /q bin
rmdir /s /q docs

cd tracgenericclass
rmdir /s /q build 
rmdir /s /q dist 
rmdir /s /q TracGenericClass.egg-info

cd ..\tracgenericworkflow
rmdir /s /q build 
rmdir /s /q dist 
rmdir /s /q TracGenericWorkflow.egg-info

cd ..\sqlexecutor
rmdir /s /q build 
rmdir /s /q dist 
rmdir /s /q SQLExecutor.egg-info

cd ..\testman4trac
rmdir /s /q build 
rmdir /s /q dist 
rmdir /s /q TestManager.egg-info
del /F /Q testmanager\locale\de\LC_MESSAGES\*.mo
del /F /Q testmanager\locale\es\LC_MESSAGES\*.mo
del /F /Q testmanager\locale\fr\LC_MESSAGES\*.mo
del /F /Q testmanager\locale\it\LC_MESSAGES\*.mo
del /F /Q testmanager\locale\ko\LC_MESSAGES\*.mo
del /F /Q testmanager\locale\ru\LC_MESSAGES\*.mo
del /F /Q testmanager\htdocs\js\de.js
del /F /Q testmanager\htdocs\js\es.js
del /F /Q testmanager\htdocs\js\fr.js
del /F /Q testmanager\htdocs\js\it.js
del /F /Q testmanager\htdocs\js\ko.js
del /F /Q testmanager\htdocs\js\ru.js

cd ..
