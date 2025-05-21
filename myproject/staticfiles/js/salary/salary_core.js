/**
 * Script สำหรับการจัดการ Modal เงินเดือน
 * รวบรวมฟังก์ชันสำคัญที่เกี่ยวข้องกับการทำงานของ Modal เงินเดือน
 */

// ตัวแปรกลาง
let currentPersonId = null;
let selectedMonth = document.getElementById("monthSelect")?.value || (new Date()).toISOString().substring(0, 7);

// เมื่อเอกสารโหลดเสร็จ
document.addEventListener("DOMContentLoaded", function() {
    console.log("DOM โหลดเสร็จแล้ว กำลังตั้งค่าระบบ Modal...");

    // ตั้งค่าเดือนที่เลือก
    const monthSelect = document.getElementById("monthSelect");
    if (monthSelect) {
        selectedMonth = monthSelect.value || (new Date()).toISOString().substring(0, 7);
        console.log("กำหนดเดือนที่เลือก:", selectedMonth);

        monthSelect.addEventListener("change", function() {
            selectedMonth = this.value;
            location.href = `?month=${selectedMonth}`;
        });
    }

    // แก้ไขปุ่มดูข้อมูล
    setupShowSalaryButtons();

    // ✅ ผูกปุ่มรวม Excel
    const btnExcel = document.getElementById("btnExcel");
    if (btnExcel) {
        btnExcel.addEventListener("click", function () {
            console.log("📦 กดปุ่มรวม Excel แล้ว");
            exportAllSalaryExcel();
        });
    }

    // ✅ ผูกปุ่มรวม PDF
    const btnPdf = document.getElementById("btnPdf");
    if (btnPdf) {
        btnPdf.addEventListener("click", function () {
            console.log("🧾 กดปุ่มรวม PDF แล้ว");
            exportAllSalaryPDF();
        });
    }
});


// ตั้งค่าปุ่มดูข้อมูลเงินเดือน
function setupShowSalaryButtons() {
    console.log("กำลังตั้งค่าปุ่มดูข้อมูลเงินเดือน...");
    
    const buttons = document.querySelectorAll('.show-salary-btn');
    console.log("พบปุ่มดูข้อมูลทั้งหมด:", buttons.length);
    
    buttons.forEach(function(btn) {
        const personId = btn.getAttribute('data-person-id');
        console.log("กำลังตั้งค่าปุ่มสำหรับพนักงานรหัส:", personId);
        
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log("คลิกปุ่มดูข้อมูลของพนักงานรหัส:", personId);
            window.currentPersonId = personId;
            currentPersonId = personId;
            showSalaryDetailsWithID(personId);
            return false;
        });
    });
}

/**
 * ฟังก์ชันแสดงข้อมูลเงินเดือนจากรหัสพนักงาน
 * @param {string} personId - รหัสพนักงาน
 */
function showSalaryDetailsWithID(personId) {
    console.log("เรียกฟังก์ชัน showSalaryDetailsWithID สำหรับพนักงานรหัส:", personId);
    
    // ซ่อนช่องข้อมูลเงินกู้ก่อนโหลดข้อมูล
    const loanPaymentEl = document.getElementById("savedLoanPayment");
    if (loanPaymentEl) {
        loanPaymentEl.classList.add("d-none");
        loanPaymentEl.classList.remove("d-flex");
    }
    
    const loanEl = document.getElementById("savedLoan");
    if (loanEl) {
        loanEl.style.display = "none";
    }
    
    // สร้าง Modal
    const modalElement = document.getElementById("salaryDetailsModal");
    if (!modalElement) {
        console.error("ไม่พบ Modal element: salaryDetailsModal");
        alert("ไม่พบหน้าต่างแสดงข้อมูลเงินเดือน");
        return;
    }
    
    const modal = new bootstrap.Modal(modalElement);
    
    // โหลดข้อมูล
    Promise.all([
        fetch(`/api/saved_salary/${personId}/?month=${selectedMonth}`).then(res => {
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        }),
        fetch(`/api/loan_summary/${personId}/?month=${selectedMonth}`).then(res => {
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        }),
        fetch(`/api/withdraw_history/${personId}/?month=${selectedMonth}`).then(res => {
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        })
    ])
    .then(([salaryData, loanData, withdrawData]) => {
        console.log(`ข้อมูลเงินเดือนของพนักงานรหัส ${personId}:`, salaryData);
        
        // แสดงข้อมูลพื้นฐาน
        const savedBaseEl = document.getElementById("savedBase");
        if (savedBaseEl) {
            savedBaseEl.innerText = salaryData.base_salary.toLocaleString(undefined, {minimumFractionDigits: 2}) + " บาท";
        }
        
        const savedCommissionEl = document.getElementById("savedCommission");
        if (savedCommissionEl) {
            savedCommissionEl.innerText = salaryData.commission.toLocaleString(undefined, {minimumFractionDigits: 2}) + " บาท";
        }
        
        const savedBonusEl = document.getElementById("savedBonus");
        if (savedBonusEl) {
            savedBonusEl.innerText = salaryData.bonus.toLocaleString(undefined, {minimumFractionDigits: 2}) + " บาท";
        }
        
        const savedDeductionEl = document.getElementById("savedDeduction");
        if (savedDeductionEl) {
            savedDeductionEl.innerText = salaryData.withdraw.toLocaleString(undefined, {minimumFractionDigits: 2}) + " บาท";
        }
        
        const savedTotalEl = document.getElementById("savedTotal");
        if (savedTotalEl) {
            savedTotalEl.innerText = salaryData.total_salary.toLocaleString(undefined, {minimumFractionDigits: 2}) + " บาท";
        }
        
        // แสดงข้อมูล ปกส.
        const savedSSEl = document.getElementById("savedSS");
        if (savedSSEl) {
            if (salaryData.ss_amount && salaryData.ss_amount > 0) {
                savedSSEl.style.display = "flex";
                const savedSSAmountEl = document.getElementById("savedSSAmount");
                if (savedSSAmountEl) {
                    savedSSAmountEl.innerText = salaryData.ss_amount.toLocaleString(undefined, {minimumFractionDigits: 2}) + " บาท";
                }
            } else {
                savedSSEl.style.display = "none";
            }
        }
        
        // แสดงข้อมูลเงินกู้
        if (loanPaymentEl && salaryData.loan_payment && salaryData.loan_payment > 0) {
            loanPaymentEl.classList.remove("d-none");
            loanPaymentEl.classList.add("d-flex");
            const savedLoanPaymentAmountEl = document.getElementById("savedLoanPaymentAmount");
            if (savedLoanPaymentAmountEl) {
                savedLoanPaymentAmountEl.innerText = salaryData.loan_payment.toLocaleString(undefined, {minimumFractionDigits: 2}) + " บาท";
            }
        }
        
        // แสดงข้อมูลเงินกู้คงเหลือ
        if (loanEl && Number(loanData.loan_remaining) > 0) {
            loanEl.classList.remove("d-none");
            loanEl.classList.add("d-flex");
            const savedLoanRemainingEl = document.getElementById("savedLoanRemaining");
            if (savedLoanRemainingEl) {
                savedLoanRemainingEl.innerText = Number(loanData.loan_remaining).toLocaleString(undefined, {minimumFractionDigits: 2}) + " บาท";
            }
        }
        
        // แสดงประวัติการเบิกเงิน
        displayWithdrawHistory(withdrawData);
        
        // ตั้งค่าปุ่ม Export ใน Modal
        setupModalExportButtons(personId);
    })
    .catch(error => {
        console.error("เกิดข้อผิดพลาดในการโหลดข้อมูล:", error);
        alert("เกิดข้อผิดพลาดในการโหลดข้อมูล: " + error.message);
    });
    
    // แสดงโมดัล
    modal.show();
}

/**
 * ตั้งค่าปุ่ม Export ใน Modal
 * @param {string} personId - รหัสพนักงาน
 */
function setupModalExportButtons(personId) {
    console.log("กำลังตั้งค่าปุ่ม Export ใน Modal...");
    
    // ตั้งค่าปุ่ม Export Excel
    const btnExportExcel = document.querySelector('.modal-footer button[onclick="exportPersonSalaryExcel()"]');
    if (btnExportExcel) {
        console.log("พบปุ่ม Export Excel");
        btnExportExcel.onclick = function(e) {
            e.preventDefault();
            console.log("คลิกปุ่ม Export Excel");
            
            if (typeof exportPersonSalaryExcel === 'function') {
                exportPersonSalaryExcel(personId);
            } else {
                console.error("ไม่พบฟังก์ชัน exportPersonSalaryExcel");
                alert("ไม่พบฟังก์ชัน exportPersonSalaryExcel กรุณาตรวจสอบการโหลดไฟล์ JavaScript");
            }
            
            return false;
        };
    }
    
    // ตั้งค่าปุ่ม Export PDF
    const btnExportPdf = document.querySelector('.modal-footer button[onclick="exportPersonSalaryPDF()"]');
    if (btnExportPdf) {
        console.log("พบปุ่ม Export PDF");
        btnExportPdf.onclick = function(e) {
            e.preventDefault();
            console.log("คลิกปุ่ม Export PDF");
            
            if (typeof exportPersonSalaryPDF === 'function') {
                exportPersonSalaryPDF(personId);
            } else {
                console.error("ไม่พบฟังก์ชัน exportPersonSalaryPDF");
                alert("ไม่พบฟังก์ชัน exportPersonSalaryPDF กรุณาตรวจสอบการโหลดไฟล์ JavaScript");
            }
            
            return false;
        };
    }
    
    // ตั้งค่าปุ่มแก้ไข
    const btnEdit = document.querySelector('.modal-footer button[onclick="editSavedSalary()"]');
    if (btnEdit) {
        console.log("พบปุ่มแก้ไข");
        btnEdit.onclick = function(e) {
            e.preventDefault();
            console.log("คลิกปุ่มแก้ไข");
            
            if (typeof editSavedSalary === 'function') {
                editSavedSalary();
            } else {
                console.error("ไม่พบฟังก์ชัน editSavedSalary");
                alert("ไม่พบฟังก์ชัน editSavedSalary กรุณาตรวจสอบการโหลดไฟล์ JavaScript");
            }
            
            return false;
        };
    }
}

/**
 * แสดงประวัติการเบิกเงิน
 * @param {Object} withdrawData - ข้อมูลการเบิกเงิน
 */
function displayWithdrawHistory(withdrawData) {
    console.log("กำลังแสดงประวัติการเบิกเงิน:", withdrawData);
    
    const historyContainer = document.getElementById("withdrawHistoryContainer");
    if (!historyContainer) {
        console.error("ไม่พบ element: withdrawHistoryContainer");
        return;
    }
    
    const historyBody = document.getElementById("withdrawHistoryBody");
    if (!historyBody) {
        console.error("ไม่พบ element: withdrawHistoryBody");
        return;
    }
    
    historyBody.innerHTML = "";
    
    if (withdrawData.history && withdrawData.history.length > 0) {
        historyContainer.style.display = "block";
        
        withdrawData.history.forEach(item => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${item.date}</td>
                <td class="text-end">${item.amount.toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
                <td>${item.note || "-"}</td>
            `;
            historyBody.appendChild(row);
        });
    } else {
        historyContainer.style.display = "none";
    }
}

/**
 * ฟังก์ชันแก้ไขข้อมูลเงินเดือน
 */
function editSavedSalary() {
    console.log("เรียกฟังก์ชัน editSavedSalary");
    
    const personId = window.currentPersonId || currentPersonId;
    if (!personId) {
        console.error("ไม่พบ ID ของพนักงาน");
        alert("ไม่พบ ID ของพนักงาน");
        return;
    }
    
    console.log("แก้ไขข้อมูลเงินเดือนของพนักงานรหัส:", personId);
    
    // ปิด modal รายละเอียด
    const modalElement = document.getElementById("salaryDetailsModal");
    if (!modalElement) {
        console.error("ไม่พบ Modal element: salaryDetailsModal");
        return;
    }
    
    const currentModal = bootstrap.Modal.getInstance(modalElement);
    if (currentModal) {
        currentModal.hide();
    }
    
    setTimeout(() => {
        // เปิด modal บันทึก
        openSalaryForm(personId);
    }, 500);
}

/**
 * ฟังก์ชันเปิดโมดัลบันทึกเงินเดือน
 * @param {string} personId - รหัสพนักงาน
 */
function openSalaryForm(personId) {
    console.log("เริ่มต้น openSalaryForm สำหรับ personId:", personId);
    
    // ล้างข้อมูลทั้งหมดก่อน
    clearSalaryForm();
    
    // กำหนดค่าเริ่มต้น
    const modalPersonIdEl = document.getElementById("modalPersonId");
    if (modalPersonIdEl) {
        modalPersonIdEl.value = personId;
    }
    
    const modalMonthEl = document.getElementById("modalMonth");
    if (modalMonthEl) {
        modalMonthEl.value = selectedMonth;
    }
    
    // ดึงข้อมูลเงินเดือน
    fetch(`/api/salary_info/${personId}/?month=${selectedMonth}`)
        .then((res) => {
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        })
        .then((salaryData) => {
            console.log("ได้รับข้อมูลเงินเดือน:", salaryData);
            
            // แสดงข้อมูลพื้นฐาน
            const modalPersonNameEl = document.getElementById("modalPersonName");
            if (modalPersonNameEl) {
                modalPersonNameEl.innerText = salaryData.name;
            }
            
            const salaryPerDayEl = document.getElementById("salaryPerDay");
            if (salaryPerDayEl) {
                salaryPerDayEl.innerText = salaryData.base_salary.toFixed(2);
            }
            
            const workDaysEl = document.getElementById("workDays");
            if (workDaysEl) {
                workDaysEl.innerText = salaryData.days_worked;
            }
            
            const commissionTotalEl = document.getElementById("commissionTotal");
            if (commissionTotalEl) {
                commissionTotalEl.innerText = salaryData.commission.toFixed(2);
            }
            
            const withdrawEl = document.getElementById("withdraw");
            if (withdrawEl) {
                withdrawEl.innerText = salaryData.withdraw.toFixed(2);
            }
            
            const fullWorkDaysFlagEl = document.getElementById("fullWorkDaysFlag");
            if (fullWorkDaysFlagEl) {
                fullWorkDaysFlagEl.value = salaryData.full_attendance ? "1" : "0";
            }
            
            const noAbsenceBonusEl = document.getElementById("noAbsenceBonus");
            if (noAbsenceBonusEl) {
                noAbsenceBonusEl.innerText = salaryData.attendance_bonus.toFixed(2);
            }
            
            const noAbsenceBonusLineEl = document.getElementById("noAbsenceBonusLine");
            if (noAbsenceBonusLineEl) {
                noAbsenceBonusLineEl.style.display = salaryData.full_attendance ? "block" : "none";
            }
            
            // ตรวจสอบเงินกู้
            checkAndShowLoanInfo(personId, salaryData);
            
            // คำนวณยอดรวม
            if (typeof recalculateNetTotal === 'function') {
                recalculateNetTotal();
            } else {
                console.error("ไม่พบฟังก์ชัน recalculateNetTotal");
            }
            
            // แสดง modal
            const salaryModalEl = document.getElementById("salaryModal");
            if (salaryModalEl) {
                const salaryModal = new bootstrap.Modal(salaryModalEl);
                salaryModal.show();
            } else {
                console.error("ไม่พบ Modal element: salaryModal");
            }
        })
        .catch((err) => {
            console.error("เกิดข้อผิดพลาดในการโหลดข้อมูลเงินเดือน:", err);
            alert("เกิดข้อผิดพลาดในการโหลดข้อมูลเงินเดือน: " + err.message);
        });
}

/**
 * ตรวจสอบและแสดงข้อมูลเงินกู้
 * @param {string} personId - รหัสพนักงาน
 * @param {Object} salaryData - ข้อมูลเงินเดือน
 */
function checkAndShowLoanInfo(personId, salaryData) {
    console.log("ตรวจสอบข้อมูลเงินกู้ของพนักงานรหัส:", personId);
    
    const hasLoan = salaryData.loan_payment && salaryData.loan_payment > 0;
    
    const loanMonthlyLineEl = document.getElementById("loan-monthly-line");
    const loanPaymentInputEl = document.getElementById("loanPaymentInput");
    const loanPaymentValueEl = document.getElementById("loanPaymentValue");
    const loanRemainingLineEl = document.getElementById("loan-remaining-line");
    const loanRemainingAmountEl = document.getElementById("loanRemainingAmount");
    
    if (hasLoan) {
        console.log("พบข้อมูลเงินกู้:", salaryData.loan_payment);
        
        if (loanMonthlyLineEl) {
            loanMonthlyLineEl.style.display = "block";
        }
        
        if (loanPaymentInputEl) {
            loanPaymentInputEl.value = salaryData.loan_payment.toFixed(2);
        }
        
        if (loanPaymentValueEl) {
            loanPaymentValueEl.value = salaryData.loan_payment.toFixed(2);
        }
        
        fetch(`/api/loan_summary/${personId}/?month=${selectedMonth}`)
            .then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP error! status: ${res.status}`);
                }
                return res.json();
            })
            .then(loanData => {
                console.log("ได้รับข้อมูลสรุปเงินกู้:", loanData);
                
                if (loanData.loan_remaining > 0) {
                    if (loanRemainingLineEl) {
                        loanRemainingLineEl.style.display = "block";
                    }
                    
                    if (loanRemainingAmountEl) {
                        loanRemainingAmountEl.innerText = loanData.loan_remaining.toFixed(2);
                    }
                }
                
                // คำนวณยอดรวมอีกครั้ง
                if (typeof recalculateNetTotal === 'function') {
                    recalculateNetTotal();
                }
            })
            .catch(err => {
                console.error("ไม่สามารถโหลดข้อมูลเงินกู้ได้:", err);
            });
    } else {
        console.log("ไม่พบข้อมูลเงินกู้");
        
        // ล้างและซ่อนฟิลด์เงินกู้
        if (loanMonthlyLineEl) {
            loanMonthlyLineEl.style.display = "none";
        }
        
        if (loanRemainingLineEl) {
            loanRemainingLineEl.style.display = "none";
        }
        
        if (loanPaymentInputEl) {
            loanPaymentInputEl.value = "";
        }
        
        if (loanPaymentValueEl) {
            loanPaymentValueEl.value = "0";
        }
        
        if (loanRemainingAmountEl) {
            loanRemainingAmountEl.innerText = "0.00";
        }
    }
}

/**
 * ล้างข้อมูลในฟอร์มบันทึกเงินเดือน
 */
function clearSalaryForm() {
    console.log("ล้างข้อมูลในฟอร์มบันทึกเงินเดือน");
    
    // ล้างข้อมูลการแสดงผล
    const elements = {
        "modalPersonName": "-",
        "salaryPerDay": "-",
        "workDays": "-",
        "commissionTotal": "-",
        "withdraw": "-",
        "netTotal": "-"
    };
    
    for (const [id, value] of Object.entries(elements)) {
        const element = document.getElementById(id);
        if (element) {
            element.innerText = value;
        }
    }
    
    // ซ่อนรายการโบนัส
    const noAbsenceBonusLineEl = document.getElementById("noAbsenceBonusLine");
    if (noAbsenceBonusLineEl) {
        noAbsenceBonusLineEl.style.display = "none";
    }
    
    const noAbsenceBonusEl = document.getElementById("noAbsenceBonus");
    if (noAbsenceBonusEl) {
        noAbsenceBonusEl.innerText = "-";
    }
    
    // ล้างค่า hidden fields
    const hiddenFields = {
        "baseSalary": "0",
        "commissionValue": "0",
        "bonusValue": "0",
        "deductionValue": "0",
        "ssAmount": "0",
        "loanPaymentValue": "0",
        "fullWorkDaysFlag": "0"
    };
    
    for (const [id, value] of Object.entries(hiddenFields)) {
        const element = document.getElementById(id);
        if (element) {
            element.value = value;
        }
    }
    
    // ล้างค่า form inputs
    const loanPaymentInputEl = document.getElementById("loanPaymentInput");
    if (loanPaymentInputEl) {
        loanPaymentInputEl.value = "";
    }
    
    const deductSocialSecurityEl = document.getElementById("deductSocialSecurity");
    if (deductSocialSecurityEl) {
        deductSocialSecurityEl.checked = false;
    }
    
    // ลบรายการเพิ่มเติม
    document.querySelectorAll('#incomeList .extra-item').forEach(item => item.remove());
    document.querySelectorAll('#deductList .extra-item').forEach(item => item.remove());
    
    // ลบแถว ปกส.
    const ssElement = document.getElementById("ss-line");
    if (ssElement) {
        ssElement.remove();
    }
    
    // ล้างข้อมูลเงินกู้
    const loanMonthlyLineEl = document.getElementById("loan-monthly-line");
    if (loanMonthlyLineEl) {
        loanMonthlyLineEl.style.display = "none";
    }
    
    const loanRemainingLineEl = document.getElementById("loan-remaining-line");
    if (loanRemainingLineEl) {
        loanRemainingLineEl.style.display = "none";
    }
    
    const loanRemainingAmountEl = document.getElementById("loanRemainingAmount");
    if (loanRemainingAmountEl) {
        loanRemainingAmountEl.innerText = "0.00";
    }
}