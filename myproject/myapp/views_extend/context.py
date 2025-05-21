from datetime import datetime

def thai_date_processor(request):
    """
    เพิ่มฟังก์ชันแปลงวันที่เป็นภาษาไทยให้กับ template
    """
    def format_thai_date(date_obj=None, include_year=True, include_time=False):
        """
        แปลงวันที่เป็นรูปแบบไทย เช่น "1 มกราคม 2566"
        
        Args:
            date_obj: วันที่ที่ต้องการแปลง (datetime หรือ date object)
            include_year: แสดงปี พ.ศ. หรือไม่
            include_time: แสดงเวลาหรือไม่
            
        Returns:
            str: วันที่ในรูปแบบไทย
        """
        if date_obj is None:
            date_obj = datetime.now()
            
        # ชื่อเดือนภาษาไทย
        thai_months = [
            "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
            "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
        ]
        
        day = date_obj.day
        month = thai_months[date_obj.month - 1]
        
        if include_year:
            # แปลงเป็น พ.ศ.
            year = date_obj.year + 543
            date_str = f"{day} {month} {year}"
        else:
            date_str = f"{day} {month}"
            
        if include_time:
            time_str = date_obj.strftime("%H:%M:%S")
            date_str = f"{date_str} {time_str} น."
            
        return date_str
    
    return {
        'format_thai_date': format_thai_date,
    }