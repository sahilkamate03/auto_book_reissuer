document.querySelector('form').addEventListener('submit', function () {
    document.getElementById('register-div').innerHTML = `
    <button type="button" class="btn btn-primary btn-block mb-4" id="register-button" data-bs-toggle="modal" data-bs-target="#exampleModal" disabled>
    <span id="spinner" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
    Submitting
    </button>
    `;
});

function reloadPage() {
    location.reload(true); // Pass true to force a reload from the server
}