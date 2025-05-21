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
        console.log("withdrawData =", withdrawData);

        const savedDeductionEl = document.getElementById("savedDeduction");
        console.log("savedDeductionEl = ", savedDeductionEl);
        if (savedDeductionEl) {
            let totalWithdraw = parseFloat(withdrawData.total_amount || 0);
            savedDeductionEl.innerText = totalWithdraw.toLocaleString(undefined, {
                minimumFractionDigits: 2
            }) + " บาท";
        }

        const savedExtraItemsEl = document.getElementById("savedExtraItems");
        savedExtraItemsEl.innerHTML = "";
    
        if (salaryData.extra_income && salaryData.extra_income.length > 0) {
            savedExtraItemsEl.style.display = "block";
            salaryData.extra_income.forEach(item => {
                const row = document.createElement("div");
                row.className = "d-flex justify-content-between px-3 py-2 border-top";
                row.innerHTML = `
                    <span>${item.name}:</span>
                    <span>${Number(item.amount).toLocaleString(undefined, {minimumFractionDigits: 2})} บาท</span>
                `;
                savedExtraItemsEl.appendChild(row);
            });
        } else {
            savedExtraItemsEl.style.display = "none";
        }

        const savedDeductItemsEl = document.getElementById("savedExtraDeductItems");
        savedDeductItemsEl.innerHTML = "";
        
        if (salaryData.extra_expense && salaryData.extra_expense.length > 0) {
            savedDeductItemsEl.style.display = "block";
            salaryData.extra_expense.forEach(item => {
                const row = document.createElement("div");
                row.className = "d-flex justify-content-between px-3 py-2 border-top";
                row.innerHTML = `
                    <span>${item.name}:</span>
                    <span>${Number(item.amount).toLocaleString(undefined, {minimumFractionDigits: 2})} บาท</span>
                `;
                savedDeductItemsEl.appendChild(row);
            });
        } else {
            savedDeductItemsEl.style.display = "none";
        }
        
        // แสดงข้อมูลพื้นฐาน
        const personNameEl = document.getElementById("salaryPersonName");
        if (personNameEl && salaryData.name) {
            personNameEl.innerText = salaryData.name;
        }

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
            if (salaryData.bonus > 0) {
                savedBonusEl.innerText = salaryData.bonus.toLocaleString(undefined, { minimumFractionDigits: 2 }) + " บาท";
            } else {
                savedBonusEl.innerText = "";
            }
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

        // แสดงข้อมูลเงินกู้คงเหลือ - แก้ไขตรงนี้
        if (loanEl) {
            loanEl.classList.add("d-none");
            loanEl.classList.remove("d-flex");
            
            // ตรวจสอบให้แน่ใจว่า loanData มีค่า
            if (loanData && loanData.loan_remaining && Number(loanData.loan_remaining) > 0) {
                loanEl.classList.remove("d-none");
                loanEl.classList.add("d-flex");
                const savedLoanRemainingEl = document.getElementById("savedLoanRemaining");
                if (savedLoanRemainingEl) {
                    savedLoanRemainingEl.innerText = Number(loanData.loan_remaining).toLocaleString(undefined, {minimumFractionDigits: 2}) + " บาท";
                }
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

function updateExtraItemsJson() {
    const extraItems = [];
    document.querySelectorAll('#incomeList .extra-item').forEach(item => {
        const name = item.querySelector('.item-name')?.value || "-";
        const amount = parseFloat(item.querySelector('.item-amount')?.value || 0);
        if (amount !== 0) {
            extraItems.push({ name, amount });
        }
    });

    const jsonInput = document.getElementById("extraItemsJson");
    if (jsonInput) {
        jsonInput.value = JSON.stringify(extraItems);
    }
}
