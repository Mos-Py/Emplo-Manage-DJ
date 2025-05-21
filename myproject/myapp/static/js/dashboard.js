document.addEventListener('DOMContentLoaded', function() {
    // ชื่อเดือนภาษาไทย
    const thaiMonths = [
        "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ];

    // ชื่อเดือนภาษาอังกฤษ
    const englishMonths = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"
    ];

    /**
     * แปลงวันที่จากภาษาอังกฤษเป็นภาษาไทย
     * ตัวอย่าง: "15 May 2023" -> "15 พฤษภาคม 2566"
     */
        function convertDateToThai() {
            // หาทุก element ที่มีวันที่และแปลงเป็นไทย
            document.querySelectorAll('.info-value, .stat-meta, .stat-value small').forEach(function(elem) {
                const text = elem.innerHTML;
                
                // ตรวจสอบว่ามีรูปแบบวันที่หรือไม่ (เช่น "15 May 2023")
                const dateRegex = /(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})/i;
                const match = text.match(dateRegex);
                
                if (match) {
                    const day = match[1];
                    const monthIndex = englishMonths.indexOf(match[2].toLowerCase());
                    const year = parseInt(match[3]) + 543; // แปลงเป็นพ.ศ.
                    
                    if (monthIndex !== -1) {
                        const thaiDate = day + " " + thaiMonths[monthIndex] + " พ.ศ. " + year; // เพิ่ม "พ.ศ." ตรงนี้
                        // แทนที่วันที่ภาษาอังกฤษด้วยภาษาไทย
                        elem.innerHTML = text.replace(match[0], thaiDate);
                    }
                }
            });
        }

    /**
     * จัดรูปแบบตัวเลขเป็นรูปแบบไทย เช่น 1,000.00 บาท
     */
    function formatNumbers() {
        document.querySelectorAll('.stat-value, .info-value').forEach(function(elem) {
            const text = elem.innerHTML;
            
            // ค้นหาตัวเลขที่มีทศนิยม 2 ตำแหน่ง ตามด้วยคำว่า "บาท"
            const numberRegex = /(\d+\.\d{2})\s*บาท/;
            const match = text.match(numberRegex);
            
            if (match) {
                const number = parseFloat(match[1]);
                // จัดรูปแบบตัวเลขให้มีคอมม่าคั่น
                const formattedNumber = number.toLocaleString('th-TH', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
                
                // แทนที่ตัวเลขด้วยรูปแบบใหม่
                elem.innerHTML = text.replace(match[0], formattedNumber + " บาท");
            }
        });
    }

    /**
     * เพิ่มเอฟเฟคเมื่อนำเมาส์เหนือเมนูปุ่ม
     */
    function addMenuButtonEffects() {
        document.querySelectorAll('.menu-btn').forEach(function(btn) {
            // เพิ่มเอฟเฟคเมื่อเลื่อนเมาส์เหนือปุ่ม
            btn.addEventListener('mouseenter', function() {
                const icon = this.querySelector('i');
                if (icon) {
                    icon.style.transition = 'transform 0.3s ease';
                    icon.style.transform = 'scale(1.2)';
                }
                this.style.backgroundColor = '#f0f0f0';
            });
            
            // คืนค่าเมื่อเลื่อนเมาส์ออกจากปุ่ม
            btn.addEventListener('mouseleave', function() {
                const icon = this.querySelector('i');
                if (icon) {
                    icon.style.transform = 'scale(1)';
                }
                this.style.backgroundColor = '';
            });
        });
    }

    /**
     * เพิ่มเอฟเฟคเมื่อนำเมาส์เหนือการ์ดสถิติ
     */
    function addStatCardEffects() {
        document.querySelectorAll('.dashboard-card').forEach(function(card) {
            card.addEventListener('mouseenter', function() {
                const icon = this.querySelector('.stat-icon');
                if (icon) {
                    icon.style.transition = 'transform 0.3s ease';
                    icon.style.transform = 'translateY(-5px)';
                }
            });
            
            card.addEventListener('mouseleave', function() {
                const icon = this.querySelector('.stat-icon');
                if (icon) {
                    icon.style.transform = 'translateY(0)';
                }
            });
        });
    }

    // เรียกใช้ฟังก์ชันทั้งหมด
    convertDateToThai();
    formatNumbers();
    addMenuButtonEffects();
    addStatCardEffects();
});

// เพิ่มฟังก์ชัน JavaScript สำหรับ debug
document.addEventListener('DOMContentLoaded', function() {
    console.log("Dashboard loaded");
    
    // พยายามดึงค่าวันทำงาน
    const workdaysElement = document.querySelector('.stat-value');
    if (workdaysElement) {
        console.log("Found workdays element:", workdaysElement.textContent);
    } else {
        console.log("Cannot find workdays element");
    }
    
    // ลอง log ค่าที่ render จาก Python
    console.log("Workdays debug info:", document.querySelector('.stat-card div[style]')?.textContent);
});