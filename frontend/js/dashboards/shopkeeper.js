const API_BASE_URL = 'http://localhost:5000/api';

export function initShopDashboard() {
    const token = localStorage.getItem('access_token');
    const userEmail = localStorage.getItem('user_email');
    
    if (!token) {
        window.location.href = '../pages/login.html';
        return;
    }

    loadInventory();

    const form = document.getElementById('productForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        try {
            const res = await fetch(`${API_BASE_URL}/items/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(data)
            });

            if (res.ok) {
                alert('Product listed successfully');
                toggleModal(false);
                loadInventory();
            } else {
                const err = await res.json();
                alert(err.message || 'Failed to add product');
            }
        } catch (err) {
            console.error(err);
        }
    });
}

async function loadInventory() {
    const list = document.getElementById('productList');
    const token = localStorage.getItem('access_token');

    try {
        // In reality, we'd fetch items ONLY for this shopkeeper
        const res = await fetch(`${API_BASE_URL}/items/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const items = await res.json();

        if (items.length === 0) {
            list.innerHTML = '<p style="color: #64748b;">No products listed yet.</p>';
            return;
        }

        list.innerHTML = items.map(item => `
            <div class="card" style="padding: 1rem;">
                <h4 style="margin-bottom: 0.5rem;">${item.name}</h4>
                <p style="font-size: 0.8rem; color: #64748b;">${item.category} • ${item.item_type}</p>
                <p style="font-weight: 700; margin-top: 0.5rem;">₹${item.price}</p>
                <button class="btn" style="width: 100%; margin-top: 1rem; color: #ef4444; border: 1px solid #fee2e2; padding: 0.4rem;" onclick="deleteItem('${item.id}')">Delete</button>
            </div>
        `).join('');
    } catch (err) {
        console.error(err);
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
