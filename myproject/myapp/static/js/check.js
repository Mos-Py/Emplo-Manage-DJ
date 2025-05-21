function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function reloadMonth() {
    const month = document.getElementById('month')?.value;
    if (month) {
        window.location.href = `?month=${month}`;
    } else {
        alert("กรุณาเลือกเดือน");
    }
}

function saveAttendance() {
    console.log("กำลังบันทึกข้อมูล...");
    // โหมดแก้ไขต้องอ่านข้อมูลจาก UI โดยตรง
    const data = {};
    const selectedMonth = document.getElementById('month').value;
    
    if (!selectedMonth) {
        alert("กรุณาเลือกเดือนก่อนบันทึกข้อมูล");
        return;
    }
    
    try {
        // ดึงข้อมูลทุกคนและทุกวัน
        const cells = document.querySelectorAll('.attendance-cell:not(.holiday)');
        
        cells.forEach(cell => {
            // ดึงข้อมูล person ID และ day จาก data attributes
            const personId = cell.getAttribute('data-person');
            const day = parseInt(cell.getAttribute('data-day'));
            const date = formatDateString(selectedMonth, day);
            
            if (!personId || isNaN(day)) return;
            
            // ตรวจสอบว่ามีข้อมูลที่มีอยู่แล้วหรือยัง
            if (!data[personId]) {
                data[personId] = [];
            }
            
            // ตรวจสอบค่าในเซลล์
            if (cell.querySelector('.full-day-marker')) {
                data[personId].push({
                    date: date,
                    full_day: true,
                    status: 1
                });
            } else if (cell.querySelector('.half-day-marker')) {
                data[personId].push({
                    date: date,
                    full_day: false,
                    status: 1
                });
            }
            // ถ้าเป็น absent ไม่ต้องเพิ่มข้อมูล (หรือสามารถเพิ่มเป็น status: 0 ก็ได้)
        });

        console.log("ข้อมูลที่จะส่ง:", data);
        const csrftoken = getCookie('csrftoken');

        fetch('/save_attendance/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            },
            body: JSON.stringify({
                month: selectedMonth,
                attendance: data
            }),
        })
        .then(res => {
            console.log("ได้รับการตอบกลับ:", res);
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        })
        .then(data => {
            console.log("ข้อมูลตอบกลับ:", data);
            if (data.status === 'success') {
                alert(data.message || 'บันทึกข้อมูลเรียบร้อยแล้ว');
                // Refresh หน้าใหม่พร้อมเดือนเดิม
                window.location.href = `?month=${selectedMonth}`;
            } else {
                alert('เกิดข้อผิดพลาด: ' + (data.message || 'ไม่สามารถบันทึกข้อมูลได้'));
            }
        })
        .catch(err => {
            console.error("เกิดข้อผิดพลาด:", err);
            alert('ไม่สามารถบันทึกข้อมูลได้: ' + err.message);
        });
    } catch (error) {
        console.error("เกิดข้อผิดพลาดในการประมวลผลข้อมูล:", error);
        alert('เกิดข้อผิดพลาดในการประมวลผลข้อมูล: ' + error.message);
    }
}

/* แปลงวันที่ให้อยู่ในรูปแบบ YYYY-MM-DD */
function formatDateString(monthStr, day) {
    // monthStr มีรูปแบบ YYYY-MM
    return `${monthStr}-${day.toString().padStart(2, '0')}`;
}

/* ฟังก์ชันช่วยหาชื่อวันในสัปดาห์ภาษาไทย */
function getThaiDayName(dateObj) {
    const weekdays_th = ['อาทิตย์', 'จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์'];
    return weekdays_th[dateObj.getDay()];
}

/* ฟอร์แมตวันที่เป็นรูปแบบไทย DD เดือน YYYY */
function formatThaiDateString(dateObj) {
    const months_th = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", 
                      "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"];
    
    const day = dateObj.getDate();
    const month = dateObj.getMonth() + 1;
    const year = dateObj.getFullYear();
    
    return `${day} ${months_th[month]} ${year}`;
}

/* Day off */ 
function addDayOff() {
    const daySelect = document.getElementById('day_off_day');
    const descriptionInput = document.getElementById('day_off_description');
    const dayOffList = document.getElementById('day_off_list');
    const selectedMonth = document.getElementById('month')?.value;

    if (!daySelect.value) {
        alert('กรุณาเลือกวันที่');
        return;
    }
    
    if (!selectedMonth) {
        alert('กรุณาเลือกเดือนก่อน');
        return;
    }

    const existingItem = dayOffList.querySelector(`li[data-day="${daySelect.value}"]`);
    if (existingItem) {
        alert('วันที่นี้ถูกเพิ่มไว้แล้ว');
        return;
    }
    
    // สร้างวัตถุวันที่เพื่อหาชื่อวันในสัปดาห์
    const [year, month] = selectedMonth.split('-').map(Number);
    const selectedDate = new Date(year, month - 1, parseInt(daySelect.value));
    const dayName = getThaiDayName(selectedDate);
    const formattedDate = formatThaiDateString(selectedDate);

    const listItem = document.createElement('li');
    listItem.className = 'list-group-item d-flex justify-content-between align-items-center py-1 px-2';
    listItem.dataset.day = daySelect.value;
    listItem.innerHTML = `
        <div>
            <span class="day-description">วันที่ ${daySelect.value}: <strong>${formattedDate}</strong> (วัน${dayName})</span>
            <p class="mb-0 text-muted small">${descriptionInput.value || 'วันหยุด'}</p>
        </div>
        <button class="btn btn-sm btn-outline-danger py-0 px-1 delete-btn" onclick="removeDayOff(this, ${daySelect.value})">ลบ</button>
    `;

    dayOffList.appendChild(listItem);
    daySelect.value = '';
    descriptionInput.value = '';
}

function removeDayOff(button, day) {
    if (confirm('คุณแน่ใจหรือไม่ว่าต้องการลบวันหยุดนี้?')) {
        button.parentElement.remove();
    }
}

function saveDayOffs() {
    console.log("กำลังบันทึกวันหยุด...");
    const dayOffList = document.getElementById('day_off_list');
    const selectedMonth = document.getElementById('month')?.value;
    
    if (!selectedMonth) {
        alert("ไม่พบเดือนที่เลือก");
        return;
    }
    
    const holidays = Array.from(dayOffList.children).map(item => {
        const dayDesc = item.querySelector('.day-description');
        const noteElem = item.querySelector('p.text-muted');
        const day = item.dataset.day;
        const note = noteElem ? noteElem.textContent.trim() : 'วันหยุด';
        
        return {
            date: formatDateString(selectedMonth, day),
            note: note
        };
    });

    console.log("วันหยุดที่จะบันทึก:", holidays);

    const csrftoken = getCookie('csrftoken');

    fetch('/save_day_off/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({
            month: selectedMonth,
            holidays: holidays,
        }),
    })
    .then(res => {
        console.log("ได้รับการตอบกลับ:", res);
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
    })
    .then(data => {
        console.log("ข้อมูลตอบกลับ:", data);
        if (data.status === 'success') {
            alert(data.message || 'บันทึกวันหยุดเรียบร้อยแล้ว');
            location.reload();
        } else {
            alert('เกิดข้อผิดพลาด: ' + (data.message || 'ไม่สามารถบันทึกข้อมูลได้'));
        }
    })
    .catch(err => {
        console.error('Error:', err);
        alert('ไม่สามารถบันทึกข้อมูลได้: ' + err.message);
    });
}

function setAllSundays() {
    const dayOffList = document.getElementById('day_off_list');
    const selectedMonth = document.getElementById('month').value;
    
    if (!selectedMonth) {
        alert("กรุณาเลือกเดือน");
        return;
    }
    
    const [year, month] = selectedMonth.split('-').map(Number);
    const sundays = [];
    const daysInMonthCount = new Date(year, month, 0).getDate();

    for (let day = 1; day <= daysInMonthCount; day++) {
        const date = new Date(year, month - 1, day);
        if (date.getDay() === 0) {
            sundays.push({
                day: day,
                date: date,
                formattedDate: formatThaiDateString(date)
            });
        }
    }

    dayOffList.innerHTML = '';

    sundays.forEach(sunday => {
        const listItem = document.createElement('li');
        listItem.className = 'list-group-item d-flex justify-content-between align-items-center py-1 px-2';
        listItem.dataset.day = sunday.day;
        listItem.innerHTML = `
            <div>
                <span class="day-description">วันที่ ${sunday.day}: <strong>${sunday.formattedDate}</strong> (วันอาทิตย์)</span>
                <p class="mb-0 text-muted small">วันหยุดประจำสัปดาห์</p>
            </div>
            <button class="btn btn-sm btn-outline-danger py-0 px-1 delete-btn" onclick="removeDayOff(this, ${sunday.day})">ลบ</button>
        `;
        dayOffList.appendChild(listItem);
    });
}

function clearDayOffs() {
    if (confirm('คุณแน่ใจหรือไม่ว่าต้องการลบวันหยุดทั้งหมด?')) {
        document.getElementById('day_off_list').innerHTML = '';
    }
}

// เพิ่มฟังก์ชันสำหรับเช็คครึ่งวัน
function setHalfDaysForPerson(personId) {
    const cells = document.querySelectorAll(`td.attendance-cell[data-person="${personId}"]:not(.holiday)`);
    cells.forEach(cell => {
        cell.innerHTML = '<span class="half-day-marker">½</span>';
    });
}

// ฟังก์ชันสำหรับเช็ค/ยกเลิกทั้งหมด
function checkAllDaysForPerson(personId) {
    const cells = document.querySelectorAll(`td.attendance-cell[data-person="${personId}"]:not(.holiday)`);
    cells.forEach(cell => {
        cell.innerHTML = '<span class="full-day-marker">✓</span>';
    });
}

function uncheckAllDaysForPerson(personId) {
    const cells = document.querySelectorAll(`td.attendance-cell[data-person="${personId}"]:not(.holiday)`);
    cells.forEach(cell => {
        cell.innerHTML = '<span class="absent-marker">-</span>';
    });
}

// เพิ่ม event listeners เมื่อหน้าโหลดเสร็จ
document.addEventListener('DOMContentLoaded', function() {
    console.log("ตรวจสอบข้อมูล...");
    // 1. ตรวจสอบตารางและข้อมูล
    const tableContainer = document.getElementById('attendance-table-container');
    
    if (tableContainer) {
        console.log("พบตารางเช็คชื่อ");
        // ตรวจสอบเซลล์ในตาราง
        const cells = document.querySelectorAll('.attendance-cell');
        console.log(`จำนวนเซลล์ทั้งหมด: ${cells.length}`);
        
        // ตรวจสอบสถานะในเซลล์
        let fullDayCount = document.querySelectorAll('.full-day-marker').length;
        let halfDayCount = document.querySelectorAll('.half-day-marker').length;
        let absentCount = document.querySelectorAll('.absent-marker').length;
        
        console.log(`จำนวนวันเต็ม: ${fullDayCount}, ครึ่งวัน: ${halfDayCount}, ขาด: ${absentCount}`);
    } else {
        console.error("ไม่พบตารางเช็คชื่อ");
    }

    // 2. เปิด/ปิดโหมดแก้ไข
    const editModeToggle = document.getElementById('editModeToggle');
    
    if (editModeToggle && tableContainer) {
        editModeToggle.addEventListener('change', function() {
            if (this.checked) {
                // เปิดโหมดแก้ไข
                console.log("เปิดโหมดแก้ไข");
                tableContainer.classList.add('edit-mode-active');
                enableCellEditing(true);
            } else {
                // ปิดโหมดแก้ไข
                console.log("ปิดโหมดแก้ไข");
                tableContainer.classList.remove('edit-mode-active');
                enableCellEditing(false);
            }
        });
    }
    
    // 3. ฟังก์ชันเปิด/ปิดการแก้ไขเซลล์
    function enableCellEditing(enable) {
        const cells = document.querySelectorAll('.attendance-cell:not(.holiday)');
        cells.forEach(cell => {
            if (enable) {
                cell.style.cursor = 'pointer';
                cell.dataset.editable = 'true';
            } else {
                cell.style.cursor = 'default';
                cell.dataset.editable = 'false';
            }
        });
    }
    
    // 4. คลิกที่เซลล์เพื่อเปลี่ยนสถานะ
    document.querySelectorAll('.attendance-cell').forEach(cell => {
        cell.addEventListener('click', function() {
            if (editModeToggle && editModeToggle.checked && !this.classList.contains('holiday')) {
                cycleAttendanceStatus(this);
            }
        });
    });
    
    // 5. เปลี่ยนสถานะการมาทำงาน
    function cycleAttendanceStatus(cell) {
        if (cell.querySelector('.absent-marker')) {
            // เปลี่ยนจาก - เป็น ½
            cell.innerHTML = '<span class="half-day-marker">½</span>';
        } else if (cell.querySelector('.half-day-marker')) {
            // เปลี่ยนจาก ½ เป็น ✓
            cell.innerHTML = '<span class="full-day-marker">✓</span>';
        } else {
            // เปลี่ยนจาก ✓ เป็น -
            cell.innerHTML = '<span class="absent-marker">-</span>';
        }
    }
    
    // 6. แสดงผลวันหยุด (อัปเดตจากข้อมูลที่มีอยู่แล้ว)
    const dayOffList = document.getElementById('day_off_list');
    const selectedMonth = document.getElementById('month')?.value;
    
    if (dayOffList && selectedMonth) {
        // คัดลอกข้อมูลจาก context ที่ถูกส่งมาจาก Django ถ้ามี
        const holidaysData = window.holidaysData || [];
        
        if (holidaysData && holidaysData.length > 0) {
            const [year, month] = selectedMonth.split('-').map(Number);
            
            // ล้างข้อมูลเดิม
            dayOffList.innerHTML = '';
            
            // เพิ่มข้อมูลวันหยุดทั้งหมด
            holidaysData.forEach(holiday => {
                const day = holiday.date__day;
                const note = holiday.note || 'วันหยุด';
                const dateObj = new Date(year, month - 1, day);
                const dayName = getThaiDayName(dateObj);
                const formattedDate = formatThaiDateString(dateObj);
                
                const listItem = document.createElement('li');
                listItem.className = 'list-group-item d-flex justify-content-between align-items-center py-1 px-2';
                listItem.dataset.day = day;
                listItem.innerHTML = `
                    <div>
                        <span class="day-description">วันที่ ${day}: <strong>${formattedDate}</strong> (วัน${dayName})</span>
                        <p class="mb-0 text-muted small">${note}</p>
                    </div>
                    <button class="btn btn-sm btn-outline-danger py-0 px-1 delete-btn" onclick="removeDayOff(this, ${day})">ลบ</button>
                `;
                dayOffList.appendChild(listItem);
            });
        }
    }
});