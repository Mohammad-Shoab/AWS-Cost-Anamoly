# AWS Budget and Cost Anomaly Detection

## Overview

This web application is designed for AWS Budget and Cost Anomaly detection. It allows users to view, edit, and manage data related to AWS services. The application provides functionalities to select a service, view its data in tabular form, and edit individual entries.

## Pages

### Home Page

The home page presents users with a dropdown menu containing a list of AWS services. Users can select a service from the dropdown menu.

### Collection Page

After selecting a service from the home page, users are redirected to the collection page. This page displays the data of the selected service in a tabular format. Each entry in the table includes an "Edit" option in the last column, allowing users to modify the data.

### Edit Page

Upon clicking the "Edit" button for a specific entry on the collection page, users are redirected to the edit page. Here, they can modify the data of that particular entry. The edit page consists of the following fields:

1. **UsageTypes**
2. **Daily-Alert**
3. **Daily-Threshold**
4. **Weekly-Alert**
5. **Weekly-Threshold**
6. **Monthly-Alert**
7. **Monthly-Threshold**

### Field Validation

- All input values are trimmed of extra spaces before updating the data in the database.
- The application performs various validation checks on the input fields:
  - If the '%' symbol is provided with the value in the Daily-Threshold, Weekly-Threshold, or Monthly-Threshold fields, a popup message appears: "Invalid input: Please enter the value without '%' symbol."
  - If the input value is negative, a popup message appears: "Invalid input: Please enter a positive integer."
  - If the input value is not between 0 and 100, a popup message appears: "Invalid input: Please enter a number between 0 and 100."
  - If the input value is a decimal, a popup message appears: "Decimal value detected in one or more fields. Do you want to round them to the nearest integer?" Users can choose to round the value or keep it as it is.

### Additional Features

- The application provides a dropdown menu containing true or false options for fields like Daily-Alert, Weekly-Alert, and Monthly-Alert. The update value (true or false) is stored in lowercase.

## Technologies Used

- **Flask**: Web framework for building the application.
- **MongoDB**: Database for storing and managing data.
- **HTML/CSS/JavaScript**: Frontend technologies for user interface and interactivity.

## Setup and Installation

1. Clone the repository:

    ```bash
    git clone <repository-url>
    ```
    
2. Navigate to the project directory:

    ```bash
    cd Web-App
    ```
    
3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```
    
4. Run the Flask application:

    ```bash
    python app.py
    ```
    
5. Access the application in your web browser at http://localhost:5000.

## Contributing

Contributions are welcome! If you find any bugs or have suggestions for improvements, please open an issue or submit a pull request.
