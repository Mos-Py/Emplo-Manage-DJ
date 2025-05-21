// ตัวแปรแปลงคำนำหน้าและเดือน
const TITLE_MAPPING = {
  'Mr': 'นาย',
  'Mrs': 'นาง',
  'Ms': 'นางสาว'
};

const THAI_MONTHS = [
  "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม",
  "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
];

// ฟังก์ชันแปลงคำนำหน้าเป็นภาษาไทย
function convertTitleToThai() {
  document.querySelectorAll("#salaryTable tbody tr td:first-child").forEach(cell => {
    let name = cell.textContent.trim();
    for (const [engTitle, thaiTitle] of Object.entries(TITLE_MAPPING)) {
      name = name.replace(new RegExp(`^${engTitle}\\s+`, 'i'), `${thaiTitle} `);
    }
    cell.textContent = name;
  });
}

// ฟังก์ชันแปลงเดือนเป็นภาษาไทย
function setupThaiMonthDisplay() {
  const monthSelect = document.getElementById("monthSelect");
  if (!monthSelect) return;
  
  // บันทึกค่าปัจจุบันและพาเรนต์โนด
  const currentValue = monthSelect.value;
  const parentNode = monthSelect.parentNode;
  const originalInputId = monthSelect.id;
  const originalInputName = monthSelect.name;
  const originalClasses = monthSelect.className;
  const originalStyle = monthSelect.style.cssText;
  
  // สร้าง wrapper ใหม่
  const wrapper = document.createElement('div');
  wrapper.className = 'month-select-wrapper';
  wrapper.style.position = 'relative';
  wrapper.style.display = 'inline-block';
  
  // ฟังก์ชันแปลงเดือนและปีเป็นภาษาไทย
  const formatThaiMonth = (dateStr) => {
    if (!dateStr) return "";
    const [year, month] = dateStr.split("-");
    return `${THAI_MONTHS[parseInt(month)]} ${parseInt(year) + 543}`;
  };
  
  // สร้าง input ใหม่ที่ซ่อนไว้สำหรับเก็บค่าจริง
  const hiddenInput = document.createElement('input');
  hiddenInput.type = 'month';
  hiddenInput.id = originalInputId;
  hiddenInput.name = originalInputName || 'month';
  hiddenInput.value = currentValue;
  hiddenInput.style.cssText = 'position: absolute; opacity: 0; width: 1px; height: 1px;';
  
  // สร้างช่องแสดงเดือนภาษาไทย
  const thaiDisplay = document.createElement('div');
  thaiDisplay.className = originalClasses || 'form-control';
  thaiDisplay.style.cssText = originalStyle;
  thaiDisplay.style.cursor = 'pointer';
  thaiDisplay.style.width = '200px';
  thaiDisplay.style.display = 'inline-flex';
  thaiDisplay.style.alignItems = 'center';
  thaiDisplay.innerHTML = `<i class="fas fa-calendar-alt me-2"></i><span>${formatThaiMonth(currentValue)}</span>`;
  
  // แทนที่ช่องเดิมด้วย wrapper ที่มีช่องใหม่
  parentNode.replaceChild(wrapper, monthSelect);
  wrapper.appendChild(hiddenInput);
  wrapper.appendChild(thaiDisplay);
  
  // เพิ่ม event listeners
  thaiDisplay.addEventListener('click', () => {
    hiddenInput.showPicker();
  });
  
  hiddenInput.addEventListener('change', function() {
    thaiDisplay.querySelector('span').textContent = formatThaiMonth(this.value);
    location.href = `?month=${this.value}`;
  });
  
  // ทำให้ wrapper นี้ไม่ติดกับ label ถ้ามี
  const label = document.querySelector(`label[for="${originalInputId}"]`);
  if (label) {
    label.addEventListener('click', () => {
      hiddenInput.showPicker();
    });
  }
}

// สร้างชื่อไฟล์ภาษาไทย
function createThaiFilename(prefix, personName = null) {
  const [year, month] = selectedMonth.split('-');
  const thaiMonth = THAI_MONTHS[parseInt(month)];
  const thaiYear = parseInt(year) + 543;
  
  if (personName) {
    // แปลงคำนำหน้า
    Object.entries(TITLE_MAPPING).forEach(([eng, thai]) => {
      personName = personName.replace(new RegExp(`^${eng}\\s+`, 'i'), `${thai} `);
    });
    return `${prefix}ของ${personName}_${thaiMonth}_${thaiYear}`;
  }
  
  return `${prefix}_${thaiMonth}_${thaiYear}`;
}

// เริ่มต้นเมื่อเว็บโหลดเสร็จ
document.addEventListener("DOMContentLoaded", function() {
  convertTitleToThai();
  setupThaiMonthDisplay();
});