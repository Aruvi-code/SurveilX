let isAudioUnlocked = false;
let hasPlayedCriticalSpeech = false;
let currentThreatLevel = "Normal";

document.addEventListener("DOMContentLoaded", () => {
    // 1. Audio Initialization
    const initAudioBtn = document.getElementById('init-audio-btn');
    const alarmSound = document.getElementById('alarm-sound');

    initAudioBtn.addEventListener('click', () => {
        // Unlock speech synthesis by speaking a silent string
        const utterance = new SpeechSynthesisUtterance("Audio systems online.");
        utterance.volume = 1;
        window.speechSynthesis.speak(utterance);

        // Unlock HTML5 Audio
        alarmSound.play().then(() => {
            alarmSound.pause();
            alarmSound.currentTime = 0;
            isAudioUnlocked = true;
            document.getElementById('audio-panel').style.display = 'none';
        }).catch(err => {
            console.error("Audio unlock failed:", err);
        });
    });

    // 2. Scenario Controls
    const btnNormal = document.getElementById('btn-normal');
    const btnThreat = document.getElementById('btn-threat');
    const btnWebcam = document.getElementById('btn-webcam');
    const threatIndicator = document.getElementById('threat-indicator');

    async function setScenario(scenario) {
        try {
            const feedStatus = document.getElementById('feed-status');
            feedStatus.textContent = "[SWITCHING FEED...]";
            feedStatus.style.color = "var(--neon-yellow)";

            const response = await fetch('/api/set_scenario', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scenario: scenario })
            });
            const data = await response.json();
            console.log("Scenario changed:", data);

            // Reset frontend state
            threatIndicator.className = "threat-indicator Normal";
            threatIndicator.textContent = "Normal";
            currentThreatLevel = "Normal";
            hasPlayedCriticalSpeech = false;

            feedStatus.textContent = "[LIVE]";
            feedStatus.style.color = "var(--neon-green)";
            alarmSound.pause();
            alarmSound.currentTime = 0;

            // Immediately fetch status to wipe alerts
            fetchStatus();

        } catch (error) {
            console.error("Failed to inject scenario:", error);
        }
    }

    if (btnWebcam) btnWebcam.addEventListener('click', () => setScenario('webcam'));
    btnNormal.addEventListener('click', () => setScenario('normal'));
    btnThreat.addEventListener('click', () => setScenario('threat'));

    // 2.5. Upload Controls
    const btnUpload = document.getElementById('btn-upload');
    const uploadInput = document.getElementById('scenario-upload');

    btnUpload.addEventListener('click', async () => {
        const file = uploadInput.files[0];
        if (!file) {
            alert("Please select an MP4 file.");
            return;
        }

        const feedStatus = document.getElementById('feed-status');
        try {
            feedStatus.textContent = "[PROCESSING ACOUSTIC DATA...]";
            feedStatus.style.color = "var(--neon-yellow)";

            const formData = new FormData();
            formData.append("file", file);

            const response = await fetch('/api/upload_scenario', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            console.log("Upload complete:", data);

            // Reset frontend state
            threatIndicator.className = "threat-indicator Normal";
            threatIndicator.textContent = "Normal";
            currentThreatLevel = "Normal";
            hasPlayedCriticalSpeech = false;

            feedStatus.textContent = "[LIVE]";
            feedStatus.style.color = "var(--neon-green)";
            alarmSound.pause();
            alarmSound.currentTime = 0;

            fetchStatus();
        } catch (error) {
            console.error("Upload failed:", error);
            feedStatus.textContent = "[UPLOAD FAILED]";
            feedStatus.style.color = "var(--neon-pink)";
        }
    });

    // 3. Status Polling loop
    async function fetchStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            // Threat level updates
            if (data.threat_level !== currentThreatLevel) {
                threatIndicator.textContent = data.threat_level;
                threatIndicator.className = `threat-indicator ${data.threat_level}`;
                currentThreatLevel = data.threat_level;

                if (data.threat_level === "Critical" && isAudioUnlocked) {
                    if (!hasPlayedCriticalSpeech) {
                        hasPlayedCriticalSpeech = true;

                        // Pick out best alert payload to read
                        let alertText = "Critical security breach detected.";
                        if (data.active_alerts && data.active_alerts.length > 0) {
                            alertText = data.active_alerts[0]; // say the first alert
                        }

                        try {
                            const msg = new SpeechSynthesisUtterance(`Warning! ${alertText}`);
                            msg.rate = 1.1;
                            msg.pitch = 0.9;

                            msg.onerror = (event) => {
                                console.warn("Speech Synthesis Error (Likely Network):", event.error);
                                // Fallback: Visual indicator or silent log
                            };

                            window.speechSynthesis.speak(msg);
                        } catch (e) {
                            console.error("Critical Speech Engine Failure:", e);
                        }

                        alarmSound.play().catch(e => console.log("Alarm play blocked", e));
                    }
                } else if (data.threat_level !== "Critical") {
                    hasPlayedCriticalSpeech = false;
                    alarmSound.pause();
                }
            }

            // Alerts
            const alertsContainer = document.getElementById('alerts-container');
            if (data.active_alerts && data.active_alerts.length > 0) {
                alertsContainer.innerHTML = data.active_alerts.map(alert =>
                    `<div class="alert-item">${alert}</div>`
                ).join('');
            } else {
                alertsContainer.innerHTML = '<p style="color: rgba(255,255,255,0.4); font-size: 1rem; font-style: italic;">No active alerts.</p>';
            }

            // Tamper status
            const blurEl = document.getElementById('tamper-blur');
            if (data.tampering.blur) {
                blurEl.className = 'tamper-item tamper-alert';
                blurEl.textContent = 'BLUR DETECTED';
            } else {
                blurEl.className = 'tamper-item tamper-ok';
                blurEl.textContent = 'LENS CLEAR';
            }

            const blackEl = document.getElementById('tamper-blackout');
            if (data.tampering.blackout) {
                blackEl.className = 'tamper-item tamper-alert';
                blackEl.textContent = 'BLACK OUT';
            } else {
                blackEl.className = 'tamper-item tamper-ok';
                blackEl.textContent = 'VISIBILITY OK';
            }

        } catch (error) {
            // Keep silent if backend is rebooting/restarting scenario
        }
    }

    setInterval(fetchStatus, 500);
});
