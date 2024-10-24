const form = document.getElementById('changeForm');
const resultsDiv = document.getElementById('results');

form.addEventListener('submit', function (e) {
    e.preventDefault();
    const formData = new FormData(form);
    
    fetch('/process', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        resultsDiv.innerHTML = '';
        for (const [changeNumber, result] of Object.entries(data)) {
            resultsDiv.innerHTML += `<p><strong>${changeNumber}</strong>: ${result}</p>`;
        }
    })
    .catch(error => console.error('Error:', error));
});
