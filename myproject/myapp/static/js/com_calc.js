// com_calc.js - เวอร์ชันที่ปรับปรุงใหม่

// ตัวแปรเก็บเงื่อนไขหัวคิวทั้งหมด
const rules = [];

function calculateMoney(input) {
    const day = input.name.split("raw_queue_")[1];
    const value = parseInt(input.value) || 0;
    const moneyInput = document.querySelector(`input[name='money_earned_${day}']`);
    
    let money = 0;

    // เพิ่มการตรวจสอบว่า rules มีข้อมูลหรือไม่
    if (rules.length === 0) {
        moneyInput.value = "0.00";
        return;
    }

    // หาว่าค่าอยู่ในช่วงไหน
    for (const rule of rules) {
        if (value >= rule.min && value <= rule.max) {
            // ตรงนี้เปลี่ยนการคำนวณ - ใช้ค่า price โดยตรง ไม่ต้องคูณกับจำนวนหัวคิว
            money = rule.price;
            break;
        }
    }

    moneyInput.value = money.toFixed(2);
    
    // อัปเดตยอดรวมทั้งหมด
    updateTotals();
}

// อัปเดตยอดรวมทั้งหมด
function updateTotals() {
    let totalQueues = 0;
    let totalMoney = 0;
    
    // รวมจำนวนหัวคิว
    document.querySelectorAll('.queue-input').forEach(input => {
        const value = parseInt(input.value) || 0;
        totalQueues += value;
    });
    
    // รวมจำนวนเงิน
    document.querySelectorAll('.money-input').forEach(input => {
        const value = parseFloat(input.value) || 0;
        totalMoney += value;
    });
    
    // แสดงผลรวม
    document.getElementById('totalQueues').textContent = totalQueues;
    document.getElementById('totalMoney').textContent = totalMoney.toFixed(2) + ' บาท';
}

// ลบกฎเงื่อนไข
function removeRule(min, max, price) {
    const index = rules.findIndex(r => r.min === min && r.max === max && r.price === price);
    if (index !== -1) {
        rules.splice(index, 1);
        updateAllCalculations();
    }
}

// โหลดเงื่อนไขของเดือนปัจจุบัน
function loadConditionsOnPageLoad() {
    const selectedMonth = document.getElementById("month")?.value;
    if (!selectedMonth) return;

    fetch(`/load_queue_conditions/?month=${selectedMonth}`)
        .then(res => res.json())
        .then(data => {
            if (data.success && data.rules.length > 0) {
                applyConditions(data.rules);
            } else {
                // ถ้าไม่พบข้อมูล แสดงข้อความแจ้งเตือนให้ใช้ค่าเริ่มต้น
                if (confirm("ไม่พบเงื่อนไขหัวคิวของเดือนนี้ ต้องการใช้ค่าเริ่มต้นหรือไม่?")) {
                    loadDefaultConditions();
                }
            }
        })
        .catch(err => {
            console.error("โหลดเงื่อนไขล้มเหลว", err);
            // ถ้าเกิดข้อผิดพลาด ก็เสนอให้ใช้ค่าเริ่มต้น
            if (confirm("ไม่สามารถโหลดเงื่อนไขได้ ต้องการใช้ค่าเริ่มต้นหรือไม่?")) {
                loadDefaultConditions();
            }
        });
}
// โหลดเงื่อนไขเริ่มต้น
function loadDefaultConditions() {
    console.log("เริ่มฟังก์ชัน loadDefaultConditions");
    // ค่า default จากรูปภาพที่ให้มา
    const defaultRules = [
        { min: 40, max: 79, price: 20 },
        { min: 80, max: 99, price: 25 },
        { min: 100, max: 119, price: 30 },
        { min: 120, max: 139, price: 35 },
        { min: 140, max: 159, price: 40 },
        { min: 160, max: 179, price: 45 },
        { min: 180, max: 199, price: 50 },
        { min: 200, max: 219, price: 55 },
        { min: 220, max: 239, price: 60 },
        { min: 240, max: 999, price: 65 }
    ];

    if (confirm("ต้องการใช้ค่าหัวคิวเริ่มต้นหรือไม่?")) {
        console.log("defaultRules:", defaultRules);
        applyConditions(defaultRules);
    }
}
// โหลดเงื่อนไขจากเดือนก่อนหน้า
function loadPreviousMonthConditions() {
    const selectedMonth = document.getElementById("month")?.value;
    if (!selectedMonth) {
        alert("กรุณาเลือกเดือนก่อน");
        return;
    }

    if (confirm("ต้องการโหลดเงื่อนไขจากเดือนก่อนหน้าหรือไม่?")) {
        fetch(`/load_prev_queue_conditions/?month=${selectedMonth}`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (confirm(`ต้องการนำเงื่อนไขจากเดือน ${data.month} มาใช้หรือไม่?`)) {
                        applyConditions(data.rules);
                    }
                } else {
                    alert(data.message || "ไม่พบเงื่อนไขของเดือนก่อน");
                }
            })
            .catch(err => {
                console.error("Error loading conditions:", err);
                alert("โหลดข้อมูลล้มเหลว");
            });
    }
}

// แสดงรายการเงื่อนไขในหน้า
function applyConditions(fetchedRules) {
    rules.length = 0;
    document.getElementById("rule_list").innerHTML = "";

    for (const rule of fetchedRules) {
        rules.push(rule);

        const li = document.createElement("li");
        li.className = "list-group-item d-flex justify-content-between align-items-center";
        li.innerHTML = `${rule.min}-${rule.max} หัว = ${rule.price.toFixed(2)} บาท
            <button class="btn btn-sm btn-outline-danger" 
                    onclick="removeRule(${rule.min}, ${rule.max}, ${rule.price}); this.parentElement.remove()">
                ลบ
            </button>`;
        document.getElementById("rule_list").appendChild(li);
    }
    
    // คำนวณใหม่สำหรับทุก input
    updateAllCalculations();
}

// เพิ่มเงื่อนไขด้วยตนเอง
function addRule() {
    const min = parseInt(document.getElementById("min_queue").value);
    const max = parseInt(document.getElementById("max_queue").value);
    const price = parseFloat(document.getElementById("price_per_head").value);

    if (isNaN(min) || isNaN(max) || isNaN(price)) {
        alert("กรุณากรอกช่วงและราคาให้ครบ");
        return;
    }

    // ตรวจสอบว่า min ไม่มากกว่า max
    if (min > max) {
        alert("ค่าต่ำสุดต้องไม่มากกว่าค่าสูงสุด");
        return;
    }

    const rule = { min, max, price };
    rules.push(rule);

    const li = document.createElement("li");
    li.className = "list-group-item d-flex justify-content-between align-items-center";
    li.innerHTML = `${min}-${max} หัว = ${price.toFixed(2)} บาท
        <button class="btn btn-sm btn-outline-danger" 
                onclick="removeRule(${min}, ${max}, ${price}); this.parentElement.remove()">
            ลบ
        </button>`;
    document.getElementById("rule_list").appendChild(li);

    // เคลียร์ฟอร์มหลังจากเพิ่ม
    document.getElementById("min_queue").value = "";
    document.getElementById("max_queue").value = "";
    document.getElementById("price_per_head").value = "";
    
    // คำนวณใหม่สำหรับทุก input
    updateAllCalculations();
}

// คำนวณใหม่ทั้งหมด
function updateAllCalculations() {
    document.querySelectorAll('input[name^="raw_queue_"]').forEach(input => {
        calculateMoney(input);
    });
}

// บันทึกเงื่อนไขผ่าน AJAX
function saveConditionsAJAX() {
    const month = document.getElementById("month")?.value;
    if (!month) {
        alert("กรุณาเลือกเดือนก่อนบันทึกเงื่อนไข");
        return;
    }
    
    if (rules.length === 0) {
        alert("ไม่มีเงื่อนไขที่จะบันทึก");
        return;
    }

    // ตรวจสอบว่าเงื่อนไขไม่ทับซ้อนกัน
    const sortedRules = [...rules].sort((a, b) => a.min - b.min);
    for (let i = 1; i < sortedRules.length; i++) {
        if (sortedRules[i].min <= sortedRules[i-1].max) {
            alert("มีช่วงหัวคิวที่ทับซ้อนกัน กรุณาตรวจสอบอีกครั้ง");
            return;
        }
    }

    // ส่งข้อมูลไปยังเซิร์ฟเวอร์ผ่าน AJAX
    fetch("/save_queue_conditions/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({ month, rules })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("บันทึกเงื่อนไขเรียบร้อยแล้ว");
        } else {
            alert("เกิดข้อผิดพลาดในการบันทึก: " + data.message);
        }
    })
    .catch(err => {
        console.error("Error saving conditions:", err);
        alert("ไม่สามารถบันทึกเงื่อนไขได้");
    });
}

// ดึง CSRF token จาก cookie
function getCSRFToken() {
    const cookie = document.cookie.split(";").find(item => item.trim().startsWith("csrftoken="));
    return cookie ? cookie.split("=")[1] : "";
}

function confirmDeleteAllRules() {
    if (rules.length === 0) {
        alert("ไม่มีเงื่อนไขให้ลบ");
        return;
    }

    if (confirm("คุณแน่ใจหรือไม่ว่าต้องการลบเงื่อนไขทั้งหมด?\nการกระทำนี้ไม่สามารถยกเลิกได้!")) {
        deleteAllRules();
    }
}

// ฟังก์ชันลบเงื่อนไขทั้งหมดทั้งจาก UI และฐานข้อมูล
function deleteAllRules() {
    const month = document.getElementById("month")?.value;
    if (!month) {
        alert("กรุณาเลือกเดือนก่อน");
        return;
    }

    // ลบจาก UI
    rules.length = 0;
    document.getElementById("rule_list").innerHTML = "";

    // ส่งคำขอลบไปยังเซิร์ฟเวอร์
    fetch("/delete_all_queue_conditions/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({ month })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("ลบเงื่อนไขทั้งหมดเรียบร้อยแล้ว");
            // คำนวณใหม่หลังจากลบเงื่อนไข
            updateAllCalculations();
        } else {
            alert("เกิดข้อผิดพลาดในการลบเงื่อนไข: " + data.message);
        }
    })
    .catch(err => {
        console.error("Error deleting rules:", err);
        alert("ไม่สามารถลบเงื่อนไขได้");
    });
}

// Event เมื่อโหลดหน้า
document.addEventListener("DOMContentLoaded", function () {
    // ตั้งค่าให้ input "จำนวนหัวคิวดิบ" คำนวณอัตโนมัติ
    const rawInputs = document.querySelectorAll('input[name^="raw_queue_"]');
    rawInputs.forEach(input => {
        input.addEventListener("input", function () {
            calculateMoney(this);
        });
    });

    // โหลดเงื่อนไขของเดือนปัจจุบันเมื่อเข้า
    loadConditionsOnPageLoad();

    // คำนวณยอดรวมเมื่อเปิดหน้า
    updateTotals();
});