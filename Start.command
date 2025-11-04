#!/bin/bash
cd ~/Desktop/bot_senales_final
source venv/bin/activate

# --- Arranca el panel en segundo plano ---
nohup python3 panel.py > panel.log 2>&1 &
sleep 5

# --- Abre ngrok automáticamente ---
nohup ngrok http 10000 > ngrok.log 2>&1 &
sleep 5

# --- Ejecuta el bot ---
python3 bot_iq.py
