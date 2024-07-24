function validateForm() {
    var endDate = document.getElementById("end_date").value;
    if (endDate === "") {
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
    var table = document.getElementById("service-table-body");
    var rows = Array.from(table.rows);

    rows.sort(function(a, b) {
        var cellA = parseFloat(a.cells[columnIndex + 1].innerText) || 0; // +1 to account for the service name column
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