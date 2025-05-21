$(document).ready(function() {
    // กำหนดค่า DataTable
    var table = $('#employee_table').DataTable({
        "language": {
            "search": "ค้นหา:",
            "lengthMenu": "แสดง _MENU_ รายการ",
            "info": "แสดงรายการ _START_ ถึง _END_ จากทั้งหมด _TOTAL_ รายการ",
            "infoEmpty": "ไม่พบรายการ",
            "infoFiltered": "(กรองจากทั้งหมด _MAX_ รายการ)",
            "zeroRecords": "ไม่พบรายการที่ค้นหา",
            "paginate": {
                "first": "หน้าแรก",
                "last": "หน้าสุดท้าย",
                "next": "ถัดไป",
                "previous": "ก่อนหน้า"
            }
        },
        "pageLength": 10,
        "responsive": true,
        "columnDefs": [
            { "orderable": false, "targets": 5 }  // ไม่ให้เรียงลำดับคอลัมน์การจัดการ
        ],
        "order": [[0, 'asc']],  // เรียงตามรหัสพนักงาน
        
        // แก้ไขการแสดงผลของ DOM elements
        "dom": "<'row align-items-center mb-3'<'col-sm-6 col-12 mb-2 mb-sm-0'l><'col-sm-6 col-12'f>>" +
               "<'row'<'col-sm-12'tr>>" +
               "<'row align-items-center mt-3'<'col-sm-5 col-12 mb-2 mb-sm-0 text-muted'i><'col-sm-7 col-12'p>>",
               
        // ปรับแต่งเพิ่มเติม
        "initComplete": function() {
            // จัดรูปแบบการแสดงจำนวนรายการต่อหน้า
            $('.dataTables_length select').addClass('form-select form-select-sm');
            
            // จัดรูปแบบช่องค้นหา
            $('.dataTables_filter input').addClass('form-control form-control-sm rounded-pill');
            $('.dataTables_filter input').attr('placeholder', 'ค้นหาพนักงาน...');
            $('.dataTables_filter label').contents().filter(function() {
                return this.nodeType === 3; // เลือกเฉพาะ Text Node
            }).remove(); // ลบข้อความ "ค้นหา:" ออก
            
            // เพิ่มไอคอนค้นหา
            $('.dataTables_filter label').prepend('<i class="fas fa-search position-absolute ms-3" style="top: 10px; opacity: 0.5;"></i>');
            $('.dataTables_filter input').css('padding-left', '2.2rem');
            $('.dataTables_filter label').css('position', 'relative');
            
            // แก้ไขการแสดงผลของปุ่ม pagination
            $('.dataTables_paginate').addClass('pagination-sm');
            
            // เรียกฟังก์ชันอัพเดทไอคอนเมื่อโหลดครั้งแรก
            updateSortIcons();
        },
        "drawCallback": function() {
            // อัพเดทไอคอนทุกครั้งที่ตารางถูกวาด (draw) ใหม่
            updateSortIcons();
        }
    });
    
    function updateSortIcons() {
        // แทนที่เนื้อหาภายใน th ด้วยข้อความเดิม + ไอคอนใหม่
        $('#employee_table thead th').each(function() {
            // เก็บข้อความเดิม (ไม่รวมไอคอน)
            var originalText = $(this).clone().children().remove().end().text().trim();
            
            // ล้างเนื้อหาเดิมทั้งหมด
            $(this).empty();
            
            // ใส่ข้อความเดิมกลับไป
            $(this).text(originalText);
            
            // เพิ่มไอคอนตามสถานะ
            if ($(this).hasClass('sorting_asc')) {
                $(this).append('<i class="fas fa-sort-up ms-2"></i>');
            } else if ($(this).hasClass('sorting_desc')) {
                $(this).append('<i class="fas fa-sort-down ms-2"></i>');
            } else if ($(this).hasClass('sorting')) {
                $(this).append('<i class="fas fa-sort ms-2 opacity-50"></i>');
            }
        });
    }
    
    // เพิ่ม event listener สำหรับการคลิกที่ header ของตาราง
    $('#employee_table thead th').on('click', function() {
        // รอสักครู่ให้ DataTable ประมวลผลการเรียงลำดับก่อน
        setTimeout(function() {
            updateSortIcons();
        }, 100);
    });
});