import subprocess
import os
import time

BASE_DIR = "/home/omg/raw"
os.makedirs(BASE_DIR, exist_ok=True)

def start_recording():
    output_pattern = os.path.join(BASE_DIR, "%Y-%m-%d_%H-%M-%S.wav")
    
    cmd = [
        "ffmpeg", 
        "-hide_banner", 
        "-loglevel", "warning",
        "-thread_queue_size", "4096",
        
        # --- GİRİŞ (INPUT) BÖLÜMÜ ---
        "-f", "alsa", 
        "-i", "plughw:2,0", # Cihazdan sesi kendi varsayılan ayarlarıyla (natürel) alıyoruz
        
        # --- ÇIKIŞ (OUTPUT) BÖLÜMÜ ---
        "-ac", "1",         # Aldığımız sesi yazılımsal olarak Mono'ya çeviriyoruz
        "-ar", "8000",      # Aldığımız sesi yazılımsal olarak 8000 Hz'e düşürüyoruz
        "-c:a", "pcm_s16le",
        "-f", "segment",
        "-segment_time", "300",
        "-segment_atclocktime", "1",
        "-strftime", "1",
        "-flush_packets", "1",
        output_pattern
    ]
    
    print(f"[{time.ctime()}] 8kHz Kesintisiz Buffer Korumalı Kayıt başlatıldı...")
    subprocess.run(cmd)

while True:
    try:
        start_recording()
    except Exception as e:
        print(f"[{time.ctime()}] Beklenmeyen Hata: {e}")
    
    print("Sistem 2 saniye içinde yeniden başlatılıyor...")
    time.sleep(2)