@echo off
set PYTHONUTF8=1
cd /d "C:\Projetos\bot-whatsapp"
if not exist logs mkdir logs
echo ================== %date% %time% ================== >> logs\campanha.log
python limpar_nomes.py >> logs\campanha.log 2>&1
python verificar_whatsapp.py >> logs\campanha.log 2>&1
python bloquear_sem_whatsapp.py >> logs\campanha.log 2>&1
python campanha_whatsapp.py >> logs\campanha.log 2>&1
python enviar_resumo.py >> logs\campanha.log 2>&1
copy /Y leads.xlsx "G:\Meu Drive\Compartilhado\Queiroz Seguros\BOT\leads_backup.xlsx" >> logs\campanha.log 2>&1
