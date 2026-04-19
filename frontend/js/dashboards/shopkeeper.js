const BACKEND_URL = 'http://127.0.0.1:5000';
const API_BASE_URL = `${BACKEND_URL}/api`;

export function initShopDashboard() {
    const token = localStorage.getItem('access_token');
    const userEmail = localStorage.getItem('user_email');
    
    if (!token) {
        window.location.href = '../pages/login.html';
        return;
    }

    loadInventory();
    loadShopStatus();

    const imgInput = document.getElementById('productImgInput');
    const imgPreview = document.getElementById('imgPreview');
    const statusEl = document.getElementById('visionStatus');
    const cameraBtn = document.getElementById('cameraBtn');
    const cameraContainer = document.getElementById('cameraContainer');
    const video = document.getElementById('video');
    const captureBtn = document.getElementById('captureBtn');
    let capturedBlob = null;

    // CAMERA LOGIC
    cameraBtn.onclick = async (e) => {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        try {
            console.log("Opening Camera...");
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            cameraContainer.style.display = 'block';
            imgPreview.style.display = 'none';
        } catch (err) {
            console.error("Camera error:", err);
            alert('Camera access denied or not found');
        }
    };

    captureBtn.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        
        canvas.toBlob((blob) => {
            capturedBlob = blob;
            const url = URL.createObjectURL(blob);
            imgPreview.src = url;
            imgPreview.style.display = 'block';
            cameraContainer.style.display = 'none';
            
            // Stop camera
            const stream = video.srcObject;
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }

            // Trigger Vision Scan for the captured image
            runVisionScan(blob);
            unlockSubmit();
        }, 'image/jpeg');
    };

    async function runVisionScan(file) {
        if (!file) return;
        statusEl.textContent = '🛡️ OpenCV Scanning...';
        statusEl.style.display = 'block';
        statusEl.style.background = '#f1f5f9';
        statusEl.style.color = '#475569';

        const scanData = new FormData();
        scanData.append('product_img', file, 'captured.jpg');

        try {
            const currentToken = localStorage.getItem('access_token');
            const res = await fetch(`${API_BASE_URL}/items/scan`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${currentToken}` },
                body: scanData
            });
            if (res.ok) {
                const data = await res.json();
                statusEl.textContent = `🛡️ OpenCV Result: ${data.status}`;
                statusEl.style.background = data.status === 'Verified' ? '#dcfce7' : '#fee2e2';
                statusEl.style.color = data.status === 'Verified' ? '#166534' : '#991b1b';
            }
        } catch (err) {
            console.error("Scan failed silently", err);
            statusEl.textContent = '🛡️ Vision Service Ready';
        }
    }

    imgInput.addEventListener('change', () => {
        const file = imgInput.files[0];
        if (!file) return;
        capturedBlob = null; // Reset captured if file picked

        const reader = new FileReader();
        reader.onload = (e) => {
            imgPreview.src = e.target.result;
            imgPreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
        runVisionScan(file);
        unlockSubmit();
    });

    function unlockSubmit() {
        const btn = document.getElementById('submitProductBtn');
        if (btn) {
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        }
    }

    const form = document.getElementById('productForm');

    // MANUAL SUBMISSION TRIGGER
    const submitBtn = document.getElementById('submitProductBtn');
    submitBtn.onclick = async (e) => {
        if (e) e.preventDefault();
        
        const fileInput = document.getElementById('productImgInput');
        const file = capturedBlob || fileInput.files[0];

        // Basic validation
        const nameVal = form.querySelector('[name="name"]').value;
        const priceVal = form.querySelector('[name="price"]').value;
        
        if (!nameVal || !priceVal) {
            alert('Please enter Product Name and Price first!');
            return;
        }

        const currentToken = localStorage.getItem('access_token');
        const formData = new FormData();
        
        formData.append('name', nameVal);
        formData.append('price', priceVal);
        formData.append('category', form.querySelector('[name="category"]').value);
        formData.append('item_type', form.querySelector('[name="item_type"]').value);
        formData.append('product_img', file, file.name || 'product.jpg');

        try {
            console.log("Listing product...");
            const res = await fetch(`${API_BASE_URL}/items/`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${currentToken}` },
                body: formData
            });

            if (res.ok) {
                alert('SUCCESS! Product is now in your inventory.');
                window.location.reload();
            } else {
                const result = await res.json();
                const errMsg = result.message || result.error || 'Check server logs';
                
                if (errMsg.toLowerCase().includes('expired')) {
                    alert('Session Expired! Please Log Out and Log In again to continue.');
                } else {
                    alert('DB ERROR: ' + errMsg);
                }
            }
        } catch (err) {
            alert('CONNECTION ERROR: ' + err.message);
        }
    };

    // NOTIFICATION LOGIC
    let lastOrderCount = -1;
    const alertSound = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3');

    async function checkNewOrders() {
        try {
            const token = localStorage.getItem('access_token');
            const res = await fetch(`${API_BASE_URL}/orders/all`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const orders = await res.json();
            
            if (lastOrderCount !== -1 && orders.length > lastOrderCount) {
                // NEW ORDER DETECTED!
                alertSound.play();
                alert('🔔 NEW ORDER RECEIVED! Please check the Orders tab for transport details. 🏗️');
                if (window.loadOrders) window.loadOrders(); // Refresh table if on that tab
            }
            lastOrderCount = orders.length;
        } catch (e) { console.log("Silent error in order check"); }
    }

    // Start checking every 30 seconds
    setInterval(checkNewOrders, 30000);
    checkNewOrders(); // Run once immediately
}

async function loadShopStatus() {
    const token = localStorage.getItem('access_token');
    const user_id = localStorage.getItem('user_id');
    const statusEl = document.getElementById('shopStatus');
    
    try {
        const res = await fetch(`${API_BASE_URL}/auth/status?user_id=${user_id}`);
        const data = await res.json();
        
        if (data.status === 'approved') {
            statusEl.textContent = 'Status: Approved ✅';
            statusEl.className = 'status-pill status-approved';
        } else if (data.status === 'rejected') {
            statusEl.textContent = 'Status: Rejected ❌';
            statusEl.style.background = '#fee2e2';
            statusEl.style.color = '#991b1b';
        }
    } catch (err) {
        console.error("Status fetch failed", err);
    }
}

async function loadInventory() {
    const list = document.getElementById('productList');
    const token = localStorage.getItem('access_token');

    try {
        console.log("--- Fetching Inventory ---");
        const res = await fetch(`${API_BASE_URL}/items/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.status === 401) {
            list.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 3rem;"><p style="color: #ef4444; font-weight:bold;">🔒 Session Expired! Please Log Out and Log In again.</p></div>`;
            return;
        }

        const data = await res.json();
        console.log("Raw Inventory Data:", data);

        if (!Array.isArray(data)) {
            list.innerHTML = `<p style="color: #ef4444; font-weight:bold;">⚠️ Error: ${data.message || 'Database returned bad format'}</p>`;
            return;
        }

        if (data.length === 0) {
            list.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 3rem;"><p style="color: #64748b; font-size: 1.1rem;">No products listed yet. Click "+ Add Product" to start!</p></div>';
            return;
        }

        list.innerHTML = data.map(item => {
            const imgPath = item.image_url ? 
                (item.image_url.startsWith('http') ? item.image_url : `${BACKEND_URL}${item.image_url}`) : 
                'https://placehold.co/400x300?text=No+Photo';

            return `
                <div class="card" style="padding: 1rem; border: 1px solid #e2e8f0; transition: transform 0.2s;">
                    <img src="${imgPath}" style="width: 100%; height: 160px; object-fit: cover; border-radius: 12px; margin-bottom: 1rem;" onerror="this.src='https://placehold.co/400x300?text=Image+Error'">
                    <h3 style="font-size: 1rem; margin-bottom: 0.25rem; font-weight: 700;">${item.name || 'Unnamed Product'}</h3>
                    <p style="font-size: 0.8rem; color: #64748b; margin-bottom: 0.5rem; height: 32px; overflow: hidden;">${item.category || 'Uncategorized'}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: auto;">
                        <span style="font-size: 1.1rem; font-weight: 800; color: #2563eb;">₹${item.price || '0.00'}</span>
                        <button class="btn" style="background: #fee2e2; color: #991b1b; padding: 0.4rem 0.8rem; border-radius: 8px; font-size: 0.75rem; font-weight: 600;" onclick="deleteItem('${item.id}')">Delete</button>
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (err) {
        console.error("Critical Inventory Failure:", err);
        list.innerHTML = `<p style="color: #ef4444;">⚠️ Connection failed: ${err.message}</p>`;
    }
}

window.deleteItem = async (id) => {
    if (!confirm('Are you sure you want to delete this item?')) return;
    const token = localStorage.getItem('access_token');
    
    try {
        const res = await fetch(`${API_BASE_URL}/items/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) loadInventory();
    } catch (err) {
        console.error(err);
    }
}
