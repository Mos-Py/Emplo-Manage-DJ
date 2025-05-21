import calendar, json
from datetime import datetime, date
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from myapp.models import Person, WorkDay
from django.contrib.auth.decorators import login_required
from myapp.access_control import role_required, admin_required
from myapp.utils import log_activity

@login_required
@admin_required
def check_view(request):
    # บันทึกการเข้าใช้งานระบบเช็คชื่อ
    log_activity(request, 'checkin', 'เข้าหน้าเช็คชื่อ')
    
    selected_month = request.GET.get("month", datetime.today().strftime("%Y-%m"))
    year, month = map(int, selected_month.split('-'))
    num_days = calendar.monthrange(year, month)[1]
    days_in_month = [date(year, month, day) for day in range(1, num_days + 1)]

    # วันหยุด: ใช้ WorkDay ที่ status = 0
    # แก้ไขส่วนที่ใช้ distinct('date__day') เป็นวิธีอื่น
    holidays_query = WorkDay.objects.filter(date__year=year, date__month=month, status=0)
    
    # ดึงข้อมูลทั้งหมดและทำการจัดกลุ่มเอง
    holidays_data = {}
    for holiday in holidays_query:
        day = holiday.date.day
        if day not in holidays_data:
            holidays_data[day] = {
                'date__day': day,
                'note': holiday.note
            }
    
    # แปลงเป็นลิสต์
    holidays = list(holidays_data.values())
    holidays_days = [h['date__day'] for h in holidays]

    persons = Person.objects.all()
    work_logs = WorkDay.objects.filter(date__year=year, date__month=month)

    work_log_dict = {}
    for person in persons:
        work_log_dict[person.id] = {'full': [], 'half': [], 'total': 0.0}

    for log in work_logs:
        pid = log.person.id
        day = log.date.day

        if log.status == 0:
            continue  # วันหยุดไม่ต้องนับรวมในสรุป

        if log.full_day:
            work_log_dict[pid]['full'].append(day)
            work_log_dict[pid]['total'] += 1.0
        else:
            work_log_dict[pid]['half'].append(day)
            work_log_dict[pid]['total'] += 0.5

    weekdays_th = {
        0: "อา.",
        1: "จ.",
        2: "อ.",
        3: "พ.",
        4: "พฤ.",
        5: "ศ.",
        6: "ส."
    }

    month_name_th = [
        "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]

    context = {
        "selected_month": selected_month,
        "month_display": f"{month_name_th[month]} {year}",
        "days_in_month": days_in_month,
        "persons": persons,
        "holidays": holidays_days,
        "holidays_data": holidays,
        "weekdays_th": weekdays_th,
        "work_log_dict": work_log_dict,
        "empty_person_data": {"full": [], "half": [], "total": 0},
    }
    return render(request, "check.html", context)


@csrf_exempt
def save_attendance(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            month = data.get('month')
            attendance = data.get('attendance')
            year, month_num = map(int, month.split('-'))
            
            # บันทึกข้อมูลการบันทึกเช็คชื่อ
            log_activity(request, 'checkin', 'บันทึกการเข้างาน', f'บันทึกข้อมูลเดือน: {month}')

            for pid_str, days_data in attendance.items():
                pid = int(pid_str)
                try:
                    person = Person.objects.get(id=pid)

                    for day_data in days_data:
                        date_str = day_data.get('date')
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                        # อัปเดตหรือสร้าง WorkDay ใหม่ (ค่า default คือ status = 1)
                        workday, created = WorkDay.objects.update_or_create(
                            person=person,
                            date=date_obj,
                            defaults={
                                'full_day': day_data.get('full_day', True),
                                'status': day_data.get('status', 1)
                            }
                        )
                        
                        # บันทึก log เพิ่มเติมสำหรับการสร้างหรือแก้ไขข้อมูลแต่ละรายการ
                        action = 'สร้าง' if created else 'แก้ไข'
                        detail = f'{action}ข้อมูลการเข้างานของ {person.first_name} {person.last_name} วันที่ {date_obj}'
                        log_activity(request, 'checkin', f'{action}ข้อมูลการเข้างาน', detail, workday)
                        
                except Person.DoesNotExist:
                    print(f"ไม่พบพนักงานรหัส {pid}")

            return JsonResponse({'status': 'success', 'message': 'บันทึกข้อมูลเรียบร้อยแล้ว'})
        except Exception as e:
            print(f"ข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}")
            # บันทึกข้อผิดพลาด
            log_activity(request, 'checkin', 'ข้อผิดพลาดในการบันทึกข้อมูล', str(e))
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'})

@csrf_exempt
def save_day_off(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            month = data.get("month")
            holidays = data.get("holidays", [])
            
            # บันทึกการบันทึกวันหยุด
            log_activity(request, 'checkin', 'บันทึกวันหยุด', f'บันทึกวันหยุดเดือน: {month}, จำนวน: {len(holidays)}')

            if not month:
                return JsonResponse({"status": "error", "message": "ไม่มีเดือนที่ระบุ"}, status=400)

            year, month_num = map(int, month.split('-'))

            # ลบวันหยุดเดิม
            WorkDay.objects.filter(date__year=year, date__month=month_num, status=0).delete()

            for holiday in holidays:
                date_str = holiday.get("date")
                note = holiday.get("note", "วันหยุด")
                
                try:
                    holiday_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                    for person in Person.objects.all():
                        workday, created = WorkDay.objects.update_or_create(
                            person=person,
                            date=holiday_date,
                            defaults={
                                'full_day': False,
                                'status': 0,
                                'note': note
                            }
                        )
                        
                        # บันทึก log สำหรับการกำหนดวันหยุดแต่ละวัน
                        log_activity(request, 'checkin', 'กำหนดวันหยุด', 
                                     f'กำหนดวันหยุด: {holiday_date} สำหรับ {person.first_name} {person.last_name} หมายเหตุ: {note}',
                                     workday)
                except Exception as e:
                    print(f"ข้อผิดพลาดในการประมวลผลวันที่ {date_str}: {str(e)}")
                    log_activity(request, 'checkin', 'ข้อผิดพลาดในการกำหนดวันหยุด', f'วันที่ {date_str}: {str(e)}')

            return JsonResponse({"status": "success", "message": "บันทึกวันหยุดเรียบร้อยแล้ว"})
        except Exception as e:
            print(f"ข้อผิดพลาดในการบันทึกวันหยุด: {str(e)}")
            log_activity(request, 'checkin', 'ข้อผิดพลาดในการบันทึกวันหยุด', str(e))
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)