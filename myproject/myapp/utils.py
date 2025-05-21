def log_activity(request, system, action, details='', related_object=None):
    """
    บันทึกกิจกรรมการใช้งานระบบ
    
    Args:
        request: HTTP request object
        system: ระบบที่ใช้งาน (dashboard, checkin, withdraw, ฯลฯ)
        action: การกระทำที่ผู้ใช้ทำ
        details: รายละเอียดเพิ่มเติม
        related_object: วัตถุที่เกี่ยวข้อง (เช่น WorkDay, Fee, ฯลฯ)
    """
    from myapp.models import ActivityLog
    
    if not request.user.is_authenticated:
        return
    
    # ดึง IP ผู้ใช้
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ',' in ip:  # ในกรณีที่มี proxy หลายตัว
        ip = ip.split(',')[0].strip()
    
    # ข้อมูลวัตถุที่เกี่ยวข้อง (ถ้ามี)
    related_object_id = None
    related_object_type = ''
    if related_object:
        related_object_id = related_object.id
        related_object_type = related_object.__class__.__name__
    
    # บันทึกข้อมูล
    ActivityLog.objects.create(
        user=request.user,
        system=system,
        action=action,
        details=details,
        ip_address=ip,
        related_object_id=related_object_id,
        related_object_type=related_object_type
    )