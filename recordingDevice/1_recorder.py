import subprocess
import os
import time

BASE_DIR = "/home/omg/raw" # Raw folder path
os.makedirs(BASE_DIR, exist_ok=True)

def start_recording():
    output_pattern = os.path.join(BASE_DIR, "%Y-%m-%d_%H-%M-%S.wav")
    
    cmd = [
        "ffmpeg", 
        "-hide_banner", 
        "-loglevel", "warning",
        "-thread_queue_size", "4096",
        
        # Input 
        "-f", "alsa", 
        "-i", "plughw:2,0", # Soundcard
        
        # Output
        "-ac", "1",
        "-ar", "8000",
        "-c:a", "pcm_s16le",
        "-f", "segment",
        "-segment_time", "300",
        "-segment_atclocktime", "1",
        "-strftime", "1",
        "-flush_packets", "1",
        output_pattern
    ]
    
    print(f"[{time.ctime()}] Recording has been started..")
    subprocess.run(cmd)

while True:
    try:
        start_recording()
    except Exception as e:
        print(f"[{time.ctime()}] Unexpected Error: {e}")
    
    print("System restarts in 2 seconds..")
    time.sleep(2)