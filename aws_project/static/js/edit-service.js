/**
 * Function to handle form submission
 */
document.addEventListener('DOMContentLoaded', function() {
    const editServiceForm = document.getElementById('edit-service-form');
    editServiceForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const inputs = editServiceForm.querySelectorAll('input[type="text"]');
        let decimalFields = [];
        let decimalFields1 = [];
        let negativeIntegerFields = [];
        let percentSymbolFields = [];
        let outOfRangeFields = [];
        let outOfRangeFields1 = [];
        let booleanFields = [];

        // Iterate over form inputs to perform validation
        inputs.forEach(function(input) {
            const fieldName = input.getAttribute('name');
            let value = input.value.trim();

            if (fieldName === 'Daily-Alert' || fieldName === 'Weekly-Alert' || fieldName === 'Monthly-Alert') {
                value = value.toLowerCase(); // Convert to lowercase
            }

            if (fieldName === 'Daily-Threshold-Percentage' || fieldName === 'Weekly-Threshold-Percentage' || fieldName === 'Monthly-Threshold-Percentage') {
                if (value.toLowerCase() === 'na') { // Check if value is 'NA' in any case
                    return; // Skip validation for 'NA'
                }
                if (isNaN(value) || value < 0) {
                    negativeIntegerFields.push(input);
                }
                if (value === '-0') {
                    negativeIntegerFields.push(input);
                }
                if (value < 0 || value > 100) {
                    outOfRangeFields.push(input);
                }
                if (!isNaN(value) && value.includes('.')) {
                    decimalFields.push(input);
                }
            }
            if (fieldName === 'Daily-Threshold-Value' || fieldName === 'Weekly-Threshold-Value' || fieldName === 'Monthly-Threshold-Value') {
                if (value.toLowerCase() === 'na') { // Check if value is 'NA' in any case
                    return; // Skip validation for 'NA'
                }
                if (isNaN(value) || value < 0) {
                    negativeIntegerFields.push(input);
                }
                if (value === '-0' || value === '-0.0' || value === '-0.00') {
                    negativeIntegerFields.push(input);
                }
                if (value < 0 || value > 1000000) {
                    outOfRangeFields1.push(input);
                }

                // Check if value has more than two decimal places
                if (value.includes('.')) {
                    const decimalPlaces = value.split('.')[1].length;
                    if (decimalPlaces > 2) {
                        decimalFields1.push(input);
                    }
                }

                // Convert value to a number and format it with two decimal places
                value = parseFloat(value);
                if (!isNaN(value)) {
                    input.value = value.toFixed(2);
                }
            }
        });

        // Display appropriate popups based on validation results    
        if (percentSymbolFields.length > 0) {
            const popupContainer = document.getElementById('percent-popup-container');
            popupContainer.style.display = 'block';
            return;
        }

        if (negativeIntegerFields.length > 0) {
            const popupContainer = document.getElementById('integer-popup-container');
            popupContainer.style.display = 'block';
            return;
        }

        if (outOfRangeFields.length > 0) {
            const popupContainer = document.getElementById('range-popup-container');
            popupContainer.style.display = 'block';
            return;
        }

        if (outOfRangeFields1.length > 0) {
            const popupContainer = document.getElementById('range-popup-container1');
            popupContainer.style.display = 'block';
            return;
        }

        if (decimalFields.length > 0) {
            const popupContainer = document.getElementById('popup-container');
            popupContainer.style.display = 'block';
            return;
        }

        if (decimalFields1.length > 0) {
            const popupContainer = document.getElementById('popup-container1');
            popupContainer.style.display = 'block';
            return;
        }

        // Submit the form if no validation errors
        editServiceForm.submit();
    });
});

// /**
//  * Function to round decimal fields to the nearest integer
//  * @param {boolean} round - Indicates whether to round or not
//  */
// function roundDecimalFields(round) {
//     const editServiceForm = document.getElementById('edit-service-form');
//     const decimalFields = editServiceForm.querySelectorAll('input[type="text"]');
//     decimalFields.forEach(function(field) {
//         const value = parseFloat(field.value);
//         if (!isNaN(value) && value < 0.5) {
//             field.value = round ? Math.round(value) : value;
//         } else if (!isNaN(value) && value >= 0.5) {
//             field.value = round ? Math.round(value) : value;
//         }
//     });
//     const popupContainer = document.getElementById('popup-container');
//     popupContainer.style.display = 'none';
//     // if (round) {
//     //     editServiceForm.submit();
//     // }
// }

/**
 * Function to round decimal fields to the nearest integer
 * @param {boolean} round - Indicates whether to round or not
 */
function roundDecimalFields(round) {
    const editServiceForm = document.getElementById('edit-service-form');
    const inputs = editServiceForm.querySelectorAll('input[type="text"]');
    inputs.forEach(function(field) {
        const fieldName = field.getAttribute('name');
        if (fieldName === 'Daily-Threshold-Percentage' || fieldName === 'Weekly-Threshold-Percentage' || fieldName === 'Monthly-Threshold-Percentage') {
            const value = parseFloat(field.value);
            if (!isNaN(value)) {
                field.value = round ? Math.round(value) : value;
            }
        }
    });
    const popupContainer = document.getElementById('popup-container');
    popupContainer.style.display = 'none';
}

/**
 * Function to round decimal fields to two decimal places
 * @param {boolean} round - Indicates whether to round or not
 */
function roundDecimalFields1(round) {
    const editServiceForm = document.getElementById('edit-service-form');
    const inputs = editServiceForm.querySelectorAll('input[type="text"]');
    inputs.forEach(function(field) {
        const fieldName = field.getAttribute('name');
        if (fieldName === 'Daily-Threshold-Value' || fieldName === 'Weekly-Threshold-Value' || fieldName === 'Monthly-Threshold-Value') {
            let value = parseFloat(field.value);
            if (!isNaN(value)) {
                // Add a small number to the value before rounding
                value = round ? (value + 0.00001).toFixed(2) : value;
                field.value = value;
            }
        }
    });
    const popupContainer = document.getElementById('popup-container1');
    popupContainer.style.display = 'none';
}

/**
 * Function to close popup container
 * @param {string} popupId - ID of the popup container to close
 */
function closePopup(popupId) {
    const popupContainer = document.getElementById(popupId);
    popupContainer.style.display = 'none';
}
