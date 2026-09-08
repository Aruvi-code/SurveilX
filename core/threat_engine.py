import asyncio
import time
import os
import cv2
from datetime import datetime
from core.reporting import generate_and_save_report
from core.notification_engine import NotificationEngine

class ThreatEngine:
    def __init__(self, vision_engine, audio_engine):
        self.vision = vision_engine
        self.audio = audio_engine
        self.running = False
        self.current_threat_level = "Normal"
        self.active_alerts = []
        self.last_alert_time = 0
        self.notifier = NotificationEngine()
        os.makedirs("evidence_logs", exist_ok=True)

    async def monitor_threats(self):
        self.running = True
        while self.running:
            vision_conf = self.vision.highest_person_confidence
            audio_conf = self.audio.highest_threat_confidence
            loiterers = self.vision.active_loiterers
            
            threat_score = (vision_conf * 0.6) + (audio_conf * 0.4)
            
            if len(loiterers) > 0:
                threat_score += 0.3
            if self.vision.tampering_status["blur"] or self.vision.tampering_status["blackout"]:
                threat_score += 0.5
                
            self.active_alerts = []
            if len(loiterers) > 0:
                self.active_alerts.append(f"Loitering Detected: IDs {loiterers}")
            if self.vision.tampering_status["blur"]:
                self.active_alerts.append("SENSOR SABOTAGE: Lens Blur")
            if self.vision.tampering_status["blackout"]:
                self.active_alerts.append("SENSOR SABOTAGE: Blackout")
            if audio_conf > 0.5:
                self.active_alerts.append(f"Audio Anomaly: {self.audio.detected_sound_class}")
                
            if threat_score > 0.75:
                self.current_threat_level = "Critical"
            elif threat_score > 0.4:
                self.current_threat_level = "Suspicious"
            else:
                self.current_threat_level = "Normal"
                
            if self.current_threat_level in ["Suspicious", "Critical"]:
                await self.trigger_alert()
                
            await asyncio.sleep(0.5)

    async def trigger_alert(self):
        current_time = time.time()
        if current_time - self.last_alert_time < 5.0:
            return
            
        self.last_alert_time = current_time
        
        frame = self.vision.get_latest_frame()
        if frame is None:
            return
            
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        base_path = os.path.join("evidence_logs", timestamp_str)
        img_path = f"{base_path}.jpg"
        txt_path = f"{base_path}.txt"
        
        await asyncio.to_thread(self._save_image, frame, img_path)
        
        reason = ", ".join(self.active_alerts) if self.active_alerts else f"Combined Vision/Audio Threat Score crossed threshold."
        
        audio_context = f"Yamnet detected '{self.audio.detected_sound_class}' with {self.audio.highest_threat_confidence*100:.1f}% confidence."
        
        await generate_and_save_report(
            txt_path, 
            alert_level=self.current_threat_level, 
            reason=reason, 
            audio_context=audio_context
        )

        # ── Send Email Alert (with snapshot attached) ──
        await self.notifier.send_email_alert(
            threat_level=self.current_threat_level,
            reasons=self.active_alerts if self.active_alerts else [reason],
            img_path=img_path
        )

        # ── Make Phone Call (only on Critical threats) ──
        if self.current_threat_level == "Critical":
            await self.notifier.make_phone_call(
                threat_level=self.current_threat_level
            )

    def _save_image(self, frame, path):
        cv2.imwrite(path, frame)

    def stop(self):
        self.running = False
