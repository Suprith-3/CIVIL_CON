const API_BASE_URL = window.location.origin + '/api';
const IMG_BASE_URL = window.location.origin;

export function initLogin(role) {
    const form = document.getElementById('loginForm');
    const errorBox = document.getElementById('errorBox');
    const spinner = document.getElementById('spinner');
    const btnText = document.getElementById('btnText');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');

    // WARMUP: Wake up Render backend as soon as user starts focusing fields
    const warmup = () => {
        fetch(`${API_BASE_URL.replace('/api', '')}/health`).catch(() => {});
        emailInput.removeEventListener('focus', warmup);
        passwordInput.removeEventListener('focus', warmup);
    };
    emailInput.addEventListener('focus', warmup);
    passwordInput.addEventListener('focus', warmup);

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const email = emailInput.value;
        const password = passwordInput.value;

        // Reset state
        errorBox.style.display = 'none';
        spinner.style.display = 'inline-block';
        btnText.textContent = 'Verifying...';
        form.querySelector('button').disabled = true;

        const startTime = performance.now();

        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Login failed');
            }

            // Speed: Store tokens and full profile immediately
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            localStorage.setItem('user_type', data.user.user_type);
            localStorage.setItem('user_id', data.user.id);
            localStorage.setItem('user_email', email);
            localStorage.setItem('user_name', data.user.full_name || 'User');
            localStorage.setItem('user_pic', data.user.profile_pic_url || '');

            const endTime = performance.now();
            console.log(`Login roundtrip took: ${Math.round(endTime - startTime)}ms`);

            // Redirect instantly
            window.location.href = `../dashboards/${data.user.user_type}-dashboard.html`;

        } catch (err) {
            errorBox.textContent = err.message;
            errorBox.style.display = 'block';
            spinner.style.display = 'none';
            btnText.textContent = 'Sign In';
            form.querySelector('button').disabled = false;
        }
    });
}

export function initRegister(role) {
    const form = document.getElementById('registerForm');
    const errorBox = document.getElementById('errorBox');
    const spinner = document.getElementById('spinner');
    const btnText = document.getElementById('btnText');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(form);
        formData.append('user_type', role);

        // Validation: Ensure passwords match
        const pass = formData.get('password');
        const confirmPass = formData.get('confirmPassword');
        
        if (pass !== confirmPass) {
            errorBox.textContent = "Passwords don't match";
            errorBox.style.display = 'block';
            return;
        }

        errorBox.style.display = 'none';
        if (spinner) spinner.style.display = 'inline-block';
        if (btnText) btnText.textContent = 'Submitting for review...';

        try {
            // Note: When sending FormData, we DO NOT set Content-Type header manually.
            // The browser will set it correctly with the boundary for files.
            const response = await fetch(`${API_BASE_URL}/auth/register`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Registration failed');
            }

            alert('Registration submitted! Our admin will review your documents.');
            window.location.href = 'login.html?role=' + role;

        } catch (err) {
            errorBox.textContent = err.message;
            errorBox.style.display = 'block';
            if (spinner) spinner.style.display = 'none';
            if (btnText) btnText.textContent = 'Submit for Review';
        }
    });
}
export async function verifyDocumentAI(file, type) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = (event) => {
            const img = new Image();
            img.src = event.target.result;
            img.onload = async () => {
                // Resize image to avoid "Payload Too Large" (400) error
                const canvas = document.createElement('canvas');
                const MAX_WIDTH = 800;
                const MAX_HEIGHT = 800;
                let width = img.width;
                let height = img.height;

                if (width > height) {
                    if (width > MAX_WIDTH) {
                        height *= MAX_WIDTH / width;
                        width = MAX_WIDTH;
                    }
                } else {
                    if (height > MAX_HEIGHT) {
                        width *= MAX_HEIGHT / height;
                        height = MAX_HEIGHT;
                    }
                }

                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);

                const compressedBase64 = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];

                try {
                    const res = await fetch(`${API_BASE_URL}/ai/verify-document`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ image: compressedBase64, type: type })
                    });
                    const data = await res.json();
                    resolve(data);
                } catch (err) {
                    console.error("AI Error:", err);
                    resolve({ valid: false, message: "AI verification service error." });
                }
            };
        };
        reader.onerror = (err) => reject(err);
    });
}
