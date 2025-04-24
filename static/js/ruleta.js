document.addEventListener('DOMContentLoaded', function() {
    var typeSelect = document.getElementById('bet_type');
    var numberField = document.getElementById('field_number');
    var colorField = document.getElementById('field_color');
    var parityField = document.getElementById('field_parity');
    var dozenField = document.getElementById('field_dozen');

    function updateFields() {
        numberField.style.display = (typeSelect.value === 'number') ? 'block' : 'none';
        colorField.style.display = (typeSelect.value === 'color') ? 'block' : 'none';
        parityField.style.display = (typeSelect.value === 'parity') ? 'block' : 'none';
        dozenField.style.display = (typeSelect.value === 'dozen') ? 'block' : 'none';
    }

    typeSelect.addEventListener('change', updateFields);
    updateFields(); // mostrar campos al cargar la página
});

