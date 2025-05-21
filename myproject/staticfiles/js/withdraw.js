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

document.addEventListener("DOMContentLoaded", function () {
    const personSelect = document.getElementById("person");
    const monthInput = document.getElementById("month_filter");
    const historyBox = document.querySelector(".card-body.bg-light .mb-3.text-muted");
    const totalBox = document.getElementById("total-summary");

    function loadHistory() {
        const personId = personSelect.value;
        const selectedMonth = monthInput.value;
        
        if (!personId || !selectedMonth) {
            historyBox.innerHTML = "(ยังไม่มีการแสดงผล — จะแสดงเมื่อเลือกชื่อพนักงาน)";
            totalBox.innerText = "0";
            return;
        }

        // ส่ง fee_status=0 เพื่อดึงเฉพาะรายการเบิกเงิน
        fetch(`/api/fee_history/${personId}/?month=${selectedMonth}&fee_status=0`)
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    if (data.data.length === 0) {
                        historyBox.innerHTML = "<em>ไม่พบประวัติการเบิก</em>";
                    } else {                        
                        // เรียงลำดับตามวันที่
                        data.data.sort((a, b) => new Date(a.date.split('/').reverse().join('/')) - new Date(b.date.split('/').reverse().join('/')));
            
                        let html = "<ul class='list-group small'>";
                        data.data.forEach(item => {
                            html += `
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    <div>
                                        <span>${item.date}</span> - <span>${item.amount.toLocaleString()} บาท</span>
                                        <br><span class="text-muted small">${item.description}</span>
                                    </div>
                                    <button class="btn btn-sm btn-outline-danger ms-2" onclick="deleteFee(${item.id})">ลบ</button>
                                </li>
                            `;
                        });
                        html += "</ul>";
                        historyBox.innerHTML = html;
                    }
            
                    totalBox.innerText = data.total.toLocaleString();
                } else {
                    historyBox.innerHTML = "เกิดข้อผิดพลาด";
                    totalBox.innerText = "0";
                }
            })            
    }

    personSelect.addEventListener("change", loadHistory);
    monthInput.addEventListener("change", loadHistory);
});

function deleteFee(id) {
    if (!confirm("คุณแน่ใจหรือไม่ว่าต้องการลบรายการนี้?")) return;

    fetch(`/api/delete_fee/${id}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            alert("ลบเรียบร้อยแล้ว");
            document.getElementById("person").dispatchEvent(new Event("change")); // refresh list
        } else {
            alert("ลบไม่สำเร็จ");
        }
    })
    .catch(err => {
        console.error(err);
        alert("เกิดข้อผิดพลาด");
    });
}