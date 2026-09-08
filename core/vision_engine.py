import asyncio
import cv2
import numpy as np
import time
import torch
from ultralytics import YOLO

class VisionEngine:
    def __init__(self, source='normal.mp4'):
        self.source = source
        self.new_source = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = YOLO('models/yolo26n.pt').to(self.device)
        self.running = False
        self.latest_frame = None
        self.latest_frame_bytes = None
        self.tampering_status = {"blur": False, "blackout": False}
        self.loitering_records = {}
        self.active_loiterers = []
        self.highest_person_confidence = 0.0

    async def start_processing(self):
        self.running = True
        await asyncio.to_thread(self._process_loop)

    def _open_capture(self, src):
        if isinstance(src, str) and src.isdigit():
            return cv2.VideoCapture(int(src))
        elif isinstance(src, int):
            return cv2.VideoCapture(src)
        return cv2.VideoCapture(src)

    def _process_loop(self):
        cap = self._open_capture(self.source)
        while self.running:
            if self.new_source is not None:
                cap.release()
                self.source = self.new_source
                self.new_source = None
                cap = self._open_capture(self.source)

            ret, frame = cap.read()
            if not ret:
                # If reading video failed, try rewinding for file
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    # Provide standby frame if video file is missing or camera disconnected
                    standby = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(standby, "SURVEILX STANDBY", (160, 220),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 243, 255), 2)
                    cv2.putText(standby, f"Source: {self.source}", (160, 270),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
                    self.latest_frame = standby
                    _, buffer = cv2.imencode('.jpg', standby)
                    self.latest_frame_bytes = buffer.tobytes()
                    time.sleep(0.1)
                    continue

            self._check_tampering(frame)

            results = self.model.track(frame, persist=True, classes=[0], verbose=False, tracker="bytetrack.yaml", device=self.device)
            
            self.highest_person_confidence = 0.0
            current_active_ids = []
            
            if results[0].boxes is not None and results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                track_ids = results[0].boxes.id.int().cpu().numpy()
                confidences = results[0].boxes.conf.cpu().numpy()

                for box, track_id, conf in zip(boxes, track_ids, confidences):
                    current_active_ids.append(track_id)
                    if conf > self.highest_person_confidence:
                        self.highest_person_confidence = float(conf)
                        
                    if track_id not in self.loitering_records:
                        self.loitering_records[track_id] = time.time()
                    else:
                        time_spent = time.time() - self.loitering_records[track_id]
                        if time_spent > 15.0 and track_id not in self.active_loiterers:
                            self.active_loiterers.append(track_id)

                    x1, y1, x2, y2 = map(int, box)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    label = f"ID: {track_id} Conf: {conf:.2f}"
                    
                    if track_id in self.active_loiterers:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                        label = f"LOITERING ID: {track_id}"
                        
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            self.loitering_records = {k: v for k, v in self.loitering_records.items() if k in current_active_ids}
            self.active_loiterers = [x for x in self.active_loiterers if x in current_active_ids]

            self.latest_frame = frame.copy()
            _, buffer = cv2.imencode('.jpg', frame)
            self.latest_frame_bytes = buffer.tobytes()

            time.sleep(0.01)
            
        cap.release()

    def _check_tampering(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        self.tampering_status["blur"] = bool(laplacian_var < 50.0)
        
        mean_intensity = np.mean(gray)
        self.tampering_status["blackout"] = bool(mean_intensity < 15.0)

    async def get_latest_frame_bytes(self):
        return self.latest_frame_bytes
        
    def get_latest_frame(self):
        return self.latest_frame

    def set_source(self, source):
        self.new_source = source

    def stop(self):
        self.running = False
