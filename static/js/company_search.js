function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}
axios.defaults.headers.common['X-CSRFToken'] = getCSRFToken();
$(document).ready(function () {
    const select = $('#companySelect');
    const detailsDiv = document.getElementById('company-details');

    select.select2({
    placeholder: "Search for a company",
    allowClear: true
    });

    select.on('change', function () {
    const companyId = $(this).val();
    if (!companyId) {
        detailsDiv.innerHTML = '';
        return;
    }

    axios.get(`/api/company/${companyId}/`)
        .then(res => {
        const company = res.data;
        showCompanyDetails(company);
        })
        .catch(() => {
        detailsDiv.innerHTML = `<p>Error fetching company data.</p>`;
        });
    });

    function showCompanyDetails(company) {
    detailsDiv.innerHTML = `
        <h3>${company.name}</h3>
        <p><strong>Company-ID: </strong> ${company.company_id || ''}</p>
        <p><strong>Type Of Company: </strong> ${company.type_of_company || ''}</p>
        <p><strong>Job Profile: </strong> ${company.job_profile || ''}</p>
        <p><strong>Job Offer: </strong> ${company.job_offer || ''}</p>
        <p><strong>Package Offered: </strong> ${company.max_package_offered || ''}</p>
        <p><strong>Eligible Batches: </strong> ${company.eligible_passouts || ''}</p>
        <p><strong>HR Contact Email: </strong> ${company.hr_contact_email || ''}</p>
        <p><strong>HR Contact Phone Number: </strong>${company.hr_contact_phno || ''}</p>
        <p><strong>HR Contact Alternate: </strong>${company.hr_contact_alternate || ''}</p>
        <p><strong>Google Form link: </strong> ${company.google_form_link || ''}</p>
        <p><strong>Eligible Core Branch(es): </strong> ${company.eligible_core_branch || ''}</p>
        <p><strong>Eligible Non-core Branch(es): </strong> ${company.eligible_non_core_branch || ''}</p>
        <button onclick='editCompany(${JSON.stringify(company)})'>Edit</button>
        <button onclick="deleteCompany('${company.company_id}')">Delete</button>
    `;
    }

    window.editCompany = function (company) {
    detailsDiv.innerHTML = `
        <h3>Edit Company: ${company.name}</h3>
        <form id="editForm">
        <label>Company Name:</label>
        <input name="name" value="${company.name || ''}" disabled><br><br>

        <label>Type Of Company:</label>
        <input name="type_of_company" value="${company.type_of_company || ''}"><br><br>

        <label>Job Profile:</label>
        <input name="job_profile" value="${company.job_profile || ''}"><br><br>

        <label>Job Offer:</label>
        <input name="job_offer" value="${company.job_offer || ''}"><br><br>

        <label>Max Package Offered:</label>
        <input name="max_package_offered" value="${company.max_package_offered || ''}"><br><br>

        <label>Eligible Batches:</label>
        <input name="eligible_passouts" value="${company.eligible_passouts || ''}"><br><br>

        <label>HR Contact Email:</label>
        <input name="hr_contact_email" value="${company.hr_contact_email || ''}"><br><br>

        <label>HR Contact Phone Number:</label>
        <input name="hr_contact_phno" value="${company.hr_contact_phno || ''}"><br><br>

        <label>HR Contact Alternate:</label>
        <input name="hr_contact_alternate" value="${company.hr_contact_alternate || ''}"><br><br>

        <label>Google Form Link:</label>
        <input name="google_form_link" value="${company.google_form_link || ''}"><br><br>

        <label>Eligible Core Branch(es):</label>
        <input name="eligible_core_branch" value="${company.eligible_core_branch || ''}"><br><br>

        <label>Eligible Non-core Branch(es):</label>
        <input name="eligible_non_core_branch" value="${company.eligible_non_core_branch || ''}"><br><br>

        <button type="submit">Update</button>
        </form>
    `;

    document.getElementById('editForm').onsubmit = function(e) {
        if (!confirm("Are you sure to Update the Data?")) return;
        e.preventDefault();
        const formData = new FormData(this);
        const payload = {};
        formData.forEach((v, k) => payload[k] = v);

        axios.put(`/api/company/${company.company_id}/update/`, payload)
        .then(() => {
            alert('Updated successfully!');
            select.val(company.company_id).trigger('change'); 
        })
        .catch(() => alert('Failed to update company.'));
    }
    }


    window.deleteCompany = function (companyId) {
    if (!confirm("Are you sure to delete this company?")) return;

    axios.delete(`/api/company/${companyId}/delete/`)
        .then(() => {
        alert('Deleted successfully!');
        detailsDiv.innerHTML = '';
        select.val(null).trigger('change');
        })
        .catch(() => alert('Failed to delete company.'));
    }
});
const modal = document.getElementById("uploadModal");
const singleTab = document.getElementById("singleUploadTab");
const bulkTab = document.getElementById("bulkUploadTab");

document.getElementById("uploadBtn").onclick = () => {
    modal.style.display = "block";
    showTab('single');  
};

function closeModal() {
    modal.style.display = "none";
}

function showTab(tab) {
    singleTab.style.display = tab === 'single' ? 'block' : 'none';
    bulkTab.style.display = tab === 'bulk' ? 'block' : 'none';
}


window.onclick = function(event) {
    if (event.target === modal) {
    closeModal();
    }
};