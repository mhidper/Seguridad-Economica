@echo off
chcp 65001 > nul
echo ========================================================
echo   INICIANDO COPIA DE SEGURIDAD A GOOGLE DRIVE
echo ========================================================
echo.
echo Origen: %CD%
echo Destino: G:\Mi unidad\Proyectos\Seguridad Economica
echo.
echo Sincronizando archivos (excluyendo .git y .venv)...
echo.

robocopy "%CD%" "G:\Mi unidad\Proyectos\Seguridad Economica" /MIR /XD .git .venv /R:3 /W:5 /NDL /NP

echo.
echo ========================================================
echo   COPIA DE SEGURIDAD FINALIZADA CON EXITO
echo ========================================================
pause
