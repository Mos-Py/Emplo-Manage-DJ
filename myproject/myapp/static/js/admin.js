/**
 * JavaScript สำหรับหน้า Admin Person - แสดง/ซ่อนฟิลด์ตามตำแหน่งที่เลือก
 */
(function($) {
    $(document).ready(function() {
        // ฟังก์ชันสำหรับแสดง/ซ่อนฟิลด์ concrete_mixer_numbers
        function toggleDriverFields() {
            const roleField = $('#id_Role');
            const isDriver = roleField.val() === 'Concrete Mixer Driver';
            const driverFieldRow = $('.form-row.field-concrete_mixer_numbers');
            
            if (isDriver) {
                driverFieldRow.show();
            } else {
                driverFieldRow.hide();
                // เคลียร์ค่าเมื่อเปลี่ยนตำแหน่งเป็นอื่นที่ไม่ใช่คนขับรถโม่
                $('#id_concrete_mixer_numbers').val('');
            }
        }
        
        // เรียกใช้ฟังก์ชันเมื่อโหลดหน้า
        toggleDriverFields();
        
        // เรียกใช้ฟังก์ชันเมื่อมีการเปลี่ยนค่าในฟิลด์ Role
        $('#id_Role').on('change', toggleDriverFields);
    });
})(django.jQuery);