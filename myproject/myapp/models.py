from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import JSONField 
from decimal import Decimal
import string
import random

# กำหนด Choices ในระดับโมดูล
SYSTEM_CHOICES = [
    ('dashboard', 'แดชบอร์ด'),
    ('checkin', 'เช็คชื่อพนักงาน'),
    ('withdraw', 'เบิกเงิน'),
    ('loan', 'กู้เงิน'),
    ('calc', 'คำนวณหัวคิว'),
    ('salary', 'เงินเดือน'),
    ('employee', 'จัดการพนักงาน'),
    ('password', 'จัดการรหัสผ่าน'),
    ('notification', 'การแจ้งเตือน'),
]

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    gender = models.CharField(max_length=1, choices=[('M', 'ชาย'), ('F', 'หญิง'), ('O', 'อื่นๆ')])
    title = models.CharField(max_length=10, choices=[('Mr', 'นาย'), ('Mrs', 'นาง'), ('Ms', 'นางสาว')])
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    id_card_number = models.CharField(max_length=13, blank=True, verbose_name="เลขบัตรประชาชน")
    nationality = models.CharField(max_length=50, default="ไทย", verbose_name="สัญชาติ")
    address = models.TextField(blank=True, verbose_name="ที่อยู่")
    phone_number = models.CharField(max_length=15, blank=True, verbose_name="เบอร์โทรศัพท์")
    
    ROLE_CHOICES = [
        ('Employee', 'พนักงานทั่วไป'),
        ('Accountant', 'พนักงานบัญชี'),
        ('Concrete Mixer Driver', 'คนขับรถโม่'),
        ('Production staff', 'พนักงานฝ่ายผลิต'),
        ('Plant Operator', 'คนดูแลแพ้นท์'),
        ('Leader Employee', 'หัวหน้าพนักงาน')
    ]
    Role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    concrete_mixer_numbers = models.CharField(max_length=100, blank=True, verbose_name="เลขประจำรถโม่")
    salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ค่าจ้างต่อวัน")
    status = models.IntegerField(default=1, choices=[(0, 'ไม่ได้ทำงาน'), (1, 'ทำงาน')])  

    def __str__(self):
        return f"{self.title} {self.first_name} {self.last_name}"
    
    def get_thai_title(self):
        """รับคำนำหน้าชื่อเป็นภาษาไทย"""
        title_mapping = {
            'Mr': 'นาย',
            'Mrs': 'นาง',
            'Ms': 'นางสาว'
        }
        return title_mapping.get(self.title, self.title)
    
    def get_thai_role(self):
        """รับชื่อตำแหน่งเป็นภาษาไทย"""
        for role_code, role_name in self.ROLE_CHOICES:
            if self.Role == role_code:
                return role_name
        return self.Role
    
    def get_status_display_thai(self):
        """รับสถานะการทำงานเป็นภาษาไทย"""
        return "ทำงาน" if self.status == 1 else "ไม่ได้ทำงาน"
        
    def get_monthly_salary(self):
        """รับเงินเดือนล่าสุดจาก SalaryRecord"""
        from django.utils import timezone
        latest_salary = self.salaryrecord_set.order_by('-month').first()
        if latest_salary:
            return latest_salary.total
        return None
    
    def get_thai_gender(self):
        """รับเพศเป็นภาษาไทย"""
        gender_mapping = {
            'M': 'ชาย',
            'F': 'หญิง',
            'O': 'อื่นๆ'
        }
        return gender_mapping.get(self.gender, self.gender)
    
    def get_age(self):
        """รับอายุ"""
        if self.date_of_birth:
            today = timezone.now().date()
            age = today.year - self.date_of_birth.year
            if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
                age -= 1
            return age
        return None
    
    def has_pending_password_reset(self):
        """ตรวจสอบว่ามีคำขอรีเซตรหัสผ่านที่รออนุมัติหรือไม่"""
        if not self.user:
            return False
        import json
        try:
            if self.user.first_name.startswith('{'):
                reset_data = json.loads(self.user.first_name)
                return reset_data.get('status') == 'pending'
        except:
            pass
        return False

class WorkDay(models.Model):
    date = models.DateField(db_index=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    full_day = models.BooleanField(default=True)  # True = เต็มวัน, False = ครึ่งวัน
    queue_count = models.PositiveIntegerField(default=0)
    pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.IntegerField(default=1)  # 1 = ทำงาน, 0 = หยุด
    note = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ("date", "person")
        ordering = ["date"]
        indexes = [
            models.Index(fields=['person', 'date']),
        ]

    def __str__(self):
        return f"{self.person} - {self.date}" 

class QueueRate(models.Model):
    month = models.DateField()
    min_queue = models.PositiveIntegerField()
    max_queue = models.PositiveIntegerField()
    pay_per_queue = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ['month', 'min_queue']

    def __str__(self):
        return f"{self.month.strftime('%Y-%m')}: {self.min_queue}-{self.max_queue} = {self.pay_per_queue} บาท/คิว"

class Fee(models.Model):
    STATUS_CHOICES = [
        (0, 'เบิกเงิน'),
        (1, 'กู้เงิน'),
    ]
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='fees')
    fee_status = models.IntegerField(choices=STATUS_CHOICES)  # 0 = เบิกเงิน, 1 = กู้เงิน
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    recorded_by = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='recorded_fees')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    @property
    def remaining(self):
        # ถ้าเป็นเบิกเงิน ไม่มียอดคงเหลือ
        if self.fee_status == 0:
            return 0
            
        # ถ้าเป็นกู้เงิน ให้หาผลรวมการจ่ายคืน
        payments = Fee.objects.filter(
            person=self.person,
            fee_status=1, # กู้เงิน
            amount__lt=0, # จำนวนเงินติดลบ = การจ่ายคืน
            date__gte=self.date # การจ่ายคืนต้องเกิดหลังจากวันที่กู้
        )
        total_paid = abs(sum(payment.amount for payment in payments))
        
        # ยอดคงเหลือ = ยอดกู้ - ยอดจ่ายคืนทั้งหมด
        return max(self.amount - total_paid, 0)
    
    def __str__(self):
        if self.fee_status == 0:  # เบิกเงิน
            return f"{self.person} เบิก {self.amount} บาท - {self.date}"
        else:  # กู้เงิน
            return f"{self.person} กู้ {self.amount} บาท เหลือ {self.remaining} บาท - {self.date}"

class SalaryRecord(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    month = models.DateField()
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    withdraw = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ss_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    loan_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    extra_items = JSONField(default=list, blank=True)
    extra_expenses = models.JSONField(default=list, blank=True)
    recorded_by = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='recorded_salaries')
    
    class Meta:
        unique_together = ('person', 'month')
        ordering = ['-month']

    def __str__(self):
        return f"{self.person} - เงินเดือน {self.month.strftime('%B %Y')} = {self.total} บาท"

class Company(models.Model):
    C_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(max_length=100)

    def __str__(self):
        return self.C_name

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activities')
    system = models.CharField(max_length=20, choices=SYSTEM_CHOICES)
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)  # ID ของวัตถุที่เกี่ยวข้อง (ถ้ามี)
    related_object_type = models.CharField(max_length=50, blank=True)  # ชื่อโมเดลของวัตถุที่เกี่ยวข้อง
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
    
    def __str__(self):
        username = self.user.username if self.user else 'Unknown'
        return f"{username} - {self.action} ({self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
<<<<<<< HEAD
=======
    
    @classmethod
    def get_unread_count_for_superuser(cls):
        """นับจำนวน log ที่สำคัญสำหรับ superuser"""
        from datetime import timedelta
        
        yesterday = timezone.now() - timedelta(days=1)
        return cls.objects.filter(
            created_at__gte=yesterday,
            system__in=['password', 'employee', 'salary']
        ).count()

# =============================================================================
# UTILITY FUNCTIONS สำหรับระบบรหัสผ่าน
# =============================================================================

def generate_temp_password():
    """สร้างรหัสผ่านชั่วคราว 6 หลัก"""
    return ''.join(random.choices(string.digits, k=6))

def create_password_reset_request(username, note=""):
    """สร้างคำขอรีเซตรหัสผ่าน"""
    try:
        user = User.objects.get(username=username)
        
        # เก็บข้อมูลในฟิลด์ last_login ชั่วคราว (ใช้ JSON format)
        import json
        from datetime import datetime, timedelta
        
        reset_data = {
            'status': 'pending',
            'requested_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=3)).isoformat(),
            'note': note
        }
        
        # บันทึกข้อมูลใน first_name field ของ User ชั่วคราว
        user.first_name = json.dumps(reset_data)
        user.save()
        
        return True, "สร้างคำขอสำเร็จ"
    except User.DoesNotExist:
        return False, "ไม่พบผู้ใช้งาน"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาด: {str(e)}"

def get_pending_password_resets():
    """ดึงรายการคำขอรีเซตรหัสผ่านที่รออนุมัติ"""
    import json
    pending_requests = []
    
    users = User.objects.exclude(first_name="")
    for user in users:
        try:
            if user.first_name.startswith('{'):
                reset_data = json.loads(user.first_name)
                if reset_data.get('status') == 'pending':
                    pending_requests.append({
                        'user': user,
                        'data': reset_data
                    })
        except:
            continue
    
    return pending_requests

def approve_password_reset(username, approved_by_user):
    """อนุมัติคำขอรีเซตรหัสผ่าน"""
    import json
    from datetime import datetime, timedelta
    
    try:
        user = User.objects.get(username=username)
        reset_data = json.loads(user.first_name)
        
        if reset_data.get('status') != 'pending':
            return False, "คำขอนี้ไม่สามารถอนุมัติได้"
        
        # สร้างรหัสชั่วคราว
        temp_password = generate_temp_password()
        
        reset_data.update({
            'status': 'approved',
            'temp_password': temp_password,
            'approved_by': approved_by_user.username,
            'approved_at': datetime.now().isoformat()
        })
        
        user.first_name = json.dumps(reset_data)
        user.save()
        
        return True, f"อนุมัติสำเร็จ รหัสชั่วคราว: {temp_password}"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาด: {str(e)}"

def check_temp_password_login(username, temp_password):
    """ตรวจสอบการ login ด้วยรหัสชั่วคราว"""
    import json
    from datetime import datetime
    
    try:
        user = User.objects.get(username=username)
        reset_data = json.loads(user.first_name)
        
        if (reset_data.get('status') == 'approved' and 
            reset_data.get('temp_password') == temp_password):
            
            # เปลี่ยนสถานะเป็น used
            reset_data['status'] = 'used'
            reset_data['used_at'] = datetime.now().isoformat()
            user.first_name = json.dumps(reset_data)
            user.save()
            
            return True, user, reset_data.get('temp_password')
        
        return False, None, None
    except:
        return False, None, None

def count_pending_notifications():
    """นับจำนวนการแจ้งเตือนที่รออนุมัติ"""
    pending_count = len(get_pending_password_resets())
    
    # นับ activity log ที่สำคัญใน 24 ชั่วโมงที่ผ่านมา
    from datetime import timedelta
    yesterday = timezone.now() - timedelta(days=1)
    activity_count = ActivityLog.objects.filter(
        created_at__gte=yesterday,
        system__in=['password', 'employee', 'salary']
    ).count()
    
    return pending_count + activity_count

def reject_password_reset(username, rejected_by_user, reason=""):
    """ปฏิเสธคำขอรีเซตรหัสผ่าน"""
    import json
    from datetime import datetime
    
    try:
        user = User.objects.get(username=username)
        reset_data = json.loads(user.first_name)
        
        if reset_data.get('status') != 'pending':
            return False, "คำขอนี้ไม่สามารถปฏิเสธได้"
        
        reset_data.update({
            'status': 'rejected',
            'rejected_by': rejected_by_user.username,
            'rejected_at': datetime.now().isoformat(),
            'rejection_reason': reason
        })
        
        user.first_name = json.dumps(reset_data)
        user.save()
        
        return True, "ปฏิเสธคำขอสำเร็จ"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาด: {str(e)}"

def clear_password_reset_data(username):
    """ล้างข้อมูลคำขอรีเซตรหัสผ่าน"""
    try:
        user = User.objects.get(username=username)
        user.first_name = ""
        user.save()
        return True, "ล้างข้อมูลสำเร็จ"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาด: {str(e)}"
>>>>>>> ba71a2b (เพิ่มเปลี่ยนกับลืมรหัสและเพิ่มwidgetให้super user)
