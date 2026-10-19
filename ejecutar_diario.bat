@echo off
setlocal
cd /d "%~dp0"

echo ======================================================== >> data\ejecucion_diaria.log
echo Ejecutando SearchJobs Agente Diario: %date% %time% >> data\ejecucion_diaria.log
echo ======================================================== >> data\ejecucion_diaria.log

py -3 src\job_agent.py >> data\ejecucion_diaria.log 2>&1

echo Finalizado con codigo: %ERRORLEVEL% a las %time% >> data\ejecucion_diaria.log
echo. >> data\ejecucion_diaria.log

if exist .git (
    git add data/empleo.db data/ofertas.json >> data\ejecucion_diaria.log 2>&1
    git commit -m "chore: actualizacion diaria local bd y ofertas json [skip ci]" >> data\ejecucion_diaria.log 2>&1
    git push origin main >> data\ejecucion_diaria.log 2>&1
)

endlocal
