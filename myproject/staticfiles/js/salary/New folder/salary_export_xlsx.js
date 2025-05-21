// ชื่อเดือนไทย
const THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม",
    "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน",
    "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
];

// ฟังก์ชันแสดง/ซ่อน loading
function showLoading(message) {
    // ถ้ายังไม่มี loading element ให้สร้างขึ้นมา
    if (!document.getElementById('loadingIndicator')) {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loadingIndicator';
        loadingDiv.style.position = 'fixed';
        loadingDiv.style.top = '0';
        loadingDiv.style.left = '0';
        loadingDiv.style.width = '100%';
        loadingDiv.style.height = '100%';
        loadingDiv.style.backgroundColor = 'rgba(0,0,0,0.5)';
        loadingDiv.style.display = 'flex';
        loadingDiv.style.justifyContent = 'center';
        loadingDiv.style.alignItems = 'center';
        loadingDiv.style.zIndex = '9999';
        
        const loadingContent = document.createElement('div');
        loadingContent.style.backgroundColor = 'white';
        loadingContent.style.padding = '20px';
        loadingContent.style.borderRadius = '5px';
        loadingContent.style.textAlign = 'center';
        
        const spinner = document.createElement('div');
        spinner.className = 'spinner-border text-primary';
        spinner.setAttribute('role', 'status');
        
        const loadingText = document.createElement('p');
        loadingText.id = 'loadingText';
        loadingText.style.marginTop = '10px';
        loadingText.textContent = message || 'กำลังโหลด...';
        
        loadingContent.appendChild(spinner);
        loadingContent.appendChild(loadingText);
        loadingDiv.appendChild(loadingContent);
        document.body.appendChild(loadingDiv);
    } else {
        document.getElementById('loadingText').textContent = message || 'กำลังโหลด...';
        document.getElementById('loadingIndicator').style.display = 'flex';
    }
}

function hideLoading() {
    const loadingDiv = document.getElementById('loadingIndicator');
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
}

// ตรวจสอบว่ามีการโหลด XLSX library
function checkXLSXLibrary() {
    if (typeof XLSX === 'undefined') {
        console.error("XLSX library not loaded. Please include the library in your HTML.");
        alert("กรุณาเพิ่มไลบรารี XLSX.js ในไฟล์ HTML");
        return false;
    }
    console.log("XLSX library successfully loaded");
    return true;
}

function exportTableToExcel() {
    if (!checkXLSXLibrary()) return;
    
    try {
        console.log("Starting Excel export...");
        // Create new workbook
        const wb = XLSX.utils.book_new();
        
        // Convert table to worksheet
        const table = document.getElementById("salaryTable");
        if (!table) {
            console.error("Table with ID 'salaryTable' not found");
            alert("ไม่พบตารางสำหรับส่งออก");
            return;
        }
        
        console.log("Converting table to worksheet...");
        const ws = XLSX.utils.table_to_sheet(table);
        
        // Set column widths
        ws['!cols'] = [
            { width: 30 }, // Employee name
            { width: 20 }, // Position
            { width: 15 }, // Department
            { width: 15 }, // Status
            { width: 15 }  // Management
        ];
        
        // Add worksheet to workbook
        XLSX.utils.book_append_sheet(wb, ws, "รายการเงินเดือน");
        
        // แยกปี และ เดือนจาก selectedMonth (รูปแบบ YYYY-MM)
        const month = selectedMonth;
        const [year, monthNumber] = month.split("-");
        
        // สร้างชื่อไฟล์เริ่มต้นที่มีเดือนและปีไทย
        const thaiMonth = THAI_MONTHS[parseInt(monthNumber)];
        const thaiYear = parseInt(year) + 543;
        const fileName = `เงินเดือน_${thaiMonth}_${thaiYear}.xlsx`;
        
        console.log("Writing Excel file:", fileName);
        // Save Excel file
        XLSX.writeFile(wb, fileName);
        console.log("Excel export completed successfully");
    } catch (error) {
        console.error("Error exporting to Excel:", error);
        alert("เกิดข้อผิดพลาดในการส่งออกไฟล์ Excel: " + error.message);
    }
}

function exportPersonSalaryExcel(personId) {
    if (!personId) {
        personId = currentPersonId;
    }
    
    if (!personId) {
        alert("ไม่พบข้อมูลพนักงาน");
        return;
    }
    
    // ดึงข้อมูลเดือนปัจจุบัน
    const month = selectedMonth;
    console.log(`กำลังส่งออกข้อมูลเงินเดือน: รหัสพนักงาน ${personId}, เดือน ${month}`);
    
    // แยกปี และ เดือนจาก selectedMonth (รูปแบบ YYYY-MM)
    const [year, monthNumber] = month.split("-");
    
    // สร้างชื่อไฟล์เริ่มต้นที่มีเดือนและปีไทย
    const thaiMonth = THAI_MONTHS[parseInt(monthNumber)];
    const thaiYear = parseInt(year) + 543;
    const defaultFilename = `สลิปเงินเดือน_${thaiMonth}_${thaiYear}.xlsx`;
    
    // แสดง loading
    showLoading("กำลังสร้างไฟล์ Excel...");
    
    // เรียกใช้ API เพื่อดึงข้อมูลพนักงาน
    fetch(`/api/salary_info/${personId}/?month=${month}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`เซิร์ฟเวอร์ตอบกลับด้วยสถานะ ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // ดึงชื่อพนักงานจาก API
            let employeeName = data.name || "";
            
            console.log("ข้อมูลพนักงานจาก API:", data);
            console.log("ชื่อพนักงานเดิม:", employeeName);
            
            // แปลงคำนำหน้าภาษาอังกฤษเป็นภาษาไทย
            employeeName = employeeName.replace(/^Mr\s+/i, "นาย ");
            employeeName = employeeName.replace(/^Mrs\s+/i, "นาง ");
            employeeName = employeeName.replace(/^Ms\s+/i, "นางสาว ");
            
            console.log("ชื่อพนักงานหลังแปลงคำนำหน้า:", employeeName);
            
            // สร้างชื่อไฟล์ที่มีชื่อพนักงาน
            let filename = defaultFilename;
            
            // ตรวจสอบว่ามีชื่อพนักงานหรือไม่
            if (employeeName && employeeName !== "-" && employeeName !== "") {
                filename = `สลิปเงินเดือนของ${employeeName}_${thaiMonth}_${thaiYear}.xlsx`;
                console.log("ใช้ชื่อไฟล์พร้อมชื่อพนักงาน:", filename);
            } else {
                console.log("ไม่มีชื่อพนักงาน ใช้ชื่อไฟล์ปกติ:", filename);
            }
            
            // URL สำหรับดาวน์โหลด Excel
            const exportUrl = `/api/export_person_salary/${personId}/?month=${month}`;
            
            // ดาวน์โหลดไฟล์
            return fetch(exportUrl)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`เซิร์ฟเวอร์ตอบกลับด้วยสถานะ ${response.status}`);
                    }
                    return response.blob();
                })
                .then(blob => {
                    // สร้าง URL และ link สำหรับดาวน์โหลด
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    
                    // ทำความสะอาด
                    setTimeout(() => {
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                        hideLoading();
                    }, 100);
                });
        })
        .catch(error => {
            console.error("Error exporting Excel:", error);
            alert("เกิดข้อผิดพลาดในการส่งออกข้อมูล: " + error.message);
            hideLoading();
            
            // กรณีเกิดข้อผิดพลาด ลองดาวน์โหลดแบบไม่มีชื่อพนักงาน
            const exportUrl = `/api/export_person_salary/${personId}/?month=${month}`;
            fetch(exportUrl)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`เซิร์ฟเวอร์ตอบกลับด้วยสถานะ ${response.status}`);
                    }
                    return response.blob();
                })
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = defaultFilename;
                    document.body.appendChild(a);
                    a.click();
                    setTimeout(() => {
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                    }, 100);
                })
                .catch(innerError => {
                    console.error("Error in fallback download:", innerError);
                });
        });
}
// จัดรูปแบบ worksheet
function formatPayslipWorksheet(ws) {
    // กำหนดความกว้างคอลัมน์
    ws['!cols'] = [
        { width: 20 }, // A
        { width: 15 }, // B
        { width: 10 }, // C
        { width: 20 }, // D
        { width: 15 }, // E
        { width: 10 }  // F
    ];
    
    // กำหนดการรวมเซลล์
    ws['!merges'] = [
        { s: { r: 0, c: 0 }, e: { r: 0, c: 2 } }, // A1:C1 (ชื่อบริษัท)
        { s: { r: 0, c: 4 }, e: { r: 0, c: 5 } }, // E1:F1 (ใบรายเงินเดือน)
        { s: { r: 1, c: 0 }, e: { r: 1, c: 2 } }, // A2:C2 (ที่อยู่บริษัท)
        { s: { r: 1, c: 4 }, e: { r: 1, c: 5 } }, // E2:F2 (Pay Slip)
        { s: { r: 2, c: 0 }, e: { r: 2, c: 1 } }, // A3:B3 (ชื่อพนักงาน)
        { s: { r: 2, c: 2 }, e: { r: 2, c: 3 } }, // C3:D3 (ตำแหน่ง)
    ];
    
    // กำหนดรูปแบบสีพื้นหลัง
    const headerStyle = { fill: { fgColor: { rgb: "4F4F4F" }, patternType: "solid" }, font: { color: { rgb: "FFFFFF" } } };
    const subTotalStyle = { fill: { fgColor: { rgb: "DDDDDD" }, patternType: "solid" } };
    const netPayStyle = { fill: { fgColor: { rgb: "FFFFCC" }, patternType: "solid" } };
    
    // กำหนดรูปแบบของเซลล์
    for (let i = 0; i < 30; i++) {
        // กำหนดสีพื้นหลังส่วนหัวตาราง
        if (i === 4) {
            for (let j = 0; j < 6; j++) {
                const cellRef = XLSX.utils.encode_cell({ r: i, c: j });
                if (!ws[cellRef]) ws[cellRef] = {};
                ws[cellRef].s = headerStyle;
            }
        }
        
        // กำหนดสีพื้นหลังส่วนสรุปรายรับรายจ่าย
        if (i === 13) {
            for (let j = 0; j < 6; j++) {
                const cellRef = XLSX.utils.encode_cell({ r: i, c: j });
                if (!ws[cellRef]) ws[cellRef] = {};
                ws[cellRef].s = subTotalStyle;
            }
        }
        
        // กำหนดสีพื้นหลังส่วนเงินรับสุทธิ
        if (i === 16) {
            for (let j = 3; j < 6; j++) {
                const cellRef = XLSX.utils.encode_cell({ r: i, c: j });
                if (!ws[cellRef]) ws[cellRef] = {};
                ws[cellRef].s = headerStyle;
            }
        }
        
        if (i === 17) {
            for (let j = 3; j < 6; j++) {
                const cellRef = XLSX.utils.encode_cell({ r: i, c: j });
                if (!ws[cellRef]) ws[cellRef] = {};
                ws[cellRef].s = netPayStyle;
            }
        }
    }
}

function exportAllSalaryExcel() {
    const month = selectedMonth;
    console.log("📦 เรียก exportAllSalaryExcel สำหรับเดือน:", month);

    // แยกปี และ เดือนจาก selectedMonth (รูปแบบ YYYY-MM)
    const [year, monthNumber] = month.split("-");
    
    // สร้างชื่อไฟล์เริ่มต้นที่มีเดือนและปีไทย
    const thaiMonth = THAI_MONTHS[parseInt(monthNumber)];
    const thaiYear = parseInt(year) + 543;
    const filename = `รวมสลิปเงินเดือน_${thaiMonth}_${thaiYear}.xlsx`;

    console.log("Excel filename:", filename);

    showLoading("กำลังสร้างไฟล์ Excel รวม...");
    fetch(`/api/export_all_salary_excel/?month=${month}`)
        .then(response => {
            if (!response.ok) throw new Error("โหลด Excel ล้มเหลว");
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            a.style.display = "none";
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                hideLoading();
            }, 100);
        })
        .catch(error => {
            console.error("❌ Export Excel รวมล้มเหลว:", error);
            alert("เกิดข้อผิดพลาดในการรวม Excel: " + error.message);
            hideLoading();
        });
}