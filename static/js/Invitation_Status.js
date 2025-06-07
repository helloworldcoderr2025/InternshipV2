document.addEventListener('DOMContentLoaded', () => {
    const select = $('#companySelect');  
    const resultBox = document.getElementById('inviteResults');

    select.select2({
        placeholder: "Search companies...",
        allowClear: true
    });


    select.on('change', async function() {
 
        const selectedCompanies = $(this).val(); 

        try {
            const response = await axios.post('/fetching_company_invitation_status/', {
                company_ids: selectedCompanies
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const results = response.data.results;
            renderResults(results);
        } catch (error) {
            resultBox.innerHTML = `<p class="error">Error fetching data. Try again later.</p>`;
        
        }
    });

    function renderResults(results) {
        resultBox.innerHTML = '';
        results.forEach(({ name, invited, dates }) => {
            const block = document.createElement('div');
            block.className = 'status-block';

            if (invited) {
                block.innerHTML = `<strong>${name}</strong>: ✅ Invited on ${dates.join(', ')}`;
            } else {
                block.innerHTML = `<strong>${name}</strong>: ❌ Not Invited`;
            }

            resultBox.appendChild(block);
        });
    }
});
