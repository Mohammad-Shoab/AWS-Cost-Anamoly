function validateForm() {
    var endDateValue = document.getElementById("end_date").value;
    if (endDateValue === "") {
        // Show the popup
        document.getElementById('validateFormPopup').style.display = 'block';
        return false;
    }
    return true;
}

function closePopup(popupId) {
    document.getElementById(popupId).style.display = 'none';
}

function sortTable(columnIndex, order) {
    var table = document.getElementById("usage-table-body");
    var rows = Array.from(table.rows);

    rows.sort(function(a, b) {
        var cellA = parseFloat(a.cells[columnIndex + 1].innerText) || 0; // +1 to account for the usage type column
        var cellB = parseFloat(b.cells[columnIndex + 1].innerText) || 0;

        if (order === 'asc') {
            return cellA - cellB;
        } else {
            return cellB - cellA;
        }
    });

    rows.forEach(function(row) {
        table.appendChild(row);
    });
}