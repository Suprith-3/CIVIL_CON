const API_BASE_URL = 'http://localhost:5000/api';

export function initUserDashboard() {
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
    const grid = document.getElementById('featuredGrid');
    const allGrid = document.getElementById('allGrid');
    
    try {
        const res = await fetch(`${API_BASE_URL}/items/`);
        const items = await res.json();

        const renderItem = (item) => `
            <div class="product-card card">
                <div class="product-img"></div>
                <div class="product-info">
                    <span style="font-size: 0.75rem; color: var(--primary); font-weight: 600;">${item.category}</span>
                    <h4 style="margin: 0.25rem 0;">${item.name}</h4>
                    <p style="font-size: 0.8rem; color: #64748b; margin-bottom: 0.5rem;">${item.description || ''}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
                        <span style="font-weight: 700; color: #1e293b;">₹${item.price}${item.item_type === 'rent' ? '/day' : ''}</span>
                        <button class="btn btn-primary" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">Add</button>
                    </div>
                </div>
            </div>
        `;

        if (items.length > 0) {
            grid.innerHTML = items.slice(0, 3).map(renderItem).join('');
            allGrid.innerHTML = items.map(renderItem).join('');
        } else {
            grid.innerHTML = '<p>No items found.</p>';
        }
    } catch (err) {
        console.error('Failed to load items', err);
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
