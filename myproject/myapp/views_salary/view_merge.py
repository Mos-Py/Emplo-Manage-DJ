import os, time, tempfile
import xlwings as xw
from django.http import HttpResponse
from django.conf import settings
from pathlib import Path
from datetime import datetime
from myapp.models import SalaryRecord
from django.core.files.uploadedfile import SimpleUploadedFile
from urllib.parse import quote

from .convert_excel_pdf import convert_excel_to_pdf
from .view_excel import export_person_salary_excel_to_file

THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม",
    "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน",
    "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]

def merge_excels_to_one(file_paths, output_path):
    app = xw.App(visible=False)
    final_wb = app.books.add()
    final_ws = final_wb.sheets[0]
    current_row = 1

    for idx, path in enumerate(file_paths):
        wb = app.books.open(path)
        ws = wb.sheets[0]

        used_range = ws.used_range
        row_count = used_range.last_cell.row
        col_count = used_range.last_cell.column

        ws.range((1, 1), (row_count, col_count)).copy(final_ws.range((current_row, 1)))

        # จัดความสูงของแต่ละแถว
        for r in range(1, row_count + 1):
            final_ws.range((current_row + r - 1, 1)).row_height = ws.range((r, 1)).row_height

        if idx == 0:
            for c in range(1, col_count + 1):
                final_ws.range((1, c)).column_width = ws.range((1, c)).column_width

        # ✅ เพิ่ม Page Break ทุก 2 คน
        if (idx + 1) % 2 == 0:
            final_ws.api.HPageBreaks.Add(final_ws.range((current_row, 1)).api)

        current_row += row_count - 7  
        wb.close()

    final_ws.api.PageSetup.Zoom = False
    final_ws.api.PageSetup.FitToPagesTall = 1
    final_ws.api.PageSetup.FitToPagesWide = 1
    final_wb.save(str(output_path))
    final_wb.close()
    app.quit()
    return output_path

def export_all_salary_excel(request):
    month_str = request.GET.get("month")
    if not month_str:
        return HttpResponse("Missing month", status=400)

    month_date = datetime.strptime(month_str, "%Y-%m").date()
    salary_records = SalaryRecord.objects.filter(month=month_date)
    if not salary_records.exists():
        return HttpResponse("ไม่พบพนักงานที่บันทึกเงินเดือนในเดือนนี้", status=404)

    temp_files = []
    for sr in salary_records:
        temp_path = Path(tempfile.gettempdir()) / f"slip_{sr.person.id}_{int(time.time())}.xlsx"
        success, result = export_person_salary_excel_to_file(sr.person.id, month_str, temp_path)
        if success:
            temp_files.append(temp_path)

    merged_path = Path(tempfile.gettempdir()) / f"merge_salary_all_{int(time.time())}.xlsx"
    merge_excels_to_one(temp_files, merged_path)

    with open(merged_path, "rb") as f:
        file_data = f.read()

    response = HttpResponse(file_data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="รวมสลิปเงินเดือน_{month_str}.xlsx"'
    return response

def export_all_salary_pdf(request):
    try:
        month_str = request.GET.get("month")
        if not month_str:
            return HttpResponse("Missing month", status=400)

        print(f"🧾 [DEBUG] export_all_salary_pdf เรียกเดือน: {month_str}")

        # 1. สร้าง Excel รวมจากระบบ
        excel_response = export_all_salary_excel(request)
        if excel_response.status_code != 200:
            return HttpResponse("ไม่สามารถสร้าง Excel รวมได้", status=500)

        # 2. บันทึกไฟล์ Excel ลง temp
        temp_dir = tempfile.gettempdir()
        excel_path = os.path.join(temp_dir, f"merge_excel_{int(time.time())}.xlsx")
        with open(excel_path, "wb") as f:
            f.write(excel_response.content)

        # 3. สร้างชื่อไฟล์ภาษาไทย
        year, month = [int(x) for x in month_str.split("-")]
        thai_month = THAI_MONTHS[month]
        thai_year = year + 543
        filename = f"สลิปเงินเดือน_{thai_month}_{thai_year}.pdf"
        
        print(f"🧾 [DEBUG] กำหนดชื่อไฟล์: {filename}")
        
        # 4. เรียก convert_excel_to_pdf โดยสร้าง fake request พร้อมชื่อไฟล์
        with open(excel_path, "rb") as f:
            uploaded = SimpleUploadedFile("merge.xlsx", f.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            class FakeRequest:
                method = "POST"
                FILES = {"excel_file": uploaded}
                custom_filename = filename  # เพิ่มชื่อไฟล์ที่ต้องการ
                
            fake_request = FakeRequest()
            pdf_response = convert_excel_to_pdf(fake_request)

        # 5. ตรวจสอบว่า Content-Disposition ถูกตั้งค่าหรือไม่ หากไม่มีให้เพิ่มเข้าไป
        if 'Content-Disposition' not in pdf_response:
            encoded_filename = quote(filename)
            pdf_response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}'
            
        print(f"🧾 [DEBUG] Content-Disposition: {pdf_response['Content-Disposition']}")

        return pdf_response

    except Exception as e:
        print(f"⚠️ [ERROR] export_all_salary_pdf: {e}")
        import traceback
        print(traceback.format_exc())  # แสดง stack trace เพื่อดีบัก
        return HttpResponse(f"ERROR: {e}", status=500)