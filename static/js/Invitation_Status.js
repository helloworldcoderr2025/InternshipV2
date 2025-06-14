document.addEventListener('DOMContentLoaded', () => {
    const select = $('#companySelect');
    const resultBox = document.getElementById('inviteResults');

    select.select2({
        placeholder: "Search companies...",
        allowClear: true
    });

    select.on('change', async function () {
        const selectedCompanies = $(this).val();
        try {
            const response = await axios.post('/fetching_company_invitation_status/', {
                company_ids: selectedCompanies
            });
            console.log(response);
            renderResults(response.data.results);
        } catch (error) {
            console.error("Error fetching status", error);
            resultBox.innerHTML = `<p>Error fetching data.</p>`;
        }
    });

    function renderResults(results) {
        resultBox.innerHTML = '';
        results.forEach(({ company_id, name, invited, dates, reminders, response_status }) => {
            const block = document.createElement('div');
            block.className = 'status-block';
            block.innerHTML = `<h4>${name}</h4>`;
            if (!invited) {
                block.innerHTML += `
                    <p>Status: ❌ Not Invited</p>
                    <button onclick="openModal('${company_id}', 'invitation')">📨 Send Invitation</button>
                `;
            } else {
                block.innerHTML += `
                    <p>Status: ✅ Invited on ${dates.join(', ')}</p>
                    <p>Reminders Sent: ${reminders}</p>
                    <p>Response: ${response_status || '🕒 Waiting for Response'}</p>
                    <button onclick="openModal('${company_id}', 'reminder')">🔁 Send Reminder</button>
                    <button onclick="openModal('${company_id}', 'change_date')">✏️ Change Date</button>
                `;
            }

            resultBox.appendChild(block);
        });
    }
});

function openModal(companyId, mode) {
    document.getElementById('modalCompanyId').value = companyId;
    document.getElementById('modalMode').value = (mode === 'change_date') ? 'invitation' : mode;  // We treat it like new invitation
    document.getElementById('invitationDateGroup').style.display = (mode === 'invitation' || mode === 'change_date') ? 'block' : 'none';

    axios.post('/get_email_preview/', {
        company_id: companyId,
        mode: 'invitation'
    }).then(res => {
        document.getElementById('emailContent').value = res.data.email;
        document.getElementById('overlay').style.display = 'block';
        document.getElementById('emailModal').style.display = 'block';
    });
}


function closeModal() {
    document.getElementById('overlay').style.display = 'none';
    document.getElementById('emailModal').style.display = 'none';
}
document.getElementById('emailForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const companyId = document.getElementById('modalCompanyId').value;
    const mode = document.getElementById('modalMode').value;
    const content = document.getElementById('emailContent').value;
    const invitedDate = document.getElementById('invitationDate').value;
    const selectedCompanies = $('#companySelect').val(); 
    try {
        await axios.post('/send_email/', { 
            company_id: companyId, 
            mode, 
            email: content, 
            invited_date: invitedDate 
        });
        alert("Mail sent!");
        closeModal();
        if (selectedCompanies.length > 0) {
            const response = await axios.post('/fetching_company_invitation_status/', {
                company_ids: selectedCompanies
            });
            console.log(response);
            renderResults(response.data.results);  
        }
    } catch (err) {
        console.log("I got this");
        alert("Failed to send mail.");
    }
});

