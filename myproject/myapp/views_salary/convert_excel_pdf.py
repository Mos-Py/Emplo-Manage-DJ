import os
import win32com.client
import tempfile
from django.http import FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import win32com.client
from pathlib import Path
import traceback
from urllib.parse import quote

@csrf_exempt
def convert_excel_to_pdf(request):
    if request.method != 'POST' or 'excel_file' not in request.FILES:
        return HttpResponse("ต้องส่งไฟล์ Excel มาด้วย", status=400)

    excel_file = request.FILES['excel_file']
    temp_dir = tempfile.gettempdir()
    excel_path = os.path.join(temp_dir, f"temp_excel_{os.getpid()}.xlsx")

    with open(excel_path, 'wb') as f:
        for chunk in excel_file.chunks():
            f.write(chunk)

    pdf_path = excel_path.replace(".xlsx", ".pdf")

    try:
        excel = win32com.client.DispatchEx("Excel.Application")
        wb = excel.Workbooks.Open(excel_path)

        # Set each sheet to fit 1 page
        for sheet in wb.Sheets:
            sheet.PageSetup.Zoom = False
            sheet.PageSetup.FitToPagesTall = 1
            sheet.PageSetup.FitToPagesWide = 1

        wb.ExportAsFixedFormat(0, pdf_path)
        wb.Close(False)
        excel.Quit()

        if not os.path.exists(pdf_path):
            return HttpResponse("ไม่สามารถสร้างไฟล์ PDF ได้", status=500)

        with open(pdf_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            
            # ตรวจสอบว่ามี custom_filename ถูกส่งมาหรือไม่
            # ถ้า request เป็น FakeRequest ที่ส่งมาจาก export_all_salary_pdf
            if hasattr(request, 'custom_filename') and request.custom_filename:
                filename = request.custom_filename
                encoded_filename = quote(filename)
                response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}'
            else:
                # กรณีไม่มีชื่อไฟล์กำหนด ใช้ชื่อทั่วไป
                response['Content-Disposition'] = 'attachment; filename="converted_file.pdf"'

        try:
            os.remove(pdf_path)
            os.remove(excel_path)
        except:
            pass

        return response

    except Exception as e:
        print("⚠️ ERROR:", e)
        print(traceback.format_exc())  # แสดง stack trace เพื่อดีบัก

        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            if os.path.exists(excel_path):
                os.remove(excel_path)
        except:
            pass

        return HttpResponse(f"เกิดข้อผิดพลาดในการแปลงไฟล์: {str(e)}", status=500)