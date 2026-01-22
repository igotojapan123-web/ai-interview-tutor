# video_recorder.py
# 동영상 녹화 및 처리 유틸리티

import os
import base64
import tempfile
import subprocess
from typing import Optional, Tuple, List


def get_video_recorder_html(duration: int = 30, show_audio_indicator: bool = True) -> str:
    """
    동영상 녹화 HTML/JavaScript 컴포넌트
    녹화 완료 후 다운로드 버튼 제공
    """
    audio_indicator = """
        <div id="audio-indicator" style="
            display: none;
            margin-top: 10px;
            padding: 10px;
            background: #e8f5e9;
            border-radius: 8px;
            text-align: center;
        ">
            <span style="color: #2e7d32;">🎤 마이크 연결됨</span>
            <div id="audio-level" style="
                height: 4px;
                background: #c8e6c9;
                margin-top: 8px;
                border-radius: 2px;
                overflow: hidden;
            ">
                <div id="audio-level-bar" style="
                    height: 100%;
                    width: 0%;
                    background: #4caf50;
                    transition: width 0.1s;
                "></div>
            </div>
        </div>
    """ if show_audio_indicator else ""

    return f"""
    <style>
        .recorder-container {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 720px;
            margin: 0 auto;
            padding: 20px;
        }}
        .video-box {{
            position: relative;
            background: #000;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }}
        #preview {{
            width: 100%;
            display: block;
            transform: scaleX(-1);
        }}
        #playback {{
            width: 100%;
            display: none;
        }}
        .overlay {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(to bottom, rgba(0,0,0,0.5), transparent);
        }}
        .rec-badge {{
            display: none;
            background: #f44336;
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            animation: pulse 1s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
        }}
        .timer {{
            background: rgba(0,0,0,0.6);
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 16px;
            font-family: monospace;
        }}
        .controls {{
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-top: 20px;
        }}
        .btn {{
            border: none;
            padding: 14px 32px;
            font-size: 16px;
            font-weight: 600;
            border-radius: 30px;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        .btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        .btn-record {{
            background: linear-gradient(135deg, #f44336, #e91e63);
            color: white;
        }}
        .btn-record:hover:not(:disabled) {{
            transform: scale(1.05);
            box-shadow: 0 4px 20px rgba(244,67,54,0.4);
        }}
        .btn-stop {{
            background: linear-gradient(135deg, #424242, #616161);
            color: white;
        }}
        .btn-download {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
        .btn-download:hover:not(:disabled) {{
            transform: scale(1.05);
        }}
        .btn-retry {{
            background: #f5f5f5;
            color: #333;
        }}
        .status {{
            text-align: center;
            margin-top: 16px;
            font-size: 15px;
            color: #666;
        }}
        .status.recording {{
            color: #f44336;
            font-weight: 600;
        }}
        .status.complete {{
            color: #4caf50;
            font-weight: 600;
        }}
        .progress-bar {{
            height: 6px;
            background: #e0e0e0;
            border-radius: 3px;
            margin-top: 16px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.2s linear;
        }}
        .help-text {{
            background: #fff3e0;
            border-radius: 10px;
            padding: 14px;
            margin-top: 16px;
            font-size: 14px;
            color: #e65100;
        }}
    </style>

    <div class="recorder-container">
        <div class="video-box">
            <video id="preview" autoplay muted playsinline></video>
            <video id="playback" controls playsinline></video>
            <div class="overlay">
                <div class="rec-badge" id="rec-badge">● REC</div>
                <div class="timer" id="timer">00:00</div>
            </div>
        </div>

        {audio_indicator}

        <div class="progress-bar" id="progress-bar" style="display: none;">
            <div class="progress-fill" id="progress-fill"></div>
        </div>

        <div class="controls">
            <button class="btn btn-record" id="btn-record" onclick="startRecording()">
                🎬 녹화 시작
            </button>
            <button class="btn btn-stop" id="btn-stop" onclick="stopRecording()" style="display: none;">
                ⏹ 녹화 종료
            </button>
            <button class="btn btn-download" id="btn-download" onclick="downloadVideo()" style="display: none;">
                💾 영상 저장
            </button>
            <button class="btn btn-retry" id="btn-retry" onclick="retryRecording()" style="display: none;">
                🔄 다시 촬영
            </button>
        </div>

        <div class="status" id="status">
            녹화 버튼을 눌러 시작하세요 (최대 {duration}초)
        </div>

        <div class="help-text">
            💡 <strong>사용법:</strong> 녹화 → 저장 버튼 클릭 → 다운로드된 영상을 아래에 업로드
        </div>
    </div>

    <script>
        const MAX_DURATION = {duration};
        let stream = null;
        let mediaRecorder = null;
        let recordedChunks = [];
        let recordedBlob = null;
        let timerInterval = null;
        let elapsed = 0;
        let audioContext = null;
        let analyser = null;

        async function initCamera() {{
            try {{
                stream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ width: {{ ideal: 1280 }}, height: {{ ideal: 720 }}, facingMode: 'user' }},
                    audio: {{ echoCancellation: true, noiseSuppression: true }}
                }});
                document.getElementById('preview').srcObject = stream;

                // Audio level indicator
                if ({str(show_audio_indicator).lower()}) {{
                    setupAudioIndicator();
                }}
            }} catch (err) {{
                document.getElementById('status').textContent = '⚠️ 카메라/마이크 접근 권한이 필요합니다';
                document.getElementById('status').style.color = '#f44336';
                console.error(err);
            }}
        }}

        function setupAudioIndicator() {{
            try {{
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                analyser = audioContext.createAnalyser();
                const source = audioContext.createMediaStreamSource(stream);
                source.connect(analyser);
                analyser.fftSize = 256;

                document.getElementById('audio-indicator').style.display = 'block';

                const dataArray = new Uint8Array(analyser.frequencyBinCount);
                function updateLevel() {{
                    analyser.getByteFrequencyData(dataArray);
                    const avg = dataArray.reduce((a, b) => a + b) / dataArray.length;
                    const level = Math.min(100, avg * 1.5);
                    document.getElementById('audio-level-bar').style.width = level + '%';
                    requestAnimationFrame(updateLevel);
                }}
                updateLevel();
            }} catch (e) {{
                console.log('Audio indicator not available');
            }}
        }}

        function startRecording() {{
            recordedChunks = [];
            elapsed = 0;

            const options = {{ mimeType: 'video/webm;codecs=vp9,opus' }};
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {{
                options.mimeType = 'video/webm';
            }}

            mediaRecorder = new MediaRecorder(stream, options);

            mediaRecorder.ondataavailable = (e) => {{
                if (e.data.size > 0) recordedChunks.push(e.data);
            }};

            mediaRecorder.onstop = () => {{
                recordedBlob = new Blob(recordedChunks, {{ type: 'video/webm' }});
                const url = URL.createObjectURL(recordedBlob);

                document.getElementById('preview').style.display = 'none';
                document.getElementById('playback').style.display = 'block';
                document.getElementById('playback').src = url;

                document.getElementById('btn-download').style.display = 'inline-flex';
                document.getElementById('btn-retry').style.display = 'inline-flex';
                document.getElementById('status').textContent = '✅ 녹화 완료! 영상을 저장하세요';
                document.getElementById('status').className = 'status complete';
            }};

            mediaRecorder.start(100);

            // UI 업데이트
            document.getElementById('btn-record').style.display = 'none';
            document.getElementById('btn-stop').style.display = 'inline-flex';
            document.getElementById('rec-badge').style.display = 'block';
            document.getElementById('progress-bar').style.display = 'block';
            document.getElementById('status').textContent = '🎬 녹화 중...';
            document.getElementById('status').className = 'status recording';

            // 타이머
            timerInterval = setInterval(() => {{
                elapsed++;
                const mins = Math.floor(elapsed / 60).toString().padStart(2, '0');
                const secs = (elapsed % 60).toString().padStart(2, '0');
                document.getElementById('timer').textContent = mins + ':' + secs;
                document.getElementById('progress-fill').style.width = (elapsed / MAX_DURATION * 100) + '%';

                if (elapsed >= MAX_DURATION) {{
                    stopRecording();
                }}
            }}, 1000);
        }}

        function stopRecording() {{
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {{
                mediaRecorder.stop();
            }}
            clearInterval(timerInterval);

            document.getElementById('btn-stop').style.display = 'none';
            document.getElementById('rec-badge').style.display = 'none';
            document.getElementById('progress-bar').style.display = 'none';
        }}

        function downloadVideo() {{
            if (!recordedBlob) return;

            const a = document.createElement('a');
            a.href = URL.createObjectURL(recordedBlob);
            a.download = 'interview_' + new Date().toISOString().slice(0,19).replace(/[:-]/g, '') + '.webm';
            a.click();

            document.getElementById('status').textContent = '💾 저장됨! 아래 업로드 영역에 파일을 올려주세요';
        }}

        function retryRecording() {{
            recordedChunks = [];
            recordedBlob = null;
            elapsed = 0;

            document.getElementById('preview').style.display = 'block';
            document.getElementById('playback').style.display = 'none';
            document.getElementById('playback').src = '';

            document.getElementById('btn-record').style.display = 'inline-flex';
            document.getElementById('btn-download').style.display = 'none';
            document.getElementById('btn-retry').style.display = 'none';
            document.getElementById('timer').textContent = '00:00';
            document.getElementById('status').textContent = '녹화 버튼을 눌러 시작하세요';
            document.getElementById('status').className = 'status';
        }}

        // 초기화
        initCamera();
    </script>
    """


def extract_frames_from_video(video_bytes: bytes, num_frames: int = 5) -> List[str]:
    """
    동영상에서 프레임 추출 (base64 인코딩)
    ffmpeg 사용
    """
    frames = []

    with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as vf:
        vf.write(video_bytes)
        video_path = vf.name

    try:
        # 동영상 길이 확인
        duration_cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', video_path
        ]

        try:
            result = subprocess.run(duration_cmd, capture_output=True, text=True, timeout=30)
            duration = float(result.stdout.strip()) if result.stdout.strip() else 10
        except:
            duration = 10

        # 프레임 추출 간격 계산
        interval = max(duration / (num_frames + 1), 0.5)

        for i in range(num_frames):
            timestamp = interval * (i + 1)

            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as img_file:
                img_path = img_file.name

            extract_cmd = [
                'ffmpeg', '-y', '-ss', str(timestamp), '-i', video_path,
                '-frames:v', '1', '-q:v', '2', img_path
            ]

            try:
                subprocess.run(extract_cmd, capture_output=True, timeout=30)

                if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
                    with open(img_path, 'rb') as f:
                        img_base64 = base64.b64encode(f.read()).decode('utf-8')
                        frames.append(img_base64)
            except Exception as e:
                print(f"Frame extraction error: {e}")
            finally:
                if os.path.exists(img_path):
                    os.unlink(img_path)

    except Exception as e:
        print(f"Video processing error: {e}")

    finally:
        if os.path.exists(video_path):
            os.unlink(video_path)

    return frames


def extract_audio_from_video(video_bytes: bytes) -> Optional[bytes]:
    """
    동영상에서 오디오 추출
    ffmpeg 사용
    """
    with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as vf:
        vf.write(video_bytes)
        video_path = vf.name

    audio_path = video_path.replace('.webm', '.mp3')

    try:
        extract_cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-vn', '-acodec', 'libmp3lame', '-q:a', '2', audio_path
        ]

        subprocess.run(extract_cmd, capture_output=True, timeout=60)

        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            with open(audio_path, 'rb') as f:
                return f.read()

    except Exception as e:
        print(f"Audio extraction error: {e}")

    finally:
        if os.path.exists(video_path):
            os.unlink(video_path)
        if os.path.exists(audio_path):
            os.unlink(audio_path)

    return None


def check_ffmpeg_available() -> bool:
    """ffmpeg 설치 여부 확인"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False
