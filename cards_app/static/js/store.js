// static/js/store.js
document.addEventListener('DOMContentLoaded', function() {
    const userGold = window.userGold || 0;

    function updateQuantity(itemId, price, delta) {
        const input = document.getElementById(`qty-${itemId}`);
        if (!input) return;
        let current = parseInt(input.value) || 0;
        let newVal = current + delta;
        let maxQty = price > 0 ? Math.floor(userGold / price) : 0;
        if (newVal < 0) newVal = 0;
        if (newVal > maxQty) newVal = maxQty;
        if (newVal === current) return;

        input.value = newVal;
        const quantityHidden = document.getElementById(`quantity-${itemId}`);
        if (quantityHidden) quantityHidden.value = newVal;

        const totalSpan = document.getElementById(`total-${itemId}`);
        if (totalSpan) totalSpan.innerText = `Итого: ${newVal * price}💰`;

        const buyBtn = document.querySelector(`#form-${itemId} .btn-buy`);
        if (buyBtn) {
            if (newVal > 0 && userGold >= newVal * price) {
                buyBtn.disabled = false;
                buyBtn.classList.remove('disabled');
            } else {
                buyBtn.disabled = true;
                buyBtn.classList.add('disabled');
            }
        }
    }

    document.querySelectorAll('.qty-btn.minus').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const itemId = this.dataset.itemId;
            const price = parseInt(this.dataset.price);
            updateQuantity(itemId, price, -1);
        });
    });

    document.querySelectorAll('.qty-btn.plus').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const itemId = this.dataset.itemId;
            const price = parseInt(this.dataset.price);
            updateQuantity(itemId, price, +1);
        });
    });

    // Инициализация: ограничение максимального количества при загрузке
    document.querySelectorAll('.qty-input').forEach(input => {
        const itemId = input.id.split('-')[1];
        const plusBtn = document.querySelector(`.plus[data-item-id="${itemId}"]`);
        if (!plusBtn) return;
        const price = parseInt(plusBtn.dataset.price);
        let maxQty = price > 0 ? Math.floor(userGold / price) : 0;
        input.max = maxQty;
        let currentVal = parseInt(input.value);
        if (currentVal > maxQty) {
            input.value = maxQty;
            const quantityHidden = document.getElementById(`quantity-${itemId}`);
            if (quantityHidden) quantityHidden.value = maxQty;
            const totalSpan = document.getElementById(`total-${itemId}`);
            if (totalSpan) totalSpan.innerText = `Итого: ${maxQty * price}💰`;
            const buyBtn = document.querySelector(`#form-${itemId} .btn-buy`);
            if (buyBtn) {
                if (maxQty > 0 && userGold >= maxQty * price) {
                    buyBtn.disabled = false;
                    buyBtn.classList.remove('disabled');
                } else {
                    buyBtn.disabled = true;
                    buyBtn.classList.add('disabled');
                }
            }
        }
    });
});