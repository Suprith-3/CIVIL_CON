const API_BASE_URL = 'http://localhost:5000/api';

function initUserDashboard() {
    const userEmail = localStorage.getItem('user_email');
    if (!userEmail) {
        window.location.href = '../pages/login.html';
        return;
    }

    document.getElementById('userEmail').textContent = userEmail;

    // Load initial data
    loadProducts();
    loadShops();
    loadEngineers();
}

async function loadProducts() {
    try {
        const res = await fetch(`${API_BASE_URL}/items/`);
        const items = await res.json();

        const renderItem = (item) => `
            <div class="product-card card">
                <div class="product-img" style="background-image: url('${item.image_url || '/api/uploads/placeholder.jpg'}'); background-size: cover; background-position: center; height: 180px; border-radius: 12px; margin-bottom: 1rem;"></div>
                <div class="product-info">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0;">${item.name}</h4>
                        <span style="font-weight: 700; color: #1e293b;">₹${item.price}</span>
                    </div>
                    <p style="font-size: 0.75rem; color: #64748b; margin: 0.25rem 0;">${item.category}</p>
                    <button class="btn btn-primary" style="width: 100%; margin-top: 1rem; background: #2563eb;" onclick="addToCart('${encodeURIComponent(JSON.stringify(item))}')">
                        🛒 Add to Cart & Book
                    </button>
                </div>
            </div>
        `;

        const grid = document.getElementById('featuredGrid');
        const allGrid = document.getElementById('allGrid');

        if (items.length > 0) {
            if (grid) grid.innerHTML = items.slice(0, 3).map(renderItem).join('');
            if (allGrid) allGrid.innerHTML = items.map(renderItem).join('');
        } else {
            if (grid) grid.innerHTML = '<p>No items found.</p>';
        }
    } catch (err) {
        console.error('Failed to load items', err);
    }
}

// CART LOGIC
window.addToCart = (itemData) => {
    const item = JSON.parse(decodeURIComponent(itemData));
    let cart = JSON.parse(localStorage.getItem('cart') || '[]');
    cart.push(item);
    localStorage.setItem('cart', JSON.stringify(cart));
    
    if (confirm(`${item.name} added! Would you like to proceed to Cart now?`)) {
        window.location.href = 'cart.html'; 
    }
    updateCartCount();
};

function updateCartCount() {
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const countBadge = document.getElementById('cartCount');
    if (countBadge) countBadge.textContent = cart.length;
}

// CHECKOUT LOGIC
window.placeOrder = async (isOnline = false) => {
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    if (cart.length === 0) return alert("Cart is empty");

    const total = cart.reduce((sum, item) => sum + item.price, 0);
    const token = localStorage.getItem('access_token');

    try {
        const res = await fetch(`${API_BASE_URL}/orders/create`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                amount: total,
                items: cart,
                address: document.getElementById('deliveryAddress')?.value || "Default Address"
            })
        });

        const order = await res.json();

        if (isOnline) {
            const options = {
                "key": "rzp_test_SLEACrszBCNIIo", // Activated with real key
                "amount": order.amount,
                "currency": "INR",
                "name": "Bhoomitra Shop",
                "order_id": order.id,
                "handler": function (response) {
                    verifyPayment(response);
                }
            };
            const rzp = new Razorpay(options);
            rzp.open();
        } else {
            alert("Order Placed Successfully (COD)!");
            localStorage.removeItem('cart');
            window.location.href = 'my-orders.html';
        }

    } catch (err) {
        alert("Order failed: " + err.message);
    }
};

async function verifyPayment(response) {
    const token = localStorage.getItem('access_token');
    const res = await fetch(`${API_BASE_URL}/orders/verify`, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(response)
    });

    if (res.ok) {
        alert("Payment Successful!");
        localStorage.removeItem('cart');
        window.location.href = 'my-orders.html';
    }
}

window.searchSchemes = async () => {
    const resultDiv = document.getElementById('schemesResult');
    resultDiv.innerHTML = '<p class="animate-pulse">Asking Groq AI for latest schemes...</p>';
    
    try {
        const res = await fetch(`${API_BASE_URL}/ai/schemes`);
        const data = await res.json();
        resultDiv.innerHTML = `
            <div class="card" style="white-space: pre-wrap; margin-top: 1rem; line-height: 1.6;">
                ${data.result}
            </div>
        `;
    } catch (err) {
        resultDiv.innerHTML = '<p style="color: red;">Failed to fetch AI schemes.</p>';
    }
}

async function loadShops() {
    const grid = document.getElementById('shopsGrid');
    const mockShops = [
        { name: 'City Builder Supplies', location: 'Mysuru', rating: 4.8 },
        { name: 'Modern Hardware', location: 'Bengaluru', rating: 4.5 }
    ];

    grid.innerHTML = mockShops.map(shop => `
        <div class="card" style="text-align: center;">
            <div style="width: 60px; height: 60px; background: #e2e8f0; border-radius: 50%; margin: 0 auto 1rem;"></div>
            <h4>${shop.name}</h4>
            <p style="font-size: 0.875rem; color: #64748b;">${shop.location} • ⭐ ${shop.rating}</p>
            <button class="btn" style="width: 100%; margin-top: 1rem; border: 1px solid var(--border);">View Shop</button>
        </div>
    `).join('');
}

async function loadEngineers() {
     const grid = document.getElementById('engineersGrid');
     const mockEngineers = [
        { name: 'Er. Rajesh Kumar', spec: 'Civil & Structural', rating: 4.9, projects: 12 },
        { name: 'Er. Priya Sharma', spec: 'Interior Design', rating: 4.7, projects: 8 }
    ];

    grid.innerHTML = mockEngineers.map(eng => `
        <div class="card" style="text-align: center;">
            <div style="width: 60px; height: 60px; background: #dcfce7; color: #166534; border-radius: 50%; margin: 0 auto 1rem; display: flex; align-items: center; justify-content: center; font-weight: 700;">${eng.name[4]}</div>
            <h4>${eng.name}</h4>
            <p style="font-size: 0.875rem; color: #64748b;">${eng.spec}</p>
            <p style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.5rem;">⭐ ${eng.rating} | ${eng.projects} Projects</p>
            <button class="btn btn-primary" style="width: 100%; margin-top: 1rem;">View Portfolio</button>
        </div>
    `).join('');
}
