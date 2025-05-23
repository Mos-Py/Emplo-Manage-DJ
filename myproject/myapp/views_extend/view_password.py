from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from myapp.utils import log_activity
from myapp.models import (
    create_password_reset_request, 
    get_pending_password_resets,
    approve_password_reset,
    reject_password_reset,
    count_pending_notifications,
    generate_temp_password
)
import json

def is_superuser(user):
    return user.is_superuser

# =============================================================================
# ระบบเปลี่ยนรหัสผ่าน
# =============================================================================

@login_required
def change_password_view(request):
    """หน้าเปลี่ยนรหัสผ่าน"""
    
    # ตรวจสอบว่า superuser กำลังเปลี่ยนรหัสให้คนอื่นหรือไม่
    target_user = request.user  # default เป็นตัวเอง
    
    # ถ้ามี parameter person_id และเป็น superuser
    if request.user.is_superuser and 'person_id' in request.GET:
        try:
            from myapp.models import Person
            person = Person.objects.get(id=request.GET['person_id'])
            if person.user:
                target_user = person.user
        except Person.DoesNotExist:
            messages.error(request, 'ไม่พบข้อมูลพนักงาน')
            return redirect('dashboard')
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # ตรวจสอบรหัสผ่านเดิม
        if not target_user.check_password(current_password):
            messages.error(request, 'รหัสผ่านเดิมไม่ถูกต้อง')
            log_activity(request, 'password', 'เปลี่ยนรหัสผ่านไม่สำเร็จ', f'รหัสผ่านเดิมไม่ถูกต้อง - Target: {target_user.username}')
            return render(request, 'password/change_password.html', {
                'target_user': target_user
            })
        
        # ตรวจสอบรหัสผ่านใหม่
        if new_password != confirm_password:
            messages.error(request, 'รหัสผ่านใหม่ไม่ตรงกัน')
            return render(request, 'password/change_password.html', {
                'target_user': target_user
            })
        
        if len(new_password) < 6:
            messages.error(request, 'รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร')
            return render(request, 'password/change_password.html', {
                'target_user': target_user
            })
        
        # เปลี่ยนรหัสผ่าน
        target_user.set_password(new_password)
        target_user.save()
        
        # ถ้าเปลี่ยนรหัสตัวเอง ต้องอัพเดท session
        if target_user == request.user:
            update_session_auth_hash(request, target_user)
        
        # ข้อความสำเร็จ
        if target_user == request.user:
            success_msg = 'เปลี่ยนรหัสผ่านสำเร็จ'
        else:
            success_msg = f'เปลี่ยนรหัสผ่านของ {target_user.username} สำเร็จ'
        
        messages.success(request, success_msg)
        log_activity(request, 'password', 'เปลี่ยนรหัสผ่านสำเร็จ', f'Target: {target_user.username}')
        
        return redirect('change_password')
    
    return render(request, 'password/change_password.html', {
        'target_user': target_user
    })

# =============================================================================
# ระบบลืมรหัสผ่าน (ใหม่)
# =============================================================================

def forgot_password_view(request):
    """หน้าลืมรหัสผ่าน - ขั้นตอนที่ 1"""
    if request.method == 'POST':
        username = request.POST.get('username')
        note = request.POST.get('note', '')
        
        if not username:
            messages.error(request, 'กรุณากรอก Username')
            return render(request, 'password/forgot_password.html')
        
        # สร้างคำขอรีเซตรหัสผ่าน
        success, message = create_password_reset_request(username, note)
        
        if success:
            messages.success(request, f'ส่งคำขอสำเร็จ! กรุณารอ Admin อนุมัติ (Username: {username})')
            log_activity(request, 'password', 'ส่งคำขอรีเซตรหัสผ่าน', f'Username: {username}')
        else:
            messages.error(request, message)
            log_activity(request, 'password', 'ส่งคำขอรีเซตรหัสผ่านไม่สำเร็จ', f'Username: {username}, Error: {message}')
        
        return render(request, 'password/forgot_password.html')
    
    return render(request, 'password/forgot_password.html')

# =============================================================================
# ระบบจัดการคำขอสำหรับ Admin
# =============================================================================

@login_required
@user_passes_test(is_superuser)
def admin_password_requests_view(request):
    """หน้าจัดการคำขอรีเซตรหัสผ่านสำหรับ Admin"""
    pending_requests = get_pending_password_resets()
    
    log_activity(request, 'password', 'เข้าดูคำขอรีเซตรหัสผ่าน', f'จำนวนคำขอ: {len(pending_requests)}')
    
    return render(request, 'password/admin_requests.html', {
        'pending_requests': pending_requests
    })

@csrf_exempt
@login_required
@user_passes_test(is_superuser)
def approve_request_ajax(request):
    """อนุมัติคำขอรีเซตรหัสผ่าน (AJAX) - แก้ให้ส่งรหัสถาวร"""
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        
        # สร้างรหัสผ่านใหม่แทนรหัสชั่วคราว
        success, message = approve_password_reset_permanent(username, request.user)
        
        if success:
            log_activity(request, 'password', 'อนุมัติคำขอรีเซตรหัสผ่าน', f'Username: {username}')
        else:
            log_activity(request, 'password', 'อนุมัติคำขอรีเซตรหัสผ่านไม่สำเร็จ', f'Username: {username}, Error: {message}')
        
        return JsonResponse({
            'success': success,
            'message': message
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@csrf_exempt
@login_required
@user_passes_test(is_superuser)
def reject_request_ajax(request):
    """ปฏิเสธคำขอรีเซตรหัสผ่าน (AJAX)"""
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        reason = data.get('reason', '')
        
        success, message = reject_password_reset(username, request.user, reason)
        
        if success:
            log_activity(request, 'password', 'ปฏิเสธคำขอรีเซตรหัสผ่าน', f'Username: {username}, เหตุผล: {reason}')
        else:
            log_activity(request, 'password', 'ปฏิเสธคำขอรีเซตรหัสผ่านไม่สำเร็จ', f'Username: {username}, Error: {message}')
        
        return JsonResponse({
            'success': success,
            'message': message
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

# =============================================================================
# API สำหรับแจ้งเตือน
# =============================================================================

@login_required
@user_passes_test(is_superuser)
def get_notification_count(request):
    """API ดึงจำนวนการแจ้งเตือน"""
    count = count_pending_notifications()
    return JsonResponse({'count': count})

@login_required
@user_passes_test(is_superuser)
def get_notifications(request):
    """API ดึงรายการการแจ้งเตือน"""
    pending_requests = get_pending_password_resets()
    
    notifications = []
    for req in pending_requests:
        notifications.append({
            'id': req['user'].id,
            'username': req['user'].username,
            'type': 'password_reset',
            'title': 'คำขอรีเซตรหัสผ่าน',
            'message': f'{req["user"].username} ขอรีเซตรหัสผ่าน',
            'created_at': req['data'].get('requested_at', ''),
            'note': req['data'].get('note', '')
        })
    
    return JsonResponse({
        'notifications': notifications,
        'count': len(notifications)
    })

# =============================================================================
# ฟังก์ชันช่วยเหลือ
# =============================================================================

def approve_password_reset_permanent(username, approved_by_user):
    """อนุมัติคำขอรีเซตรหัสผ่าน - ตั้งรหัสถาวรเลย (ไม่ใช่รหัสชั่วคราว)"""
    import json
    from datetime import datetime
    
    try:
        user = User.objects.get(username=username)
        
        # ตรวจสอบว่ามีคำขอรออนุมัติ
        if not user.first_name.startswith('{'):
            return False, "ไม่พบคำขอรีเซตรหัสผ่าน"
            
        reset_data = json.loads(user.first_name)
        
        if reset_data.get('status') != 'pending':
            return False, "คำขอนี้ไม่สามารถอนุมัติได้"
        
        # สร้างรหัสผ่านใหม่
        new_password = generate_temp_password()  # ใช้ฟังก์ชันเดิม แต่จะเป็นรหัสถาวร
        
        # ตั้งรหัสผ่านใหม่ทันที (ไม่ใช่รหัสชั่วคราว)
        user.set_password(new_password)
        
        # ล้างข้อมูล JSON ออกจาก first_name
        user.first_name = ""  # ล้างข้อมูลคำขอ
        user.save()
        
        return True, f"อนุมัติสำเร็จ รหัสผ่านใหม่: {new_password}"
        
    except Exception as e:
        return False, f"เกิดข้อผิดพลาด: {str(e)}"