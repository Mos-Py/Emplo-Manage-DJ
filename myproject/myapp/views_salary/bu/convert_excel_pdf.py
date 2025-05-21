import os
import tempfile
from django.http import FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import win32com.client
from pathlib import Path
import traceback

@csrf_exempt
def convert_excel_to_pdf(request):
    """API endpoint สำหรับแปลงไฟล์ Excel เป็น PDF"""
    if request.method != 'POST' or 'excel_file' not in request.FILES:
        return HttpResponse("ต้องส่งไฟล์ Excel มาด้วย", status=400)
    
    # รับไฟล์ Excel จาก request
    excel_file = request.FILES['excel_file']
    
    # สร้างไฟล์ชั่วคราวสำหรับเก็บไฟล์ Excel
    temp_dir = tempfile.gettempdir()
    excel_path = os.path.join(temp_dir, f"temp_excel_{os.getpid()}.xlsx")
    
    with open(excel_path, 'wb') as f:
        for chunk in excel_file.chunks():
            f.write(chunk)
    
    # สร้างไฟล์ชั่วคราวสำหรับเก็บไฟล์ PDF
    pdf_path = excel_path.replace(".xlsx", ".pdf")
    
    try:
        # ใช้ Microsoft Excel เพื่อแปลงไฟล์เป็น PDF
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        
        # เปิดไฟล์ Excel
        wb = excel.Workbooks.Open(excel_path)
        
        # ทำการแปลงเป็น PDF
        wb.ExportAsFixedFormat(0, pdf_path)
        
        # ปิดไฟล์
        wb.Close(False)
        excel.Quit()
        
        # ตรวจสอบว่าไฟล์ PDF ถูกสร้างขึ้นมาหรือไม่
        if not os.path.exists(pdf_path):
            return HttpResponse("ไม่สามารถสร้างไฟล์ PDF ได้", status=500)
        
        # ส่งไฟล์ PDF กลับไปยังผู้ใช้
        with open(pdf_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename=salary_export.pdf'
        
        # ลบไฟล์ชั่วคราว
        try:
            os.remove(pdf_path)
            os.remove(excel_path)
        except:
            pass
            
        return response
        
    except Exception as e:
        # แสดงข้อผิดพลาดแบบละเอียดเพื่อการแก้ไข
        error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        
        # ลบไฟล์ชั่วคราวในกรณีที่เกิดข้อผิดพลาด
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            if os.path.exists(excel_path):
                os.remove(excel_path)
        except:
            pass
            
        return HttpResponse(f"เกิดข้อผิดพลาดในการแปลงไฟล์: {str(e)}", status=500)