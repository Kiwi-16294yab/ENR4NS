import os
import gc
import glob
import logging
import numpy as np
from datetime import datetime
from scipy.io import wavfile
from scipy.signal import decimate

# Folders path
BASE_DIR  = "/home/omg/raw"
READY_DIR = "/home/omg/ready"
LOG_FILE  = "/home/omg/processor.log"

os.makedirs(READY_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

FS_TARGET     = 200
FS_ORIG       = 8000
TOTAL_SAMPLES = 24 * 60 * 60 * FS_TARGET  

def process_manual_test():
    today_str = datetime.now().strftime("%Y-%m-%d")
    logging.info(f"{today_str} Processing each audio recording.")
    
    search_pattern = os.path.join(BASE_DIR, f"{today_str}_*.wav")
    file_list      = sorted(glob.glob(search_pattern))
    
    if not file_list:
        logging.warning("No audio file was found to process.")
        return

    master_audio = np.zeros(TOTAL_SAMPLES, dtype=np.int16)
    
    for file_path in file_list:
        filename = os.path.basename(file_path)
        try:
            time_part            = filename.split('_')[1].replace('.wav', '')
            hour, minute, second = map(int, time_part.split('-'))
            
            start_sec    = (hour * 3600) + (minute * 60) + second
            start_idx    = start_sec * FS_TARGET
            
            fs, raw_data = wavfile.read(file_path)
            
            if fs != FS_ORIG:
                logging.warning(f"{filename} {fs}Hz. {FS_ORIG}Hz was expected. Has been skipped.")
                continue
            
            decimated_step1 = decimate(raw_data,        8, ftype='iir', zero_phase=True)
            decimated_data  = decimate(decimated_step1, 5, ftype='iir', zero_phase=True)
            
            decimated_data  = np.round(decimated_data).astype(np.int16)
            
            actual_end_idx  = start_idx + len(decimated_data)
            
            if actual_end_idx > TOTAL_SAMPLES:
                overflow       = actual_end_idx - TOTAL_SAMPLES
                decimated_data = decimated_data[:-overflow]
                actual_end_idx = TOTAL_SAMPLES
            
            master_audio[start_idx:actual_end_idx] = decimated_data
            
            logging.info(f"Processed: {filename} | Start: {hour:02d}:{minute:02d}:{second:02d} | Index: {start_idx} -> {actual_end_idx}")
            
            del raw_data, decimated_step1, decimated_data
            gc.collect()
            
        except Exception as e:
            logging.error(f"Error ({filename}): {e}")

    output_path = os.path.join(READY_DIR, f"{today_str}.wav")
    try:
        wavfile.write(output_path, FS_TARGET, master_audio)
        logging.info("Processing completed.")
        logging.info(f"Final file: {output_path} (Duration: {TOTAL_SAMPLES/FS_TARGET} seconds.)")
    except Exception as e:
        logging.error(f"Writing Error: {e}")
    
    del master_audio
    gc.collect()

if __name__ == "__main__":
    process_manual_test()