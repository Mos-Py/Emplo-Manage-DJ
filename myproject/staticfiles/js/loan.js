document.addEventListener("DOMContentLoaded", function () {
    const personSelect = document.querySelector('select[name="person"]');
    const historyBox = document.querySelector("#loan-history-box");
    const balanceBox = document.querySelector("#loan-balance-box");

    window.loadLoanHistory = function() {
        const personId = personSelect.value;
        if (!personId) {
            historyBox.innerHTML = "<p class='text-muted'>(กรุณาเลือกพนักงาน)</p>";
            balanceBox.innerText = "0";
            return;
        }

        fetch(`/api/loan_history/${personId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    let html = "<ul class='list-group small'>";
                    if (data.data.length === 0) {
                        html += "<li class='list-group-item text-center text-muted'>ไม่พบข้อมูล</li>";
                    } else {
                        data.data.forEach(item => {
                            let isClosed = item.remaining_amount <= 0;

                            html += `
                                <li class="list-group-item ${isClosed ? 'list-group-item-success' : ''}">
                                    <div class="d-flex justify-content-between align-items-start">
                                        <div>
                                            ${item.date} - กู้ ${item.amount.toLocaleString()} บาท
                                            <br><small>คงเหลือ: ${item.remaining_amount.toLocaleString()} บาท</small>
                                            <br><small>ผ่อนเดือนละ: ${item.installment_amount.toLocaleString()} บาท</small>
                                            <br><small class="text-muted">${item.description}</small>
                                            ${isClosed ? `<div class="badge bg-success mt-1">ปิดหนี้แล้ว</div>` : ''}
                                        </div>
                                        <div>
                                            <button type="button" class="btn btn-sm btn-outline-danger ms-1" onclick="deleteLoan(${item.id})">ลบรายการ</button>
                                        </div>
                                    </div>
                                </li>
                            `;
                        });
                    }
                    html += "</ul>";
                    
                    // เพิ่มปุ่มลบประวัติทั้งหมด
                    if (data.data.length > 0) {
                        html += `
                            <div class="text-center mt-3">
                                <button type="button" class="btn btn-danger" onclick="deleteAllLoans(${personId})">
                                    <i class="fas fa-trash-alt"></i> ลบประวัติเงินกู้ทั้งหมด
                                </button>
                            </div>
                        `;
                    }
                    
                    historyBox.innerHTML = html;
                    balanceBox.innerText = data.total_remaining.toLocaleString();
                }
            });
    }

    personSelect.addEventListener("change", loadLoanHistory);
    
    // โหลดข้อมูลตอนเริ่มต้น
    if (personSelect.value) {
        loadLoanHistory();
    }
});

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

// ฟังก์ชันสำหรับลบรายการเงินกู้ทั้งรายการ
function deleteLoan(loanId) {
    if (!confirm("คุณแน่ใจหรือไม่ว่าต้องการลบ 'รายการเงินกู้' นี้?")) return;

    fetch(`/api/delete_loan/${loanId}/`, {
        method: "DELETE",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "Content-Type": "application/json",
        },
    })
    .then(res => {
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
    })
    .then(data => {
        if (data.status === "success") {
            alert("ลบรายการเงินกู้เรียบร้อยแล้ว");
            window.loadLoanHistory();
        } else {
            alert(data.message || "เกิดข้อผิดพลาด");
        }
    })
    .catch(err => {
        console.error("Error:", err);
        alert("เกิดข้อผิดพลาดในการลบรายการเงินกู้");
    });
}

// ฟังก์ชันสำหรับลบประวัติเงินกู้ทั้งหมดของพนักงานคนนี้
function deleteAllLoans(personId) {
    if (!confirm("คุณแน่ใจหรือไม่ว่าต้องการลบ 'ประวัติเงินกู้ทั้งหมด' ของพนักงานคนนี้?")) return;
    if (!confirm("คำเตือน: การกระทำนี้ไม่สามารถย้อนกลับได้! ยืนยันอีกครั้ง?")) return;

    fetch(`/api/delete_all_loans/${personId}/`, {
        method: "DELETE",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "Content-Type": "application/json",
        },
    })
    .then(res => {
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
    })
    .then(data => {
        if (data.status === "success") {
            alert("ลบประวัติเงินกู้ทั้งหมดเรียบร้อยแล้ว");
            window.loadLoanHistory();
        } else {
            alert(data.message || "เกิดข้อผิดพลาด");
        }
    })
    .catch(err => {
        console.error("Error:", err);
        alert("เกิดข้อผิดพลาดในการลบประวัติเงินกู้ทั้งหมด");
    });
}