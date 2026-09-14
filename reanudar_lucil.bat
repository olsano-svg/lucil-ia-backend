@echo off
title Lucil AI - Asistente Personal Local
echo ========================================================
echo         INICIANDO LUCIL AI (100% LOCAL)
echo ========================================================
echo.

echo 1. Iniciando motor local Ollama desde disco G:...
set OLLAMA_MODELS=G:\Ollama\Models
start "" /B "G:\Ollama\Programs\Ollama\ollama.exe" serve

timeout /t 2 /nobreak >nul

echo 2. Iniciando Backend FastAPI en puerto 8000...
cd /d "E:\chat en vivo y tenxo y voz conversacional . IA personalizada\backend"
start "Lucil Backend (Puerto 8000)" cmd /k ".\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak >nul

echo 3. Iniciando Frontend Web Expo en puerto 8081...
cd /d "E:\chat en vivo y tenxo y voz conversacional . IA personalizada\mobile"
set CI=1
start "Lucil Frontend Web (Puerto 8081)" cmd /k "npx expo start --web --port 8081"

echo.
echo ========================================================
echo  Todo listo! Abre tu navegador en: http://localhost:8081
echo  Usuario: admin  ^|  Contrasena: delarosa00
echo ========================================================
pause
