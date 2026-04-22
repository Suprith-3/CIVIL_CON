const Utils = {
    formatCurrency: (amount) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
        }).format(amount);
    },
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    setLocalStorage: (key, value) => {
        localStorage.setItem(key, typeof value === 'object' ? JSON.stringify(value) : value);
    },
    getLocalStorage: (key) => {
        const item = localStorage.getItem(key);
        try {
            return JSON.parse(item);
        } catch (e) {
            return item;
        }
    }
};

window.Utils = Utils;
