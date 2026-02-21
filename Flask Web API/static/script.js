let chart;
// Initialize chart
function initChart() {
    const ctx = document.getElementById('sensorChart').getContext('2d');

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],   // ✅ FIXED
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: [],
                    borderColor: '#FF6B6B',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: 'Humidity (%)',
                    data: [],
                    borderColor: '#4ECDC4',
                    backgroundColor: 'rgba(78, 205, 196, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { position: 'left' },
                y1: { position: 'right', grid: { drawOnChartArea: false } }
            }
        }
    });
}
async function fetchAndUpdateChart() {
    try {
        const response = await fetch('/api/sensor-data');
        const data = await response.json();

        const { timestamp, temperature, humidity,fire_status} = data;

        // Update sensor cards
        document.getElementById('tempValue').textContent =
            temperature.toFixed(2) + ' °C';

        document.getElementById('humidityValue').textContent =
            humidity.toFixed(2) + ' %';

        document.getElementById('fireStatus').textContent =
            fire_status == 1? "🚨": "🏡"
        // Add or remove the class based on fire status
        if (fire_status == 1) {
            document.querySelector('.fire-card').classList.add('fire-detected');
        } else {
            document.querySelector('.fire-card').classList.remove('fire-detected');
        }



        // Push new data
        chart.data.labels.push(timestamp);
        chart.data.datasets[0].data.push(temperature);
        chart.data.datasets[1].data.push(humidity);

        // Optional: limit points (keep last 20)
        const MAX_POINTS = 11;
        if (chart.data.labels.length > MAX_POINTS) {
            chart.data.labels.shift();
            chart.data.datasets.forEach(ds => ds.data.shift());
        }

        chart.update('none'); // smooth update
    } catch (error) {
        console.error('Error fetching sensor data:', error);
    }
}

// Toggle button and submit form
function toggleAndSubmit(name) {
    const form = document.getElementById('controlForm');

    // Handle threshold setting
    if (name === 'thresh') {
        const thresholdInput = document.getElementById('tempThreshold');
        const threshHidden = document.getElementById('thresh');
        const setBtn = document.querySelector('.set-btn');
        const threshold = thresholdInput.value;

        // Validate input
        if (!threshold || threshold < 0 || threshold > 100) {
            alert('Please enter a valid temperature between 0-100°C');
            return;
        }

        // Disable button
        setBtn.disabled = true;

        // Update hidden input
        threshHidden.value = threshold;

        // Send form data
        const formData = new FormData();
        formData.append('buzzer', document.getElementById('buzzer').value);
        formData.append('fun', document.getElementById('fun').value);
        formData.append('thresh', threshold);

        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            alert(`Threshold set to ${threshold}°C`);
            setBtn.disabled = false;
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error setting threshold');
            setBtn.disabled = false;
        });

        return;
    }

    // Handle buzzer and fan controls
    const input = document.getElementById(name);
    const button = document.getElementById(name + '-btn');

    // Disable buttons
    document.getElementById('buzzer-btn').disabled = true;
    document.getElementById('fun-btn').disabled = true;

    // Toggle the value
    const newValue = input.value === 'true' ? 'false' : 'true';
    input.value = newValue;

    // Update button appearance
    if (newValue === 'true') {
        button.classList.remove('btn-inactive');
        button.classList.add('btn-active');
        button.querySelector('.btn-status').textContent = 'ON';
    } else {
        button.classList.remove('btn-active');
        button.classList.add('btn-inactive');
        button.querySelector('.btn-status').textContent = 'OFF';
    }

    // Send form data
    const formData = new FormData();
    formData.append('buzzer', document.getElementById('buzzer').value);
    formData.append('fun', document.getElementById('fun').value);
    formData.append('thresh', document.getElementById('thresh').value);

    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        document.getElementById('buzzer-btn').disabled = false;
        document.getElementById('fun-btn').disabled = false;
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('buzzer-btn').disabled = false;
        document.getElementById('fun-btn').disabled = false;
    });
}

// Set today's date
document.getElementById('dateSelect').value = new Date().toISOString().split('T')[0];

function fetchData() {
    const date = document.getElementById('dateSelect').value;

    fetch(`/api/historical-data?date=${date}`)
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('tableBody');

            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="no-data">No data</td></tr>';
                return;
            }

            tbody.innerHTML = data.map(row => {
                const isFire = row.fire_status === 'True';
                return `
                    <tr>
                        <td>${row.hour}</td>
                        <td>${row.temperature}°C</td>
                        <td>${row.humidity}%</td>
                        <td class="${isFire ? 'fire-status-danger' : 'fire-status-safe'}">
                            ${isFire ? '🚨 DETECTED' : '✅ Safe'}
                        </td>
                    </tr>
                `;
            }).join('');
        });
}
// Initialize chart on page load
window.addEventListener('load', function() {
    initChart();
    // Fetch new data every 1 second
    setInterval(fetchAndUpdateChart, 5000);
});