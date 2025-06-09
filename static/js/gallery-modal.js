document.addEventListener('DOMContentLoaded', function() {
    // Масив для зберігання даних галереї
    let galleryImages = [];
    let currentImageIndex = 0;
    let touchStartX = 0;
    let touchEndX = 0;

    // Ініціалізація галереї
    function initGallery() {
        // Збираємо всі зображення з галереї
        const galleryItems = document.querySelectorAll('.u-gallery-item');
        
        galleryItems.forEach((item, index) => {
            // Отримуємо дані про зображення
            const container = item.querySelector('.u-container-layout');
            const title = container.querySelector('.u-text-2')?.textContent || '';
            const description = container.querySelector('.u-text-3')?.textContent || '';
            const imageUrl = item.style.backgroundImage.replace(/url\(['"]?(.*?)['"]?\)/, '$1');
            
            galleryImages.push({
                url: imageUrl,
                title: title,
                description: description
            });
            
            // Додаємо обробник кліку
            item.addEventListener('click', function() {
                openModal(index);
            });
        });

        // Створюємо модальне вікно
        createModal();
    }

    // Створення модального вікна
    function createModal() {
        const modalHTML = `
            <div id="galleryModal" class="gallery-modal">
                <span class="modal-close">&times;</span>
                <span class="modal-prev">&#10094;</span>
                <span class="modal-next">&#10095;</span>
                <div class="modal-loading">Завантаження...</div>
                <div class="modal-content">
                    <img id="modalImage" src="" alt="">
                    <div class="modal-caption">
                        <h3 id="modalTitle"></h3>
                        <p id="modalDescription"></p>
                    </div>
                </div>
                <div class="modal-indicator"></div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Додаємо індикатори
        const indicatorContainer = document.querySelector('.modal-indicator');
        galleryImages.forEach((_, index) => {
            const dot = document.createElement('span');
            dot.className = 'indicator-dot';
            dot.addEventListener('click', () => showImage(index));
            indicatorContainer.appendChild(dot);
        });
        
        // Додаємо обробники подій
        setupModalEvents();
    }

    // Налаштування обробників подій модального вікна
    function setupModalEvents() {
        const modal = document.getElementById('galleryModal');
        const closeBtn = modal.querySelector('.modal-close');
        const prevBtn = modal.querySelector('.modal-prev');
        const nextBtn = modal.querySelector('.modal-next');
        
        // Закриття модального вікна
        closeBtn.addEventListener('click', closeModal);
        
        // Навігація
        prevBtn.addEventListener('click', showPrevImage);
        nextBtn.addEventListener('click', showNextImage);
        
        // Закриття при кліку поза зображенням
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });
        
        // Клавіатурна навігація
        document.addEventListener('keydown', handleKeyPress);
        
        // Сенсорні жести для мобільних пристроїв
        modal.addEventListener('touchstart', handleTouchStart, {passive: true});
        modal.addEventListener('touchend', handleTouchEnd, {passive: true});
    }

    // Відкриття модального вікна
    function openModal(index) {
        const modal = document.getElementById('galleryModal');
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        showImage(index);
    }

    // Закриття модального вікна
    function closeModal() {
        const modal = document.getElementById('galleryModal');
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }

    // Показ зображення
    function showImage(index) {
        currentImageIndex = index;
        const image = galleryImages[index];
        const modalImage = document.getElementById('modalImage');
        const modalTitle = document.getElementById('modalTitle');
        const modalDescription = document.getElementById('modalDescription');
        const loadingIndicator = document.querySelector('.modal-loading');
        
        // Показуємо індикатор завантаження
        loadingIndicator.classList.add('active');
        modalImage.style.opacity = '0';
        
        // Завантажуємо зображення
        const img = new Image();
        img.onload = function() {
            modalImage.src = image.url;
            modalImage.style.opacity = '1';
            modalTitle.textContent = image.title;
            modalDescription.textContent = image.description;
            loadingIndicator.classList.remove('active');
            
            // Оновлюємо індикатори
            updateIndicators();
        };
        img.src = image.url;
    }

    // Показ попереднього зображення
    function showPrevImage() {
        currentImageIndex = (currentImageIndex - 1 + galleryImages.length) % galleryImages.length;
        showImage(currentImageIndex);
    }

    // Показ наступного зображення
    function showNextImage() {
        currentImageIndex = (currentImageIndex + 1) % galleryImages.length;
        showImage(currentImageIndex);
    }

    // Оновлення індикаторів
    function updateIndicators() {
        const dots = document.querySelectorAll('.indicator-dot');
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentImageIndex);
        });
    }

    // Обробка клавіатурних подій
    function handleKeyPress(e) {
        const modal = document.getElementById('galleryModal');
        if (!modal.classList.contains('active')) return;
        
        switch(e.key) {
            case 'ArrowLeft':
                showPrevImage();
                break;
            case 'ArrowRight':
                showNextImage();
                break;
            case 'Escape':
                closeModal();
                break;
        }
    }

    // Обробка сенсорних жестів
    function handleTouchStart(e) {
        touchStartX = e.changedTouches[0].screenX;
    }

    function handleTouchEnd(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }

    function handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchStartX - touchEndX;
        
        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                showNextImage();
            } else {
                showPrevImage();
            }
        }
    }

    // Ініціалізація
    initGallery();
});