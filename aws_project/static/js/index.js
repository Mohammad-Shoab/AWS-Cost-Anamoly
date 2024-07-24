document.addEventListener('DOMContentLoaded', function() {
    fetch('/services/')
        .then(response => response.json())
        .then(data => {
            const serviceSelect = document.getElementById('serviceSelect');
            data.services.forEach(service => {
                const option = document.createElement('option');
                option.value = service;
                option.textContent = service;
                serviceSelect.appendChild(option);
            });

            const weeklyServiceSelect = document.getElementById('weeklyServiceSelect');
            data.services.forEach(service => {
                const option = document.createElement('option');
                option.value = service;
                option.textContent = service;
                weeklyServiceSelect.appendChild(option);
            });

            const monthlyServiceSelect = document.getElementById('monthlyServiceSelect');
            data.services.forEach(service => {
                const option = document.createElement('option');
                option.value = service;
                option.textContent = service;
                monthlyServiceSelect.appendChild(option);
            });

            // Fetch initial data for graphs with the first service as default
            const defaultService = data.services[0];
            updateDailyGraph(defaultService);
            updateWeeklyGraph(defaultService);
            updateMonthlyGraph(defaultService);
        })
        .catch(error => console.error('Error fetching services:', error));
});

function updateDailyGraph(service) {
    const graphType = currentGraphType; // Use the current graph type
    fetch(`/daily_service/?service=${encodeURIComponent(service)}&graph_type=${graphType}`)
        .then(response => response.json())
        .then(data => {
            updateChartsService(data, graphType);
        })
        .catch(error => console.error('Error fetching daily service data:', error));
}

function updateWeeklyGraph(service) {
    const graphType = currentWeeklyGraphType; // Use the current graph type
    fetch(`/weekly_service/?service=${encodeURIComponent(service)}&graph_type=${graphType}`)
        .then(response => response.json())
        .then(data => {
            updateWeeklyChartsService(data, graphType);
        })
        .catch(error => console.error('Error fetching weekly service data:', error));
}

function updateMonthlyGraph(service) {
    const graphType = currentMonthlyGraphType; // Use the current graph type
    fetch(`/monthly_service/?service=${encodeURIComponent(service)}&graph_type=${graphType}`)
        .then(response => response.json())
        .then(data => {
            updateMonthlyChartsService(data, graphType);
        })
        .catch(error => console.error('Error fetching monthly service data:', error));
}

function updateGraphType() {
    const graphTypeToggle = document.getElementById('graphTypeToggle');
    const graphType = graphTypeToggle.checked ? 'line' : 'bar';
    currentGraphType = graphType; // Update the global variable
    const serviceSelect = document.getElementById('serviceSelect');
    const selectedService = serviceSelect.value;
    updateDailyGraph(selectedService); // Fetch and update the graph with the new type
}

function updateWeeklyGraphType() {
    const graphTypeToggle = document.getElementById('weeklyGraphTypeToggle');
    const graphType = graphTypeToggle.checked ? 'line' : 'bar';
    currentWeeklyGraphType = graphType; // Update the global variable
    const weeklyServiceSelect = document.getElementById('weeklyServiceSelect');
    const selectedService = weeklyServiceSelect.value;
    updateWeeklyGraph(selectedService); // Fetch and update the graph with the new type
}

function updateMonthlyGraphType() {
    const graphTypeToggle = document.getElementById('monthlyGraphTypeToggle');
    const graphType = graphTypeToggle.checked ? 'line' : 'bar';
    currentMonthlyGraphType = graphType; // Update the global variable
    const monthlyServiceSelect = document.getElementById('monthlyServiceSelect');
    const selectedService = monthlyServiceSelect.value;
    updateMonthlyGraph(selectedService); // Fetch and update the graph with the new type
}

function updateService() {
    const serviceSelect = document.getElementById('serviceSelect');
    const selectedService = serviceSelect.value;
    updateDailyGraph(selectedService);
}

function updateWeeklyService() {
    const serviceSelect = document.getElementById('weeklyServiceSelect');
    const selectedService = serviceSelect.value;
    updateWeeklyGraph(selectedService);
}

function updateMonthlyService() {
    const serviceSelect = document.getElementById('monthlyServiceSelect');
    const selectedService = serviceSelect.value;
    updateMonthlyGraph(selectedService);
}


// Fetch data from the server
fetch('/data')
    .then(response => response.json())
    .then(data => updateCharts(data, 'bar')) // Default to bar graph
    .catch(error => console.error('Error fetching data:', error));

fetch('/daily_service/')
    .then(response => response.json())
    .then(data => updateChartsService(data, 'bar')) // Default to bar graph
    .catch(error => console.error('Error fetching data:', error));

// Fetch weekly data from the server
fetch('/weekly')
    .then(response => response.json())
    .then(weekly => updateWeeklyCharts(weekly))
    .catch(error => console.error('Error fetching weekly data:', error));

fetch('/weekly_service/')
    .then(response => response.json())
    .then(weekly => updateWeeklyCharts_service(weekly))
    .catch(error => console.error('Error fetching weekly data:', error));

// Fetch monthly data from the server
fetch('/monthly')
    .then(response => response.json())
    .then(monthly => updateMonthlyCharts(monthly))
    .catch(error => console.error('Error fetching monthly data:', error));

fetch('/monthly_service/')
    .then(response => response.json())
    .then(monthly => updateMonthlyCharts_service(monthly))
    .catch(error => console.error('Error fetching monthly data:', error));

function updateGraphType() {
    const graphTypeToggle = document.getElementById('graphTypeToggle');
    const graphType = graphTypeToggle.checked ? 'line' : 'bar';
    currentGraphType = graphType; // Update the global variable
    updateCharts(chartData, graphType);
    updateChartsService(chartDataService, graphType);  // Ensure this is defined globally
}

function updateWeeklyGraphType() {
    const graphTypeToggle = document.getElementById('weeklyGraphTypeToggle');
    const graphType = graphTypeToggle.checked ? 'line' : 'bar';
    currentWeeklyGraphType = graphType; // Update the global variable
    updateWeeklyCharts(chartDataWeekly, graphType);
    updateWeeklyChartsService(chartDataWeeklyService, graphType); // Ensure this is defined globally
}

function updateMonthlyGraphType() {
    const graphTypeToggle = document.getElementById('monthlyGraphTypeToggle');
    const graphType = graphTypeToggle.checked ? 'line' : 'bar';
    currentMonthlyGraphType = graphType; // Update the global variable
    updateMonthlyCharts(chartDataMonthly, graphType);
    updateMonthlyChartsService(chartDataMonthlyService, graphType); // Ensure this is defined globally
}

let chartData; // Declare a global variable to store chart data
let chartDataService; // Declare a global variable to store service-specific chart data
let chartDataWeekly; // Declare a global variable to store weekly chart data
let chartDataWeeklyService; // Declare a global variable to store weekly service-specific chart data
let chartDataMonthly; // Declare a global variable to store monthly chart data
let chartDataMonthlyService; // Declare a global variable to store monthly service-specific chart data
let currentGraphType = 'bar'; // Global variable to track current graph type
let currentWeeklyGraphType = 'bar'; // Global variable to track current weekly graph type
let currentMonthlyGraphType = 'bar'; // Global variable to track current monthly graph type

// Function to update charts with fetched data
function updateCharts(data, graphType = 'bar') {
    chartData = data; // Store data globally for reuse

    const labels = data.labels;
    const datasets = Object.entries(data.data).map(([service, costs], i) => ({
        label: service,
        data: costs,
        fill: false,
        borderColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
        tension: 0.1,
        borderWidth: 2,
        pointRadius: 5,
        pointBackgroundColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
        pointBorderColor: '#fff',
        pointHoverRadius: 7,
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
    }));

    if (window.dailyGraph1Instance) {
        window.dailyGraph1Instance.destroy();
    }

    window.dailyGraph1Instance = new Chart(document.getElementById('dailyGraph1'), {
        type: graphType,
        data: {
            labels: labels,
            datasets: datasets.map((dataset, i) => ({
                label: dataset.label,
                data: dataset.data,
                fill: false,
                tension: 0.1,
                borderWidth: 2,
                pointRadius: 5,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#000',
                pointHoverRadius: 7,
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#000',
            }))
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Cost Trend of Top 5 Services Over Last 7 Days',
                fontSize: 20
            },
            tooltips: {
                mode: 'index',
                intersect: false,
            },
            hover: {
                mode: 'nearest',
                intersect: true
            },
            scales: {
                xAxes: [{
                    ticks: {
                        maxRotation: 0,
                        minRotation: 0,
                        autoSkip: false,
                    }
                }],
                yAxes: [{
                    ticks: {
                        beginAtZero: true
                    }
                }]
            },
            legend: {
                labels: {
                    fontSize: 15,
                    usePointStyle: true
                }
            }
        }
    });
}

function updateService() {
    const serviceSelect = document.getElementById('serviceSelect');
    const selectedService = serviceSelect.value;
    updateDailyGraph(selectedService);
}

// Function to update service-specific charts with fetched data
function updateChartsService(data, graphType = 'bar') {
    chartDataService = data; // Store data globally for reuse

    const labels = data.labels;
    const datasets = Object.entries(data.data).map(([service, costs], i) => ({
        label: service,
        data: costs,
        fill: false,
        borderColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
        tension: 0.1,
        borderWidth: 2,
        pointRadius: 5,
        pointBackgroundColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
        pointBorderColor: '#fff',
        pointHoverRadius: 7,
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
    }));

    if (window.dailyGraph2Instance) {
        window.dailyGraph2Instance.destroy();
    }

    window.dailyGraph2Instance = new Chart(document.getElementById('dailyGraph2'), {
        type: graphType,
        data: {
            labels: labels,
            datasets: datasets.map((dataset, i) => ({
                label: dataset.label,
                data: dataset.data,
                fill: false,
                tension: 0.1,
                borderWidth: 2,
                pointRadius: 5,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#000',
                pointHoverRadius: 7,
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#000',
            }))
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Cost Trend of AWS CloudHSM Over Last 7 Days',
                fontSize: 20
            },
            tooltips: {
                mode: 'index',
                intersect: false,
            },
            hover: {
                mode: 'nearest',
                intersect: true
            },
            scales: {
                xAxes: [{
                    ticks: {
                        maxRotation: 0,
                        minRotation: 0,
                        autoSkip: false,
                    }
                }],
                yAxes: [{
                    ticks: {
                        beginAtZero: true
                    }
                }]
            },
            legend: {
                labels: {
                    fontSize: 15,
                    usePointStyle: true
                }
            }
        }
    });
}

// Function to update charts with fetched data
function updateWeeklyCharts(data, graphType = 'bar') {
    chartDataWeekly = data; // Store data globally for reuse

    const labels = data.labels.map(label => {
        // Split label into two lines at a space (customize as needed)
        return label.includes(' ') ? label.split(' ') : label;
    });
    const datasets = Object.entries(data.data).map(([service, costs], i) => ({
        label: service,
        data: costs,
        fill: false,
        borderColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
        tension: 0.1,
        borderWidth: 2,
        pointRadius: 5,
        pointBackgroundColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
        pointBorderColor: '#fff',
        pointHoverRadius: 7,
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
    }));

    // Destroy existing chart instances if they exist
    if (window.weeklyGraph1Instance) {
        window.weeklyGraph1Instance.destroy();
    }

    // Chart 1: Weekly Graph 1 (Cost Trend of Top 5 Services Over Last 4 Weeks)
    window.weeklyGraph1Instance = new Chart(document.getElementById('weeklyGraph1'), {
        type: graphType,
        data: {
            labels: labels,
            datasets: datasets.map((dataset, i) => ({
                label: dataset.label,
                data: dataset.data,
                fill: false,
                tension: 0.1,
                borderWidth: 2,
                pointRadius: 5,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#000',
                pointHoverRadius: 7,
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#000',
            }))
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Cost Trend of Top 5 Services Over Last 4 Weeks',
                fontSize: 20
            },
            tooltips: {
                mode: 'index',
                intersect: false,
            },
            hover: {
                mode: 'nearest',
                intersect: true
            },
            scales: {
                xAxes: [{
                    ticks: {
                        maxRotation: 0, // Keep labels straight
                        minRotation: 0,
                        autoSkip: false, // Prevent labels from being skipped
                    }
                }],
                yAxes: [{
                    ticks: {
                        beginAtZero: true
                    }
                }]
            },
            legend: {
                labels: {
                    fontSize: 15,
                    usePointStyle: true
                }
            }
        }
    });
}

function updateWeeklyService() {
    const serviceSelect = document.getElementById('weeklyServiceSelect');
    const selectedService = serviceSelect.value;
    updateWeeklyGraph(selectedService);
}

// Function to update weekly service-specific charts with fetched data
function updateWeeklyChartsService(data, graphType = 'bar') {
    chartDataWeeklyService = data; // Store data globally for reuse

    const labels = data.labels.map(label => {
        // Split label into two lines at a space (customize as needed)
        return label.includes(' ') ? label.split(' ') : label;
    });
    const datasets = Object.entries(data.data).map(([service, costs], i) => ({
        label: service,
        data: costs,
        fill: false,
        borderColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
        tension: 0.1,
        borderWidth: 2,
        pointRadius: 5,
        pointBackgroundColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
        pointBorderColor: '#fff',
        pointHoverRadius: 7,
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
    }));

    if (window.weeklyGraph2Instance) {
        window.weeklyGraph2Instance.destroy();
    }

    // Chart 4: Weekly Graph 2 (Sample Data)
    window.weeklyGraph2Instance = new Chart(document.getElementById('weeklyGraph2'), {
        type: graphType,
        data: {
            labels: labels,
            datasets: datasets.map((dataset, i) => ({
                label: dataset.label,
                data: dataset.data,
                fill: false,
                tension: 0.1,
                borderWidth: 2,
                pointRadius: 5,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#000',
                pointHoverRadius: 7,
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#000',
            }))
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Cost Trend of Top 5 Services Over Last 4 Weeks',
                fontSize: 20
            },
            tooltips: {
                mode: 'index',
                intersect: false,
            },
            hover: {
                mode: 'nearest',
                intersect: true
            },
            scales: {
                xAxes: [{
                    ticks: {
                        maxRotation: 0, // Keep labels straight
                        minRotation: 0,
                        autoSkip: false, // Prevent labels from being skipped
                    }
                }],
                yAxes: [{
                    ticks: {
                        beginAtZero: true
                    }
                }]
            },
            legend: {
                labels: {
                    fontSize: 15,
                    usePointStyle: true
                }
            }
        }
    });
}

// Function to update charts with fetched data
function updateMonthlyCharts(data, graphType = 'bar') {
    chartDataMonthly = data; // Store data globally for reuse

    const labels = data.labels;
    const datasets = Object.entries(data.data).map(([service, costs], i) => ({
        label: service,
        data: costs,
        fill: false,
        borderColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
        tension: 0.1,
        borderWidth: 2,
        pointRadius: 5,
        pointBackgroundColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
        pointBorderColor: '#fff',
        pointHoverRadius: 7,
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
    }));

    // Destroy existing chart instances if they exist
    if (window.monthlyGraph1Instance) {
        window.monthlyGraph1Instance.destroy();
    }

    // Chart 1: Monthly Graph 1 (Cost Trend of Top 5 Services Over Last 4 Months)
    window.monthlyGraph1Instance = new Chart(document.getElementById('monthlyGraph1'), {
        type: graphType,
        data: {
            labels: labels,
            datasets: datasets.map((dataset, i) => ({
                label: dataset.label,
                data: dataset.data,
                fill: false,
                tension: 0.1,
                borderWidth: 2,
                pointRadius: 5,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#000',
                pointHoverRadius: 7,
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#000',
            }))
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Cost Trend of Top 5 Services Over Last 4 Months',
                fontSize: 20
            },
            tooltips: {
                mode: 'index',
                intersect: false,
            },
            hover: {
                mode: 'nearest',
                intersect: true
            },
            scales: {
                xAxes: [{
                    ticks: {
                        maxRotation: 0, // Keep labels straight
                        minRotation: 0,
                        autoSkip: false, // Prevent labels from being skipped
                    }
                }],
                yAxes: [{
                    ticks: {
                        beginAtZero: true
                    }
                }]
            },
            legend: {
                labels: {
                    fontSize: 15,
                    usePointStyle: true
                }
            }
        }
    });
}

function updateMonthlyService() {
    const serviceSelect = document.getElementById('monthlyServiceSelect');
    const selectedService = serviceSelect.value;
    updateMonthlyGraph(selectedService);
}

// Function to update monthly service-specific charts with fetched data
function updateMonthlyChartsService(data, graphType = 'bar') {
    chartDataMonthlyService = data; // Store data globally for reuse

    const labels = data.labels;
    const datasets = Object.entries(data.data).map(([service, costs], i) => ({
        label: service,
        data: costs,
        fill: false,
        borderColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
        tension: 0.1,
        borderWidth: 2,
        pointRadius: 5,
        pointBackgroundColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
        pointBorderColor: '#fff',
        pointHoverRadius: 7,
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: `hsl(${i * 360 / 5}, 100%, 50%)`,
    }));

    if (window.monthlyGraph2Instance) {
        window.monthlyGraph2Instance.destroy();
    }

    // Chart 6: Monthly Graph 2 (Sample Data)
    window.monthlyGraph2Instance = new Chart(document.getElementById('monthlyGraph2'), {
        type: graphType,
        data: {
            labels: labels,
            datasets: datasets.map((dataset, i) => ({
                label: dataset.label,
                data: dataset.data,
                fill: false,
                tension: 0.1,
                borderWidth: 2,
                pointRadius: 5,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#000',
                pointHoverRadius: 7,
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#000',
            }))
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Cost Trend of Top 5 Services Over Last 4 Months',
                fontSize: 20
            },
            tooltips: {
                mode: 'index',
                intersect: false,
            },
            hover: {
                mode: 'nearest',
                intersect: true
            },
            scales: {
                xAxes: [{
                    ticks: {
                        maxRotation: 0, // Keep labels straight
                        minRotation: 0,
                        autoSkip: false, // Prevent labels from being skipped
                    }
                }],
                yAxes: [{
                    ticks: {
                        beginAtZero: true
                    }
                }]
            },
            legend: {
                labels: {
                    fontSize: 15,
                    usePointStyle: true
                }
            }
        }
    });
}

function toggleCron() {
    var isChecked = document.getElementById("cron-toggle").checked;
    fetch('/toggle-cron', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ isChecked: isChecked }),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}