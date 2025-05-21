from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from myapp.models import Person, WorkDay, QueueRate
import calendar
import json
from datetime import datetime, date
from myapp.access_control import role_required, admin_required
from myapp.utils import log_activity

@login_required
@admin_required
def com_calc_view(request):
    # บันทึกการเข้าใช้งานระบบคำนวณหัวคิว
    log_activity(request, 'calc', 'เข้าหน้าคำนวณหัวคิว')
    
    selected_month = request.GET.get('month')

    if not selected_month:
        selected_month = datetime.today().strftime('%Y-%m')

    year, month = map(int, selected_month.split('-'))
    num_days = calendar.monthrange(year, month)[1]
    days_in_month = list(range(1, num_days + 1))
    month_start_date = date(year, month, 1)
    
    # ใช้การเตรียมข้อมูลแบบง่าย ไม่มีการเลือกคนขับคนเดียว
    days_data = []
    
    for day in days_in_month:
        # เตรียมข้อมูลเบื้องต้นสำหรับแต่ละวัน
        day_info = {
            'day': day,
            'raw': '',
            'money': ''
        }
        
        # หาผลรวมของหัวคิวจากคนขับทุกคนในวันนั้น
        day_date = date(year, month, day)
        day_records = WorkDay.objects.filter(date=day_date)
        
        # เฉพาะคนที่มาทำงาน
        working_records = day_records.filter(status=1)

        total_day_queue = 0
        total_day_money = 0

        for record in working_records:
            total_day_queue = record.queue_count  # queue_count เป็นค่ารวมอยู่แล้ว ใช้ค่าเดียวพอ
            total_day_money = record.pay          # pay เป็นค่าที่ถูกตั้งไว้ต่อคน ใช้ค่าเดียวพอ
            break  # เอา record แรกพอ เพราะทุกคนจะได้ค่าเดียวกันอยู่แล้ว

        if working_records.exists():
            day_info['raw'] = total_day_queue
            day_info['money'] = total_day_money

        days_data.append(day_info)

    # ถ้ามีการส่งฟอร์มบันทึกข้อมูลหัวคิว
    if request.method == "POST" and request.POST.get("action") == "save":
        # บันทึกการบันทึกข้อมูลหัวคิว
        log_activity(request, 'calc', 'บันทึกข้อมูลหัวคิว', 
                    f'บันทึกข้อมูลเดือน: {selected_month}')
        
        for day in days_in_month:
            queue_count = int(request.POST.get(f"raw_queue_{day}") or 0)
            day_date = date(year, month, day)

            # หาเงื่อนไขที่ตรงกับ queue_count
            matched_rule = QueueRate.objects.filter(
                month=month_start_date,
                min_queue__lte=queue_count,
                max_queue__gte=queue_count
            ).first()

            pay_value = matched_rule.pay_per_queue if matched_rule else 0

            # คนที่มาทำงานในวันนั้น (status = 1)
            day_records = WorkDay.objects.filter(date=day_date, status=1)

            for record in day_records:
                # เก็บค่าเดิมไว้ตรวจสอบการเปลี่ยนแปลง
                old_queue = record.queue_count
                old_pay = record.pay
                
                record.queue_count = queue_count  # ใส่ queue ทั้งวันให้ทุกคน
                record.pay = pay_value
                record.save()
                
                # บันทึกการเปลี่ยนแปลงหัวคิวสำหรับแต่ละคน
                if old_queue != queue_count or old_pay != pay_value:
                    log_detail = f'พนักงาน: {record.person.first_name} {record.person.last_name}, ' \
                                f'วันที่: {day_date}, ' \
                                f'หัวคิว: {old_queue} -> {queue_count}, ' \
                                f'เงิน: {old_pay} -> {pay_value}'
                    log_activity(request, 'calc', 'อัพเดตข้อมูลหัวคิว', log_detail, record)

        messages.success(request, "บันทึกข้อมูลหัวคิวเรียบร้อยแล้ว")
        return redirect(f'/com_calc/?month={selected_month}')


    # คำนวณยอดรวมทั้งเดือน
    total_queues = sum(day['raw'] or 0 for day in days_data)
    total_money = sum(day['money'] or 0 for day in days_data)

    month_name_th = [
        "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]

    context = {
        'selected_month': selected_month,
        'days_in_month': days_in_month,
        'month_display': f"{month_name_th[month]} {year}",
        'days_data': days_data,
        'total_queues': total_queues,
        'total_money': total_money
    }

    return render(request, 'com_calc.html', context)

# ฟังก์ชันอื่นๆ คงเดิม
@login_required
def save_queue_conditions(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            rules = data.get('rules', [])
            month_str = data.get('month')
            
            # บันทึกการบันทึกเงื่อนไขหัวคิว
            log_activity(request, 'calc', 'บันทึกเงื่อนไขหัวคิว', 
                         f'บันทึกเงื่อนไขเดือน: {month_str}, จำนวนกฎ: {len(rules)}')
            
            if not month_str or not rules:
                return JsonResponse({'success': False, 'message': 'ข้อมูลไม่ครบ'})

            # แปลงรูปแบบเดือนให้ถูกต้อง
            try:
                year, month = map(int, month_str.split('-'))
                month_date = date(year, month, 1)
            except ValueError:
                return JsonResponse({'success': False, 'message': 'รูปแบบเดือนไม่ถูกต้อง'})

            # ลบเงื่อนไขเก่า
            deleted_count = QueueRate.objects.filter(month=month_date).count()
            QueueRate.objects.filter(month=month_date).delete()
            log_activity(request, 'calc', 'ลบเงื่อนไขหัวคิวเดิม', 
                         f'ลบเงื่อนไขเดือน: {month_str}, จำนวนที่ลบ: {deleted_count}')

            # บันทึกเงื่อนไขใหม่
            for rule in rules:
                queue_rate = QueueRate.objects.create(
                    month=month_date,
                    min_queue=rule['min'],
                    max_queue=rule['max'],
                    pay_per_queue=rule['price']
                )
                log_activity(request, 'calc', 'เพิ่มเงื่อนไขหัวคิว', 
                             f'เดือน: {month_str}, Min: {rule["min"]}, Max: {rule["max"]}, ราคา: {rule["price"]}',
                             queue_rate)

            return JsonResponse({'success': True, 'message': 'บันทึกสำเร็จ'})
        except Exception as e:
            log_activity(request, 'calc', 'ข้อผิดพลาดในการบันทึกเงื่อนไขหัวคิว', str(e))
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'})

@login_required
def load_queue_conditions(request):
    selected_month_str = request.GET.get('month')
    if not selected_month_str:
        return JsonResponse({'success': False, 'message': 'ไม่ได้ระบุเดือน'})

    try:
        year, month = map(int, selected_month_str.split('-'))
        selected_date = date(year, month, 1)

        current_conditions = QueueRate.objects.filter(month=selected_date).order_by('min_queue')

        rules = [{
            'min': q.min_queue,
            'max': q.max_queue,
            'price': float(q.pay_per_queue)
        } for q in current_conditions]

        # ไม่จำเป็นต้องบันทึก log สำหรับการโหลดข้อมูลที่ไม่ได้เปลี่ยนแปลงอะไร

        return JsonResponse({'success': True, 'rules': rules})

    except Exception as e:
        log_activity(request, 'calc', 'ข้อผิดพลาดในการโหลดเงื่อนไขหัวคิว', str(e))
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def load_prev_queue_conditions(request):
    selected_month_str = request.GET.get('month')
    if not selected_month_str:
        return JsonResponse({'success': False, 'message': 'ไม่ได้ระบุเดือน'})

    try:
        year, month = map(int, selected_month_str.split('-'))
        
        # หาเดือนก่อนหน้า
        prev_month = month - 1
        prev_year = year
        if prev_month < 1:
            prev_month = 12
            prev_year -= 1

        prev_month_date = date(prev_year, prev_month, 1)

        prev_conditions = QueueRate.objects.filter(
            month=prev_month_date
        ).order_by('min_queue')

        if not prev_conditions.exists():
            return JsonResponse({'success': False, 'message': 'ไม่พบเงื่อนไขของเดือนก่อน'})

        rules = [{
            'min': q.min_queue,
            'max': q.max_queue,
            'price': float(q.pay_per_queue)
        } for q in prev_conditions]

        # บันทึกการโหลดข้อมูลจากเดือนก่อน
        log_activity(request, 'calc', 'โหลดเงื่อนไขหัวคิวจากเดือนก่อน', 
                    f'โหลดจากเดือน: {prev_year}-{prev_month:02d} สำหรับเดือน: {selected_month_str}')

        return JsonResponse({
            'success': True, 
            'rules': rules,
            'month': f"{prev_year}-{prev_month:02d}"  # เพิ่มข้อมูลเดือนที่โหลดมา
        })

    except Exception as e:
        log_activity(request, 'calc', 'ข้อผิดพลาดในการโหลดเงื่อนไขหัวคิวจากเดือนก่อน', str(e))
        return JsonResponse({'success': False, 'message': str(e)})
    
@login_required
def delete_all_queue_conditions(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            month_str = data.get('month')
            
            # บันทึกการลบเงื่อนไขหัวคิว
            log_activity(request, 'calc', 'ลบเงื่อนไขหัวคิวทั้งหมด', f'ลบเงื่อนไขเดือน: {month_str}')
            
            if not month_str:
                return JsonResponse({'success': False, 'message': 'ไม่ได้ระบุเดือน'})

            year, month = map(int, month_str.split('-'))
            month_date = date(year, month, 1)

            # ลบเงื่อนไขทั้งหมดของเดือนนั้น
            deleted_count = QueueRate.objects.filter(month=month_date).delete()[0]
            
            # บันทึกผลการลบข้อมูล
            log_activity(request, 'calc', 'ลบเงื่อนไขหัวคิวทั้งหมดสำเร็จ', 
                        f'เดือน: {month_str}, จำนวนที่ลบ: {deleted_count}')
            
            return JsonResponse({
                'success': True,
                'message': f'ลบเงื่อนไขทั้งหมด {deleted_count} รายการเรียบร้อย'
            })
        except Exception as e:
            log_activity(request, 'calc', 'ข้อผิดพลาดในการลบเงื่อนไขหัวคิวทั้งหมด', str(e))
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Method not allowed'})