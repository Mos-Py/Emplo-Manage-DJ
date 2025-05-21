// ฟังก์ชันแสดง/ซ่อน loading
function showLoading(message = 'กำลังโหลด...') {
  let loadingDiv = document.getElementById('loadingIndicator');
  
  if (!loadingDiv) {
    loadingDiv = document.createElement('div');
    loadingDiv.id = 'loadingIndicator';
    Object.assign(loadingDiv.style, {
      position: 'fixed',
      top: '0',
      left: '0',
      width: '100%',
      height: '100%',
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: '9999'
    });
    
    const content = document.createElement('div');
    Object.assign(content.style, {
      backgroundColor: 'white',
      padding: '20px',
      borderRadius: '5px',
      textAlign: 'center'
    });
    
    const spinner = document.createElement('div');
    spinner.className = 'spinner-border text-primary';
    spinner.setAttribute('role', 'status');
    
    const text = document.createElement('p');
    text.id = 'loadingText';
    text.style.marginTop = '10px';
    
    content.appendChild(spinner);
    content.appendChild(text);
    loadingDiv.appendChild(content);
    document.body.appendChild(loadingDiv);
  }
  
  document.getElementById('loadingText').textContent = message;
  loadingDiv.style.display = 'flex';
}

function hideLoading() {
  const loadingDiv = document.getElementById('loadingIndicator');
  if (loadingDiv) loadingDiv.style.display = 'none';
}

// ฟังก์ชันช่วยในการดาวน์โหลด
function downloadFile(url, filename, onError) {
  fetch(url)
    .then(response => {
      if (!response.ok) throw new Error(`เซิร์ฟเวอร์ตอบกลับ ${response.status}`);
      return response.blob();
    })
    .then(blob => {
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      setTimeout(() => {
        URL.revokeObjectURL(link.href);
        document.body.removeChild(link);
        hideLoading();
      }, 100);
    })
    .catch(error => {
      console.error(error);
      if (onError) onError(error);
      hideLoading();
    });
}

// Export Excel รวมทั้งหมด
function exportAllSalaryExcel() {
  showLoading("กำลังสร้างไฟล์ Excel รวม...");
  
  const filename = createThaiFilename('รวมสลิปเงินเดือน') + '.xlsx';
  downloadFile(
    `/api/export_all_salary_excel/?month=${selectedMonth}`,
    filename, 
    error => alert(`เกิดข้อผิดพลาดในการรวม Excel: ${error.message}`)
  );
}

// Export Excel รายบุคคล
function exportPersonSalaryExcel(personId) {
  if (!personId) personId = currentPersonId;
  if (!personId) return alert("ไม่พบข้อมูลพนักงาน");
  
  showLoading("กำลังสร้างไฟล์ Excel...");
  
  // ดึงข้อมูลชื่อพนักงานแล้วดาวน์โหลด
  fetch(`/api/salary_info/${personId}/?month=${selectedMonth}`)
    .then(response => response.ok ? response.json() : Promise.reject("ไม่สามารถดึงข้อมูลพนักงาน"))
    .then(data => {
      const filename = createThaiFilename('สลิปเงินเดือน', data.name) + '.xlsx';
      downloadFile(
        `/api/export_person_salary/${personId}/?month=${selectedMonth}`,
        filename, 
        error => alert(`เกิดข้อผิดพลาดในการส่งออกข้อมูล: ${error.message}`)
      );
    })
    .catch(error => {
      console.error(error);
      hideLoading();
      alert("เกิดข้อผิดพลาดในการดึงข้อมูลพนักงาน");
    });
}

// Export PDF รวมทั้งหมด
function exportAllSalaryPDF() {
  showLoading("กำลังสร้างไฟล์ PDF รวม...");
  
  const filename = createThaiFilename('สลิปเงินเดือน') + '.pdf';
  downloadFile(
    `/api/gen_pdf_v2/?month=${selectedMonth}`,
    filename, 
    error => alert(`เกิดข้อผิดพลาดในการรวม PDF: ${error.message}`)
  );
}

// Export PDF รายบุคคล
function exportPersonSalaryPDF(personId) {
  if (!personId) personId = currentPersonId;
  if (!personId) return alert("ไม่พบข้อมูลพนักงาน");
  
  showLoading("กำลังสร้างไฟล์ PDF...");
  
  // ดึงข้อมูลชื่อพนักงาน
  fetch(`/api/salary_info/${personId}/?month=${selectedMonth}`)
    .then(response => response.ok ? response.json() : Promise.reject("ไม่สามารถดึงข้อมูลพนักงาน"))
    .then(data => {
      // ดาวน์โหลด Excel ก่อน
      return fetch(`/api/export_person_salary/${personId}/?month=${selectedMonth}`)
        .then(response => response.ok ? response.blob() : Promise.reject("ไม่สามารถดาวน์โหลด Excel"))
        .then(blob => {
          // แปลงเป็น PDF
          const formData = new FormData();
          formData.append('excel_file', blob, `salary_${personId}_${selectedMonth}.xlsx`);
          
          return fetch('/api/convert_excel_to_pdf/', {
            method: 'POST',
            body: formData
          }).then(response => {
            if (!response.ok) throw new Error("การแปลงไฟล์ล้มเหลว");
            return response.blob();
          }).then(pdfBlob => {
            // สร้างชื่อไฟล์และดาวน์โหลด
            const filename = createThaiFilename('สลิปเงินเดือน', data.name) + '.pdf';
            const url = URL.createObjectURL(pdfBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            setTimeout(() => {
              URL.revokeObjectURL(url);
              document.body.removeChild(link);
              hideLoading();
            }, 100);
          });
        });
    })
    .catch(error => {
      console.error(error);
      hideLoading();
      alert(`เกิดข้อผิดพลาดในการสร้างไฟล์ PDF: ${error instanceof Error ? error.message : error}`);
    });
}