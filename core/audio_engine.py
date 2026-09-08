import asyncio
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import csv
import librosa
import time

class AudioEngine:
    def __init__(self, source='normal.wav'):
        self.source = source
        self.new_source = None
        self.running = False
        self.highest_threat_confidence = 0.0
        self.detected_sound_class = "System Initialization..."
        
        print("Initializing Yamnet Audio Engine...")
        
        import os
        cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "yamnet_cache"))
        os.environ["TFHUB_CACHE_DIR"] = cache_dir
        self.model = hub.load('https://tfhub.dev/google/yamnet/1')
        class_map_path = self.model.class_map_path().numpy().decode('utf-8')
        class_names = []
        with open(class_map_path) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                class_names.append(row['display_name'])
        self.class_names = np.array(class_names)

    
        self.critical_classes = [
            "Glass", "Shatter", "Smash, crash", "Breaking", 
            "Shout", "Yell", "Scream", 
            "Gunshot, gunfire", "Explosion", "Alarm", "Siren", "Emergency vehicle"
        ]

    async def start_processing(self):
        self.running = True
        await asyncio.to_thread(self._process_loop)

    def _process_loop(self):
        while self.running:
            if self.new_source:
                self.source = self.new_source
                self.new_source = None

            try:
                waveform, sr = librosa.load(self.source, sr=16000)
            except Exception as e:
                print(f"Error loading {self.source}: {e}")
                time.sleep(1)
                continue

            chunk_size = 16000  # 1 second audio at 16000Hz
            for i in range(0, len(waveform), chunk_size):
                if not self.running: return
                if self.new_source: break
                
                chunk = waveform[i:i+chunk_size]
                if len(chunk) < chunk_size:
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
                    
                scores, embeddings, spectrogram = self.model(chunk)
                mean_scores = np.mean(scores.numpy(), axis=0)
                
                # Check for critical classes among all detections
                detected_crit_score = 0.0
                detected_crit_name = None
                for crit in self.critical_classes:
                    for idx, name in enumerate(self.class_names):
                        if crit.lower() in name.lower() and mean_scores[idx] > 0.05:
                            if mean_scores[idx] > detected_crit_score:
                                detected_crit_score = float(mean_scores[idx])
                                detected_crit_name = name

                if detected_crit_name and detected_crit_score > 0.05:
                    self.highest_threat_confidence = detected_crit_score
                    self.detected_sound_class = detected_crit_name
                else:
                    top_class_index = np.argmax(mean_scores)
                    top_class_name = self.class_names[top_class_index]
                    self.highest_threat_confidence *= 0.5
                    if self.highest_threat_confidence < 0.05:
                        self.highest_threat_confidence = 0.0
                        self.detected_sound_class = f"Ambient ({top_class_name})"

                time.sleep(1.0) # sleep 1s to simulate real-time processing

    def set_source(self, source):
        self.new_source = source

    def stop(self):
        self.running = False
