// static/js/merge.js
document.addEventListener('DOMContentLoaded', () => {
    const availableCards = document.querySelectorAll('.store-grid .selectable-card');
    const mergeButton = document.getElementById('mergeButton');
    const selectedCountSpan = document.getElementById('selectedCount');
    const needCountSpan = document.getElementById('needCount');
    const sacrificedIdsInput = document.getElementById('sacrificedIdsInput');

    let selectedCardIds = [];
    let maxSelectable = needCountSpan ? parseInt(needCountSpan.textContent, 10) : 0;
    if (isNaN(maxSelectable)) maxSelectable = 0;
    maxSelectable = Math.min(maxSelectable, availableCards.length);

    if (maxSelectable <= 0 && mergeButton) {
        mergeButton.disabled = true;
        return;
    }

    function updateCounter() {
        if (selectedCountSpan) {
            selectedCountSpan.textContent = selectedCardIds.length;
        }
    }

    function updateButton() {
        if (!mergeButton) return;
        const count = selectedCardIds.length;
        mergeButton.disabled = (count < 1 || count > maxSelectable);
    }

    function updateHiddenField() {
        // Сохраняем выбранные ID в виде JSON-строки (или через запятую)
        if (sacrificedIdsInput) {
            sacrificedIdsInput.value = JSON.stringify(selectedCardIds);
            // Альтернатива: sacrificedIdsInput.value = selectedCardIds.join(',');
        }
    }

    function selectCard(cardElement, cardId) {
        if (selectedCardIds.length >= maxSelectable) {
            showToast(`Нельзя выбрать больше ${maxSelectable} карт`, 'error');
            return false;
        }
        if (!selectedCardIds.includes(cardId)) {
            selectedCardIds.push(cardId);
            cardElement.classList.add('selected');
            updateCounter();
            updateButton();
            updateHiddenField();
            return true;
        }
        return false;
    }

    function deselectCard(cardElement, cardId) {
        const index = selectedCardIds.indexOf(cardId);
        if (index !== -1) {
            selectedCardIds.splice(index, 1);
            cardElement.classList.remove('selected');
            updateCounter();
            updateButton();
            updateHiddenField();
            return true;
        }
        return false;
    }

    function handleCardClick(e) {
        const card = e.target.closest('.selectable-card');
        if (!card) return;
        const cardId = card.dataset.cardId;
        if (!cardId) return;

        if (card.classList.contains('selected')) {
            deselectCard(card, cardId);
        } else {
            selectCard(card, cardId);
        }
    }

    // Назначаем обработчики кликов на карты
    availableCards.forEach(card => card.addEventListener('click', handleCardClick));

    // Инициализация
    selectedCardIds = [];
    availableCards.forEach(card => card.classList.remove('selected'));
    updateCounter();
    updateButton();
    updateHiddenField();

    if (availableCards.length === 0 && mergeButton) {
        mergeButton.disabled = true;
        mergeButton.title = 'Нет карт для слияния';
    }
});