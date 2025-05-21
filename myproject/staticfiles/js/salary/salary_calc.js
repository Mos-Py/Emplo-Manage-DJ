// คำนวณยอดรวมใหม่
function recalculateNetTotal() {
    const salary = parseFloat(document.getElementById("salaryPerDay")?.innerText.replace(/,/g, '') || 0);
    const days = parseFloat(document.getElementById("workDays")?.innerText || 0);
    const commission = parseFloat(document.getElementById("commissionTotal")?.innerText.replace(/,/g, '') || 0);
    const withdraw = parseFloat(document.getElementById("withdraw")?.innerText.replace(/,/g, '') || 0);
    const ssChecked = document.getElementById("deductSocialSecurity")?.checked;
    const loanPayment = parseFloat(document.getElementById("loanPaymentInput")?.value || 0);

    // รายได้เพิ่มเติม (พิเศษ)
    let additionalIncome = 0;
    document.querySelectorAll('input[name="extra_income_amount[]"]').forEach(el => {
        additionalIncome += parseFloat(el.value || 0);
    });

    // รายจ่ายเพิ่มเติม (รวมจากทั้ง name และ class)
    let additionalDeduct = 0;
    document.querySelectorAll('input[name="extra_deduct_amount[]"]').forEach(el => {
        additionalDeduct += parseFloat(el.value || 0);
    });
    document.querySelectorAll('#expenseList .expense-amount').forEach(input => {
        additionalDeduct += parseFloat(input.value || 0);
    });

    // เงินเดือนพื้นฐาน
    const base = salary * days;

    // โบนัสมาทำงานครบ
    const isFull = parseInt(document.getElementById("fullWorkDaysFlag")?.value || "0") === 1;
    const bonusForFull = isFull ? salary : 0;

    // ประกันสังคม (5% ของ base)
    const ss = ssChecked ? (base * 0.05) : 0;

    // รวมรายจ่ายทั้งหมด
    const totalDeduct = withdraw + ss + loanPayment + additionalDeduct;

    // รายได้รวม = base + คอม + พิเศษ + โบนัสครบวัน
    const net = base + commission + additionalIncome + bonusForFull - totalDeduct;

    // อัปเดตค่าแสดงผล
    document.getElementById("noAbsenceBonus").innerText = bonusForFull.toLocaleString(undefined, { minimumFractionDigits: 0 });
    document.getElementById("noAbsenceBonusLine").style.display = isFull ? "block" : "none";
    document.getElementById("baseSalary").value = base;
    document.getElementById("commissionValue").value = commission;
    document.getElementById("bonusValue").value = additionalIncome + bonusForFull;
    document.getElementById("deductionValue").value = totalDeduct;
    document.getElementById("ssAmount").value = ss;
    document.getElementById("netTotal").innerText = net.toLocaleString(undefined, { minimumFractionDigits: 2 });

    // แสดง/ซ่อนช่องประกันสังคม
    updateSSDisplay(ssChecked, ss);
}



// อัปเดตการแสดงรายการ ปกส.
/**
 * อัปเดตการแสดงผลรายการ ปกส.
 * @param {boolean} checked - สถานะการเลือก
 * @param {number} ss - ยอดเงิน ปกส.
 */
function updateSSDisplay(checked, ss) {
    const ssElement = document.getElementById("ss-line");
    
    if (checked) {
        if (!ssElement) {
            // สร้างรายการใหม่
            const ssEl = document.createElement("div");
            ssEl.id = "ss-line";
            ssEl.className = "mb-3";
            ssEl.innerHTML = `
                <div class="d-flex justify-content-between">
                    <div>ปกส. (5%):</div>
                    <div>${ss.toFixed(2)} บาท</div>
                </div>
            `;
            document.getElementById("deductList").appendChild(ssEl);
        } else {
            // อัปเดตรายการที่มีอยู่
            ssElement.innerHTML = `
                <div class="d-flex justify-content-between">
                    <div>ปกส. (5%):</div>
                    <div>${ss.toFixed(2)} บาท</div>
                </div>
            `;
        }
    } else {
        // ลบรายการ
        if (ssElement) ssElement.remove();
    }
}

// อัปเดตข้อมูลเงินกู้
function updateLoanPayment() {
    const loanPaymentInput = document.getElementById("loanPaymentInput");
    const loanPayment = parseFloat(loanPaymentInput?.value || 0);
    
    // เก็บค่าไว้ในฟิลด์ hidden
    document.getElementById("loanPaymentValue").value = loanPayment.toString();
    
    // คำนวณยอดรวมใหม่
    recalculateNetTotal();
}


// อัปเดตการหัก ปกส.
function updateSocialSecurityDeduction() {
    recalculateNetTotal();
}

// เพิ่มรายการรายรับ
function addIncomeItem(name = "", amount = 0) {
    const container = document.getElementById("incomeList");

    const row = document.createElement("div");
    row.className = "mb-3 extra-item";

    row.innerHTML = `
        <div class="input-group input-group-sm mb-2">
            <input type="text" name="extra_income_name[]" class="form-control item-name" placeholder="ชื่อรายรับ">
            <input type="number" name="extra_income_amount[]" class="form-control text-end item-amount" placeholder="จำนวนเงิน" 
                   onchange="recalculateNetTotal()" onkeyup="recalculateNetTotal()" step="0.01">
            <span class="input-group-text">บาท</span>
        </div>
        <div class="d-flex justify-content-end gap-2">
            <button type="button" class="btn btn-sm btn-outline-primary" onclick="saveItem(this)">
                <i class="fas fa-check me-1"></i> บันทึก
            </button>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeItem(this)">
                <i class="fas fa-trash me-1"></i> ลบ
            </button>
        </div>
    `;

    container.appendChild(row);

    // ✅ ต้องดึง input หลังจากใส่ innerHTML แล้ว
    const nameInput = row.querySelector('.item-name');
    const amountInput = row.querySelector('.item-amount');

    nameInput.value = name;
    amountInput.value = amount;

    [nameInput, amountInput].forEach(el => el.addEventListener("input", updateExtraItemsJson));

    updateExtraItemsJson();
}

function addExpenseItem(name = "", amount = 0) {
    const container = document.getElementById("expenseList");

    const row = document.createElement("div");
    row.className = "mb-3 extra-expense";

    row.innerHTML = `
        <div class="input-group input-group-sm mb-2">
            <input type="text" class="form-control expense-name" placeholder="ชื่อรายจ่าย">
            <input type="number" class="form-control text-end expense-amount" placeholder="จำนวนเงิน" step="0.01">
            <span class="input-group-text">บาท</span>
        </div>
        <div class="d-flex justify-content-end gap-2">
            <button type="button" class="btn btn-sm btn-outline-primary" onclick="saveItem(this)">
                <i class="fas fa-check me-1"></i> บันทึก
            </button>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="this.closest('.extra-expense').remove(); updateExtraExpensesJson(); recalculateNetTotal();">
                <i class="fas fa-trash me-1"></i> ลบ
            </button>
        </div>
    `;

    container.appendChild(row);

    const nameInput = row.querySelector('.expense-name');
    const amountInput = row.querySelector('.expense-amount');

    nameInput.value = name;
    amountInput.value = amount;

    [nameInput, amountInput].forEach(el => {
        el.addEventListener("input", () => {
            row.querySelector('.btn-outline-primary').disabled = false;
            updateExtraExpensesJson();
            recalculateNetTotal();
        });
    });

    // เริ่มต้น disable ปุ่มบันทึกไว้ก่อน
    row.querySelector('.btn-outline-primary').disabled = true;

    updateExtraExpensesJson();
    recalculateNetTotal();
}

// เพิ่มรายการรายจ่าย
function addDeductItem() {
    const container = document.getElementById("deductList");
    const row = document.createElement("div");
    row.className = "mb-3 extra-item";
    row.innerHTML = `
        <div class="input-group input-group-sm mb-2">
            <input type="text" name="extra_deduct_name[]" class="form-control" placeholder="ชื่อรายจ่าย">
            <input type="number" name="extra_deduct_amount[]" class="form-control text-end" placeholder="จำนวนเงิน" 
                   onchange="recalculateNetTotal()" onkeyup="recalculateNetTotal()" step="0.01">
            <span class="input-group-text">บาท</span>
        </div>
        <div class="d-flex justify-content-end gap-2">
            <button type="button" class="btn btn-sm btn-outline-primary" onclick="saveItem(this)">
                <i class="fas fa-check me-1"></i> บันทึก
            </button>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeItem(this)">
                <i class="fas fa-trash me-1"></i> ลบ
            </button>
        </div>
    `;
    container.appendChild(row);
}

/**
 * บันทึกรายการ
 * @param {HTMLElement} btn - ปุ่มที่คลิก
 */
function saveItem(btn) {
    btn.classList.remove("btn-outline-primary");
    btn.classList.add("btn-success");
    btn.disabled = true;
    btn.innerHTML = `<i class="fas fa-check me-1"></i> บันทึกแล้ว`;
    
    // ปิดการแก้ไขในฟิลด์ input
    const parentItem = btn.closest(".extra-item, .extra-expense");
    parentItem.querySelectorAll("input").forEach(input => {
        input.readOnly = true;
    });
    updateExtraItemsJson?.();
    updateExtraExpensesJson?.();
    recalculateNetTotal?.();
}

/**
 * ลบรายการ
 * @param {HTMLElement} btn - ปุ่มที่คลิก
 */
function removeItem(btn) {
    const item = btn.closest(".extra-item");
    item.remove();
    recalculateNetTotal();
}

function updateExtraExpensesJson() {
    const data = [];
    document.querySelectorAll("#expenseList .extra-expense").forEach(row => {
        const name = row.querySelector(".expense-name")?.value || "";
        const amount = parseFloat(row.querySelector(".expense-amount")?.value || 0);
        if (amount !== 0) {
            data.push({ name, amount });
        }
    });
    const input = document.getElementById("extraExpensesJson");
    if (input) {
        input.value = JSON.stringify(data);
    }
}