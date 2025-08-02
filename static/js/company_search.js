// Get CSRF token safely
function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}
axios.defaults.headers.common['X-CSRFToken'] = getCSRFToken();

$(document).ready(function () {
    const select = $('#companySelect');
    const detailsDiv = document.getElementById('company-details');
    const uploadBtn = document.getElementById('uploadBtn');

    // Initialize select2
    select.select2({
        placeholder: "Search for a company",
        allowClear: true
    });

    // Enhanced company selection handling
    select.on('change', function () {
        const companyId = $(this).val();
        if (!companyId) {
            detailsDiv.innerHTML = '';
            // Disable upload button when no company is selected
            if (uploadBtn) {
                uploadBtn.disabled = true;
                uploadBtn.style.opacity = '0.6';
            }
            return;
        }

        // Enable upload button when company is selected
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.style.opacity = '1';
        }

        axios.get(`/api/company/${companyId}/`)
            .then(res => {
                showCompanyDetails(res.data);
            })
            .catch(() => {
                detailsDiv.innerHTML = `<p style="color:red;">Error fetching company data.</p>`;
            });
    });

    // Initially disable upload button
    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.style.opacity = '0.6';
    }

    function showCompanyDetails(data) {
        const company = data; // fixed: data *is* the company
        const jobprofiles = data.jobprofiles || [];

        let html = `
            <h3>${company.name}  ( ID-${company.id} ) </h3>
            <p><strong>Primary Email:</strong> ${company.primary_email || ''}</p>
            <p><strong>Last Visited Year:</strong> ${company.last_visited_year || ''}</p>
        `;

        if (jobprofiles.length === 0) {
            html += `<p>No job profiles available for this company.</p>`;
        } else {
            jobprofiles.forEach(profile => {
                html += `
                    <hr>
                    <h4>Job Profile: ${profile.job_profile}</h4>
                    <p><strong>Type Of Company:</strong> ${profile.type_of_company || ''}</p>
                    <p><strong>Job Offer:</strong> ${profile.job_offer || ''}</p>
                    <p><strong>Max Package Offered:</strong> ${profile.max_package_offered || ''}</p>
                    <p><strong>Eligible Passouts:</strong> ${profile.eligible_passouts || ''}</p>
                    <p><strong>Eligible Core Branch:</strong> ${profile.eligible_core_branch || ''}</p>
                    <p><strong>Eligible Non-core Branch:</strong> ${profile.eligible_non_core_branch || ''}</p>
                    <p><strong>HR Contact Email:</strong> ${profile.hr_contact_email || ''}</p>
                    <p><strong>HR Contact Phone:</strong> ${profile.hr_contact_phno || ''}</p>
                    <p><strong>HR Contact Alternate:</strong> ${profile.hr_contact_alternate || ''}</p>
                    <p><strong>Google Form Link:</strong> ${profile.google_form_link || ''}</p>
                    <button onclick='editJobProfile(${JSON.stringify(profile).replace(/'/g, "\\'")})'>Edit Job Profile</button>
                    <button onclick="deleteJobProfile(${profile.id})">Delete Job Profile</button>
                `;
            });
        }

        html += `
            <button onclick="editCompany(${company.id}, '${company.name.replace(/'/g, "\\'")}')">Edit Company</button>
            <button onclick="deleteCompany(${company.id})">Delete Company</button>
        `;

        detailsDiv.innerHTML = html;
    }

    window.editCompany = function(companyId, name) {
        detailsDiv.innerHTML = `
            <h3>Edit Company: ${name}</h3>
            <form id="editCompanyForm">
                <label>Company Name:</label>
                <input name="name" value="${name}" disabled><br><br>

                <label>Primary Email:</label>
                <input name="primary_email"><br><br>

                <label>Last Visited Year:</label>
                <input name="last_visited_year"><br><br>

                <button type="submit">Update Company</button>
            </form>
        `;
        document.getElementById("uploadBtn").onclick = () => {
            const selectedId = select.val();
            const selectedName = $("#companySelect option:selected").text();
            if (!selectedId) {
                alert("Please select a company first.");
                return;
            }

            // Prefill fields
            document.getElementById('prefilledCompanyId').value = selectedId;
            document.getElementById('prefilledCompanyName').value = selectedName;

            modal.style.display = "block";
            showTab('single');
        };

        document.getElementById('editCompanyForm').onsubmit = function(e) {
            e.preventDefault();
            if (!confirm("Update company?")) return;
            const formData = new FormData(this);
            const payload = {};
            formData.forEach((v, k) => payload[k] = v);

            axios.put(`/api/company/${companyId}/update/`, payload)
                .then(() => {
                    alert('Company updated!');
                    select.val(companyId).trigger('change');
                })
                .catch(() => alert('Failed to update company.'));
        };
    }

    window.deleteCompany = function(companyId) {
        if (!confirm("Delete this company?")) return;

        axios.delete(`/api/company/${companyId}/delete/`)
            .then(() => {
                alert('Deleted!');
                detailsDiv.innerHTML = '';
                select.val(null).trigger('change');
            })
            .catch(() => alert('Failed to delete.'));
    }

    window.editJobProfile = function(profile) {
        detailsDiv.innerHTML = `
            <h3>Edit Job Profile: ${profile.job_profile}</h3>
            <form id="editProfileForm">
                <label>Job Profile:</label>
                <input name="job_profile" value="${profile.job_profile || ''}"><br><br>

                <label>Type Of Company:</label>
                <input name="type_of_company" value="${profile.type_of_company || ''}"><br><br>

                <label>Job Offer:</label>
                <input name="job_offer" value="${profile.job_offer || ''}"><br><br>

                <label>Max Package Offered:</label>
                <input name="max_package_offered" value="${profile.max_package_offered || ''}"><br><br>

                <label>Eligible Passouts:</label>
                <input name="eligible_passouts" value="${profile.eligible_passouts || ''}"><br><br>

                <label>Eligible Core Branch:</label>
                <input name="eligible_core_branch" value="${profile.eligible_core_branch || ''}"><br><br>

                <label>Eligible Non-core Branch:</label>
                <input name="eligible_non_core_branch" value="${profile.eligible_non_core_branch || ''}"><br><br>

                <label>HR Contact Email:</label>
                <input name="hr_contact_email" value="${profile.hr_contact_email || ''}"><br><br>

                <label>HR Contact Phone:</label>
                <input name="hr_contact_phno" value="${profile.hr_contact_phno || ''}"><br><br>

                <label>HR Contact Alternate:</label>
                <input name="hr_contact_alternate" value="${profile.hr_contact_alternate || ''}"><br><br>

                <label>Google Form Link:</label>
                <input name="google_form_link" value="${profile.google_form_link || ''}"><br><br>

                <button type="submit">Update Job Profile</button>
            </form>
        `;

        document.getElementById('editProfileForm').onsubmit = function(e) {
            e.preventDefault();
            if (!confirm("Update job profile?")) return;
            const formData = new FormData(this);
            const payload = {};
            formData.forEach((v, k) => payload[k] = v);

            axios.put(`/api/jobprofile/${profile.id}/update/`, payload)
                .then(() => {
                    alert('Job profile updated!');
                    select.val(profile.company).trigger('change');
                })
                .catch(() => alert('Failed to update job profile.'));
        };
    }

    window.deleteJobProfile = function(profileId) {
        if (!confirm("Delete this job profile?")) return;

        axios.delete(`/api/jobprofile/${profileId}/delete/`)
            .then(() => {
                alert('Deleted!');
                select.trigger('change'); // reload
            })
            .catch(() => alert('Failed to delete.'));
    }

    // === Modal controls ===
    const modal = document.getElementById("uploadModal");
    const modalOverlay = document.getElementById("modalOverlay");
    const singleTab = document.getElementById("singleUploadTab");
    const bulkTab = document.getElementById("bulkUploadTab");

    document.getElementById("uploadBtn").onclick = () => {
        const selectedId = select.val();
        const selectedName = $("#companySelect option:selected").text();
        
        if (!selectedId) {
            alert("Please select a company first.");
            return;
        }

        // Prefill fields
        document.getElementById('prefilledCompanyId').value = selectedId;
        document.getElementById('prefilledCompanyName').value = selectedName;

        modal.style.display = "block";
        modalOverlay.style.display = "block";
        showTab('single');
    };

    window.closeModal = () => { 
        modal.style.display = "none"; 
        modalOverlay.style.display = "none";
    }

    window.showTab = (tab) => {
        singleTab.style.display = (tab === 'single') ? 'block' : 'none';
        bulkTab.style.display = (tab === 'bulk') ? 'block' : 'none';
    }

    window.onclick = function(event) {
        if (event.target === modal || event.target === modalOverlay) closeModal();
    };
});
