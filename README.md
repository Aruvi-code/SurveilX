# 👁️ Project SurveilX | Multi-Modal Security Intelligence 🛡️🔊

[![Version](https://img.shields.io/badge/Version-1.0.0-blue?style=for-the-badge)](#)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005863?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-FF4B11?style=for-the-badge&logo=ultralytics&logoColor=white)](https://ultralytics.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)](https://www.tensorflow.org/)

**SurveilX** is a high-performance command center that fuses **Real-Time Computer Vision** with **Acoustic Anomaly Detection**. Designed for tactical environments, it provides a comprehensive 360° overview by correlating visual evidence with acoustic signatures.

![Tactical Dashboard](static/dashboard_mockup.png)

---

## 🧠 Tiered Intelligence Architecture

Our architecture is segmented into specialized engines that work in parallel to ensure low-latency response:

1.  **Vision Engine (YOLOv8)**: Handles high-speed object tracking, biometric ID persistence, and sensor sabotage detection (blur/blackout).
2.  **Audio Engine (YAMNet)**: Processes environmental acoustic streams to classify 521+ audio events, focusing on critical signatures like glass breaking or shouting.
3.  **Threat Engine (Logic Fusion)**: Acts as the "Cognitive Core," fusing data from vision and audio layers to calculate a consolidated threat level.

---

## 🛡️ Late-Fusion Logic

SurveilX utilizes **Late-Fusion Logic** to significantly reduce false positives. Instead of triggering on a single sensor alert, the system correlates probabilities:
- **Decision Matrix**: A `Vision Anomaly (0.6)` paired with an `Audio Anomaly (0.4)` aggregates to a high-confidence alert.
- **Example**: If a camera experiences a "Blackout" while the Audio Engine detects "Screaming," the system immediately escalates to **CRITICAL**, triggers the AI Voice Alert, and locks down the forensic evidence.

---

## 🚀 Core Features

- **Behavioral Analytics**: Automated Loitering Detection with unique ID persistence.
- **Tamper Protection**: Real-time detection of lens blurring, repositioning, or covering.
- **📢 AI Voice Synergy**: Integrated Speech Synthesis for verbal tactical warnings.
- **Forensic Logging**: Automated high-resolution evidence capture and multi-modal reporting.

---

## 🛰️ Technical Stack

-   **Backend**: FastAPI, Uvicorn, Pydantic (Version-Locked)
-   **Computer Vision**: Ultralytics YOLOv8, OpenCV
-   **Deep Learning (Audio)**: TensorFlow Hub, YAMNet, Librosa
-   **Security**: Asynchronous file I/O via `aiofiles`
-   **Frontend**: Tactical Neural UI (HTML5/CSS3/JS)

---

## 📦 Installation & Deployment

### ⚡ Quick Start
```bash
# Clone the repository
git clone https://github.com/Aruvi-code/SurveilX.git
cd SurveilX

# Deployment-ready environment
python -m venv venv
source venv/bin/activate  # (.\venv\Scripts\activate on Windows)
pip install -r requirements.txt
copy .env.example .env    # then edit credentials / camera URL
```

### 🛰️ Launch Command
```bash
python app.py
```
Access the Tactical Dashboard at `http://localhost:5000`.

Keep `DRY_RUN=true` until SMTP/Twilio credentials are verified. CRITICAL events then log email and phone actions without sending.

### Live CCTV / RTSP
Set in `.env`:
```
CAMERA_SOURCE=rtsp
RTSP_URL=rtsp://user:pass@CAMERA_IP:554/Streaming/Channels/101
CAMERA_ID=CAM-01
CAMERA_FPS=15
```
Webcam: `CAMERA_SOURCE=webcam` and `CAMERA_INDEX=0`. File demo: `CAMERA_SOURCE=file` and `VIDEO_FILE=normal.mp4`.

On the dashboard use **Live CCTV / RTSP (.env)** or **Switch to Live Webcam**. The capture thread reconnects if the RTSP session drops.

### Email + phone alerts
CRITICAL detections (after `CONFIRM_FRAMES` consecutive hits and `ALERT_COOLDOWN_SEC`) enqueue work off the video thread:
- SMTP email with event type, timestamp, camera ID, confidence, and boxed snapshot
- Twilio Voice TwiML: “Critical alert detected at camera X”

Logs land in `outputs/alerts.csv` and `outputs/alerts.db`. Snapshots and an annotated demo video go to `outputs/`.

### Paper evaluation
```bash
python scripts/evaluate.py
pytest
```
Metrics and plots are written to `outputs/results/` (Precision, Recall, F1, mAP, confusion matrix, FPS, alert latency).

---

## 🛡️ License
Distributed under the **MIT License**. See `LICENSE` for more information.

---
**"Acoustic Sight. Visual Intelligence. Total Defense."**
