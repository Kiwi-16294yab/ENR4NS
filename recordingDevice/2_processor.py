import os
import gc
import glob
import numpy as np
from datetime import datetime
from scipy.io import wavfile
from scipy.signal import decimate

# Klasör Ayarları
BASE_DIR = "/home/omg/raw"
READY_DIR = "/home/omg/ready" # Raw klasörü ile karışmaması için ready olarak düzelttim
os.makedirs(READY_DIR, exist_ok=True)

FS_ORIG = 8000
FS_TARGET = 200
# 24 Saat * 60 Dk * 60 Sn * 200Hz = 17.280.000 Örnek (Tam 1 günlük veri boyutu)
TOTAL_SAMPLES = 24 * 60 * 60 * FS_TARGET  

def process_manual_test():
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"--- {today_str} Veri Birleştirme Başlatıldı (MATLAB Algoritması) ---")
    
    search_pattern = os.path.join(BASE_DIR, f"{today_str}_*.wav")
    file_list = sorted(glob.glob(search_pattern))
    
    if not file_list:
        print("İşlenecek dosya bulunamadı.")
        return

    # 1. 24 saatlik boş şablonu oluştur (Boşluklar 0 yani sessizlik olarak kalacak)
    master_audio = np.zeros(TOTAL_SAMPLES, dtype=np.int16)
    
    for file_path in file_list:
        filename = os.path.basename(file_path)
        try:
            # Dosya adından saat, dakika ve saniyeyi çek (Örn: %H-%M-%S)
            time_part = filename.split('_')[1].replace('.wav', '')
            hour, minute, second = map(int, time_part.split('-'))
            
            # KESİN BAŞLANGIÇ İNDEKSİNİ HESAPLA
            start_sec = (hour * 3600) + (minute * 60) + second
            start_idx = start_sec * FS_TARGET
            
            # FFmpeg yerine doğrudan Scipy ile 8kHz dosyayı oku
            fs, raw_data = wavfile.read(file_path)
            
            if fs != FS_ORIG:
                print(f"Uyarı: {filename} {fs}Hz. {FS_ORIG}Hz bekleniyordu. Atlanıyor.")
                continue
            
            # MATLAB İLE AYNI DECIMATE ALGORİTMASI
            # Faktör 40 (8000/200). IIR filtre stabilitesi için faktör > 13 olduğunda 
            # kademeli decimate yapılması en iyi pratiktir (40 = 8 * 5).
            # zero_phase=True, MATLAB'ın filtfilt çift yönlü filtrelemesine denk gelir.
            decimated_step1 = decimate(raw_data, 8, ftype='iir', zero_phase=True)
            decimated_data = decimate(decimated_step1, 5, ftype='iir', zero_phase=True)
            
            # Float olan sonucu tekrar int16 formatına çevir
            decimated_data = np.round(decimated_data).astype(np.int16)
            
            actual_end_idx = start_idx + len(decimated_data)
            
            # Gece yarısı taşma koruması (Kayıt 23:59:59 sonrasına taşıyorsa keser)
            if actual_end_idx > TOTAL_SAMPLES:
                overflow = actual_end_idx - TOTAL_SAMPLES
                decimated_data = decimated_data[:-overflow]
                actual_end_idx = TOTAL_SAMPLES
            
            # Veriyi hesaplanan endeks aralığına tam olarak yapıştır
            master_audio[start_idx:actual_end_idx] = decimated_data
            
            print(f"İşlendi: {filename} | Başlangıç: {hour:02d}:{minute:02d}:{second:02d} | İndeks: {start_idx} -> {actual_end_idx}")
            
            # Temizlik
            del raw_data, decimated_step1, decimated_data
            gc.collect()
            
        except Exception as e:
            print(f"Hata ({filename}): {e}")

    # 2. Final dosyasını kaydet
    output_path = os.path.join(READY_DIR, f"{today_str}_24h_200Hz.wav")
    try:
        wavfile.write(output_path, FS_TARGET, master_audio)
        print(f"\nİŞLEM BAŞARIYLA TAMAMLANDI!")
        print(f"Final Dosyası: {output_path} (Süre: {TOTAL_SAMPLES/FS_TARGET} saniye)")
    except Exception as e:
        print(f"Dosya yazma hatası: {e}")
    
    del master_audio
    gc.collect()

if __name__ == "__main__":
    process_manual_test()