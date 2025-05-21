// ตรวจสอบว่า THAI_MONTHS มีอยู่แล้วหรือไม่
if (typeof THAI_MONTHS === 'undefined') {
    const THAI_MONTHS = [
        "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม",
        "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน",
        "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ];
}

// Export ข้อมูลเงินเดือนรายบุคคลเป็น PDF
function exportPersonSalaryPDF(personId) {
    if (!personId) {
        personId = currentSalaryPersonId;
    }
    
    if (!personId) {
        alert("ไม่พบข้อมูลพนักงาน");
        return;
    }
    
    // ดึงข้อมูลเดือนปัจจุบัน
    const month = selectedMonth;
    
    // แยกปี และ เดือนจาก selectedMonth (รูปแบบ YYYY-MM)
    const [year, monthNumber] = month.split("-");
    
    // สร้างชื่อไฟล์เริ่มต้นที่มีเดือนและปีไทย
    const thaiMonth = THAI_MONTHS[parseInt(monthNumber)];
    const thaiYear = parseInt(year) + 543;
    const defaultFilename = `สลิปเงินเดือน_${thaiMonth}_${thaiYear}.pdf`;
    
    // เริ่มแสดง loading spinner หรือข้อความ
    showLoading("กำลังสร้างไฟล์ PDF...");
    
    // เรียกใช้ API เพื่อดึงข้อมูลพนักงานก่อน
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
            let personFilename = defaultFilename;
            
            // ตรวจสอบว่ามีชื่อพนักงานหรือไม่
            if (employeeName && employeeName !== "-" && employeeName !== "") {
                personFilename = `สลิปเงินเดือนของ${employeeName}_${thaiMonth}_${thaiYear}.pdf`;
                console.log("ใช้ชื่อไฟล์พร้อมชื่อพนักงาน:", personFilename);
            } else {
                console.log("ไม่มีชื่อพนักงาน ใช้ชื่อไฟล์ปกติ:", personFilename);
            }
            
            // 1. ดาวน์โหลดไฟล์ Excel ก่อน
            return fetch(`/api/export_person_salary/${personId}/?month=${month}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`เซิร์ฟเวอร์ตอบกลับด้วยสถานะ ${response.status}`);
                    }
                    return response.blob();
                })
                .then(blob => {
                    // 2. ส่ง blob ต่อไปยัง API endpoint เฉพาะสำหรับแปลง Excel เป็น PDF
                    const formData = new FormData();
                    formData.append('excel_file', blob, `salary_${personId}_${month}.xlsx`);
                    
                    return fetch('/api/convert_excel_to_pdf/', {
                        method: 'POST',
                        body: formData
                    }).then(response => {
                        if (!response.ok) {
                            throw new Error(`การแปลงไฟล์ล้มเหลว: ${response.status}`);
                        }
                        
                        // อ่านชื่อไฟล์จาก header
                        const contentDisposition = response.headers.get("Content-Disposition");
                        let filename = personFilename; // ใช้ชื่อเริ่มต้นที่มีเดือนและปีไทยและชื่อพนักงาน
                        
                        if (contentDisposition) {
                            // กรณีมี filename*=UTF-8''
                            const filenameMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
                            if (filenameMatch && filenameMatch[1]) {
                                const serverFilename = decodeURIComponent(filenameMatch[1]);
                                // ใช้ชื่อจาก server เฉพาะกรณีที่ไม่ได้กำหนดชื่อพนักงานไว้
                                if (!employeeName) {
                                    filename = serverFilename;
                                }
                                console.log("Found filename* match:", serverFilename);
                            } else {
                                // กรณีมี filename="..."
                                const regularMatch = contentDisposition.match(/filename="([^"]+)"/i);
                                if (regularMatch && regularMatch[1]) {
                                    const serverFilename = regularMatch[1];
                                    // ใช้ชื่อจาก server เฉพาะกรณีที่ไม่ได้กำหนดชื่อพนักงานไว้
                                    if (!employeeName) {
                                        filename = serverFilename;
                                    }
                                    console.log("Found regular filename match:", serverFilename);
                                }
                            }
                        }
                        
                        return response.blob().then(blob => ({ blob, filename }));
                    });
                })
                .then(({ blob, filename }) => {
                    console.log("Downloading file with name:", filename);
                    
                    // 3. ดาวน์โหลดไฟล์ PDF
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = filename;  // ใช้ชื่อที่ได้จาก header หรือชื่อเริ่มต้น
                    document.body.appendChild(a);
                    a.click();
                    
                    // ทำความสะอาดหลังจากดาวน์โหลด
                    setTimeout(() => {
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                        hideLoading();
                    }, 100);
                });
        })
        .catch(error => {
            console.error("Error exporting PDF:", error);
            alert("เกิดข้อผิดพลาดในการสร้างไฟล์ PDF: " + error.message);
            hideLoading();
            
            // ลองดาวน์โหลดไฟล์ Excel แทนในกรณีที่เกิดข้อผิดพลาด
            fetch(`/api/export_person_salary/${personId}/?month=${month}`)
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
                    a.download = `สลิปเงินเดือน_${thaiMonth}_${thaiYear}.xlsx`;
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

// ฟังก์ชันช่วยแสดง/ซ่อน loading
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

function exportAllSalaryPDF() {
    const month = selectedMonth;
    console.log("🧾 เรียก exportAllSalaryPDF สำหรับเดือน:", month);

    // แยกปี และ เดือนจาก selectedMonth (รูปแบบ YYYY-MM)
    const [year, monthNumber] = month.split("-");
    
    // สร้างชื่อไฟล์เริ่มต้นที่มีเดือนและปีไทย
    const thaiMonth = THAI_MONTHS[parseInt(monthNumber)];
    const thaiYear = parseInt(year) + 543;
    const defaultFilename = `สลิปเงินเดือน_${thaiMonth}_${thaiYear}.pdf`;

    console.log("Default filename:", defaultFilename);

    showLoading("กำลังสร้างไฟล์ PDF รวม...");

    fetch(`/api/gen_pdf_v2/?month=${month}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`เซิร์ฟเวอร์ตอบกลับด้วยสถานะ ${response.status}`);
            }
            
            const contentDisposition = response.headers.get("Content-Disposition");
            console.log("Content-Disposition:", contentDisposition); // เพิ่ม logging เพื่อดีบัก
            
            let filename = defaultFilename; // ใช้ชื่อเริ่มต้นที่มีเดือนและปีไทย
            
            // แก้ไขการใช้ regex
            if (contentDisposition) {
                // กรณีมี filename*=UTF-8''
                const filenameMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
                if (filenameMatch && filenameMatch[1]) {
                    filename = decodeURIComponent(filenameMatch[1]);
                    console.log("Found filename* match:", filename);
                } else {
                    // กรณีมี filename="..."
                    const regularMatch = contentDisposition.match(/filename="([^"]+)"/i);
                    if (regularMatch && regularMatch[1]) {
                        filename = regularMatch[1];
                        console.log("Found regular filename match:", filename);
                    }
                }
            }
            
            console.log("Final filename:", filename);
            return response.blob().then(blob => ({ blob, filename }));
        })
        .then(({ blob, filename }) => {
            console.log("Downloading file with name:", filename);
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            a.style.display = "none";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            // ซ่อน loading
            hideLoading();
            
            setTimeout(() => window.URL.revokeObjectURL(url), 100);
        })
        .catch(error => {
            console.error("❌ Export PDF รวมล้มเหลว:", error);
            alert("เกิดข้อผิดพลาดในการรวม PDF: " + error.message);
            hideLoading();
        });
}