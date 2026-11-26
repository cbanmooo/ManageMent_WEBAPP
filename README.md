# 5D BIM Executive Material & Cost Dashboard

เว็บแอพพลิเคชันสำหรับติดตามปริมาณวัสดุและงบประมาณประมาณการจากโมเดล Revit (แยกตามโครงการ อาคาร ชั้น ห้อง และหมวดวัสดุ)

## ไฟล์ในโปรเจกต์
- `app.py`: โค้ดหลักของเว็บแอพ Streamlit
- `requirements.txt`: รายการไลบรารี Python ที่จำเป็น
- `BOQ_Piping.csv`: ข้อมูลถอดปริมาณท่อจาก Revit Schedule
- `BOQ_Fitting.csv`: ข้อมูลถอดปริมาณข้อต่อฟิตติ้งจาก Revit Schedule

## วิธี Deploy ขึ้น Streamlit Community Cloud ฟรี
1. สร้าง Repository ใหม่บน GitHub และอัปโหลดไฟล์ทั้งหมดในโฟลเดอร์นี้ขึ้นไป
2. เข้าเว็บไซต์ [share.streamlit.io](https://share.streamlit.io) และล็อกอินด้วยบัญชี GitHub
3. กด **New app** เลือก Repository, Branch (`main`) และ Main file path (`app.py`) แล้วกด **Deploy!**
