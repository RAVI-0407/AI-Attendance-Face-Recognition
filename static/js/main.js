/* main.js  –  AttendAI Frontend Logic */

/* ── Photo Preview (Registration) ────────────────────────────────── */
function previewPhoto(input) {
  const preview = document.getElementById('preview') ||
                  document.getElementById('photoPreview');
  if (!preview) return;
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = e => {
      preview.src           = e.target.result;
      preview.style.display = 'block';
    };
    reader.readAsDataURL(input.files[0]);
  }
}

/* ── Auto-dismiss flash messages after 4 s ───────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    document.querySelectorAll('.flash').forEach(el => {
      el.style.opacity    = '0';
      el.style.transition = 'opacity 0.4s';
      setTimeout(() => el.remove(), 400);
    });
  }, 4000);

  /* ── Registration form loading state ─────────────────────────── */
  const regForm   = document.getElementById('regForm');
  const submitBtn = document.getElementById('submitBtn');

  if (regForm && submitBtn) {
    regForm.addEventListener('submit', () => {
      submitBtn.disabled     = true;
      submitBtn.textContent  = 'Registering…';
    });
  }
});
