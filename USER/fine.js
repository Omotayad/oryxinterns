document.addEventListener('DOMContentLoaded', () => {
    const itemNameSearchInput = document.getElementById('itemNameSearch');
    const itemNameSuggestions = document.getElementById('itemNameSuggestions');
    const itemNameInput = document.getElementById('itemName');
    const predictionResult = document.getElementById('predictionResult');
    const predictionSpan = document.getElementById('prediction');
    const form = document.getElementById('predictionForm');
    const downloadPredictionsButton = document.getElementById('downloadPredictions');

    let itemNames = [];
    let salesTrendChart;

    function getAuthHeaders() {
        const token = localStorage.getItem('authToken');
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }

    // Fetch item names from the JSON file
    fetch('item_name.json')
        .then((response) => response.json())
        .then((data) => {
            itemNames = data;
        })
        .catch((error) => console.error('Error:', error));

    itemNameSearchInput.addEventListener('input', () => {
        const searchTerm = itemNameSearchInput.value.toLowerCase();
        const filteredItemNames = itemNames.filter((itemName) =>
            itemName.toLowerCase().includes(searchTerm)
        );

        itemNameSuggestions.innerHTML = '';
        itemNameSuggestions.classList.remove('hidden');

        filteredItemNames.forEach((itemName) => {
            const suggestion = document.createElement('div');
            suggestion.textContent = itemName;
            suggestion.classList.add(
                'px-4',
                'py-2',
                'cursor-pointer',
                'hover:bg-gray-200'
            );
            suggestion.addEventListener('click', () => {
                itemNameInput.value = itemName;
                itemNameSearchInput.value = itemName;
                document.getElementById('itemName').value = itemName;
                itemNameSuggestions.classList.add('hidden');
            });
            itemNameSuggestions.appendChild(suggestion);
        });

        if (filteredItemNames.length === 0) {
            itemNameSuggestions.classList.add('hidden');
        }
    });

    itemNameSearchInput.addEventListener('blur', () => {
        setTimeout(() => {
            itemNameSuggestions.classList.add('hidden');
        }, 200);
    });

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        const formData = {
            itemname: document.getElementById('itemName').value,
            doctype: document.getElementById('doctype').value,
            linetotal: parseFloat(document.getElementById('lineTotal').value),
            year: parseInt(document.getElementById('year').value),
            quantity: parseFloat(document.getElementById('quantity').value),
            itemcost: parseFloat(document.getElementById('itemCost').value),
        };

        console.log('Form Data:', formData);

        const missingFields = Object.entries(formData)
            .filter(([key, value]) => {
                if (key === 'itemname' || key === 'doctype') {
                    return value === '' || value === null;
                } else {
                    return isNaN(value);
                }
            })
            .map(([key]) => key);

        if (missingFields.length > 0) {
            alert(`Please fill out the following fields: ${missingFields.join(', ')}`);
            return;
        }

        const formDataJSON = JSON.stringify(formData);
        fetch("http://127.0.0.1:5001/predict", {
            method: "POST",
            body: formDataJSON,
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeaders()
            },
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then((data) => {
                if (data.error) {
                    console.error('Error:', data.error);
                } else {
                    predictionSpan.textContent = data.prediction;
                    predictionResult.classList.remove('hidden');
                    document.getElementById('noPrediction').classList.add('hidden');
                    updateCharts(data.salesTrend);
                }
            })
            .catch((error) => {
                console.error('Error:', error);
                if (error.message === 'Network response was not ok') {
                    alert('Authentication failed. Please log in again.');
                    window.location.href = 'login.html';
                }
            });
    });


    downloadPredictionsButton.addEventListener('click', () => {
        fetch('http://127.0.0.1:5001/download_predictions', {
            headers: getAuthHeaders()
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.blob();
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'predictions.xlsx';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message === 'Network response was not ok') {
                    alert('Authentication failed. Please log in again.');
                    window.location.href = 'login.html';
                }
            });
    });

    function initializeCharts() {
        const salesTrendCtx = document.getElementById('salesTrendChart').getContext('2d');
        salesTrendChart = new Chart(salesTrendCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Sales',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Year'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Total Sales'
                        }
                    }
                }
            }
        });
    }

    function updateCharts(salesTrend) {
        salesTrendChart.data.labels = salesTrend.year;
        salesTrendChart.data.datasets[0].data = salesTrend.total_sales;
        salesTrendChart.update();
    }

    initializeCharts();
});