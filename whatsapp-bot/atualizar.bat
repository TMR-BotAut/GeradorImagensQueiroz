@echo off
chcp 65001 >nul
setlocal
title Atualizar Bot Queiroz Seguros

REM ==========================================================================
REM  Atualizador de 1 clique — baixa os scripts novos do GitHub e reinicia o
REM  webhook. Rode (2 cliques) sempre que for avisado que ha ajuste novo.
REM  Nao mexe na campanha (ela roda sozinha no horario). So atualiza arquivos.
REM ==========================================================================

set "PASTA=C:\Projetos\bot-whatsapp"
set "REPO=https://raw.githubusercontent.com/TMR-BotAut/GeradorImagensQueiroz/claude/confident-ride-lmz6oh/whatsapp-bot"

cd /d "%PASTA%"

echo ============================================================
echo   ATUALIZANDO BOT QUEIROZ SEGUROS
echo ============================================================
echo.
echo [1/3] Baixando arquivos novos do GitHub...
curl -s -o webhook_respostas.py  "%REPO%/webhook_respostas.py"  && echo    ok webhook_respostas.py
curl -s -o campanha_whatsapp.py  "%REPO%/campanha_whatsapp.py"  && echo    ok campanha_whatsapp.py
curl -s -o bloquear_numero.py    "%REPO%/bloquear_numero.py"    && echo    ok bloquear_numero.py

echo.
echo [2/3] Reiniciando o webhook (porta 5000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
schtasks /run /tn "Webhook WhatsApp" >nul 2>&1

echo    aguardando o webhook subir...
timeout /t 5 >nul

echo.
echo [3/3] Conferindo se voltou...
echo ------------------------------------------------------------
curl -s http://localhost:5000/status
echo.
echo ------------------------------------------------------------
echo.
echo Se apareceu "status":"online" acima, esta tudo certo.
echo.
pause
