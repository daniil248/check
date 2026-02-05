/**
 * NorthPak Logistics - Main JavaScript
 * Обработчики для навигации, форм, языков
 */

document.addEventListener('DOMContentLoaded', function() {

    // ==================== МОБИЛЬНОЕ МЕНЮ (БУРГЕР) ====================
    const burger = document.querySelector('.burger');
    const mainNav = document.getElementById('main-nav');
    const backdrop = document.getElementById('nav-backdrop');
    const body = document.body;

    function openMenu() {
        if (!mainNav || !burger) return;
        mainNav.classList.add('nav-open');
        if (backdrop) backdrop.classList.add('nav-open');
        burger.classList.add('active');
        burger.setAttribute('aria-expanded', 'true');
        burger.setAttribute('aria-label', 'Закрыть меню');
        body.style.overflow = 'hidden';
    }

    function closeMenu() {
        if (!mainNav || !burger) return;
        mainNav.classList.remove('nav-open');
        if (backdrop) backdrop.classList.remove('nav-open');
        burger.classList.remove('active');
        burger.setAttribute('aria-expanded', 'false');
        burger.setAttribute('aria-label', 'Открыть меню');
        body.style.overflow = '';
    }

    if (burger && mainNav) {
        burger.addEventListener('click', function() {
            if (mainNav.classList.contains('nav-open')) {
                closeMenu();
            } else {
                openMenu();
            }
        });
        if (backdrop) backdrop.addEventListener('click', closeMenu);
        mainNav.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', closeMenu);
        });
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') closeMenu();
        });
    }
    
    // ==================== ПЛАВНАЯ ПРОКРУТКА К СЕКЦИЯМ ====================
    const navLinks = document.querySelectorAll('.nav-link, .footer-links a');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            // Если это якорная ссылка (#services, #about, etc.)
            if (href && href.startsWith('#') && href.length > 1) {
                e.preventDefault();
                
                const targetId = href.substring(1);
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // ==================== КНОПКА "ОБРАТНЫЙ ЗВОНОК" ====================
    const callbackBtn = document.querySelector('.callback-btn');
    
    if (callbackBtn) {
        callbackBtn.addEventListener('click', function() {
            // Прокручиваем к форме внизу страницы
            const finalCta = document.querySelector('.final-cta');
            
            if (finalCta) {
                finalCta.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
                
                // Фокусируемся на первом поле формы
                setTimeout(() => {
                    const firstInput = finalCta.querySelector('input[type="tel"]');
                    if (firstInput) {
                        firstInput.focus();
                    }
                }, 800);
            }
        });
    }
    
    // ==================== ОБРАБОТКА ФОРМ ====================
    const forms = document.querySelectorAll('.request-form, .hero-form');
    
    forms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            
            // Показываем загрузку
            submitBtn.disabled = true;
            submitBtn.textContent = 'Отправка...';
            
            // Собираем данные формы
            const formData = new FormData(this);
            const data = {};
            formData.forEach((value, key) => {
                data[key] = value;
            });
            
            try {
                // Отправляем на WhatsApp (запасной вариант)
                const phone = '77473738113';
                let message = 'Новая заявка с сайта NorthPak Logistics:\n\n';
                
                for (const [key, value] of Object.entries(data)) {
                    if (key !== 'agree') {
                        message += `${key}: ${value}\n`;
                    }
                }
                
                const whatsappUrl = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
                
                // Открываем WhatsApp
                window.open(whatsappUrl, '_blank');
                
                // Показываем успех
                submitBtn.textContent = '✓ Отправлено!';
                submitBtn.style.background = '#25D366';
                
                // Очищаем форму
                setTimeout(() => {
                    this.reset();
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                    submitBtn.style.background = '';
                }, 3000);
                
            } catch (error) {
                console.error('Ошибка отправки:', error);
                
                // Показываем ошибку
                submitBtn.textContent = '✗ Ошибка. Попробуйте снова';
                submitBtn.style.background = '#dc3545';
                
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                    submitBtn.style.background = '';
                }, 3000);
            }
        });
    });
    
    // ==================== ПЕРЕКЛЮЧЕНИЕ ЯЗЫКОВ ====================
    const langButtons = document.querySelectorAll('.lang-btn');
    
    langButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const lang = this.getAttribute('data-lang');
            
            // Убираем active со всех кнопок
            langButtons.forEach(b => b.classList.remove('active'));
            
            // Добавляем active к текущей
            this.classList.add('active');
            
            // Меняем язык
            changeLanguage(lang);
        });
    });
    
    // Функция смены языка
    function changeLanguage(lang) {
        if (typeof TRANSLATIONS === 'undefined' || !TRANSLATIONS[lang]) {
            console.error('Переводы не загружены или язык не найден:', lang);
            return;
        }
        
        const translations = TRANSLATIONS[lang];
        
        // Меняем все элементы с data-i18n
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            
            if (translations[key]) {
                // Если это placeholder
                if (element.hasAttribute('placeholder')) {
                    element.placeholder = translations[key];
                } else {
                    element.innerHTML = translations[key];
                }
            }
        });
        
        // Меняем placeholders отдельно
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            
            if (translations[key]) {
                element.placeholder = translations[key];
            }
        });
        
        // Сохраняем выбранный язык
        localStorage.setItem('selectedLanguage', lang);
    }
    
    // Загружаем сохраненный язык при загрузке страницы
    const savedLang = localStorage.getItem('selectedLanguage');
    if (savedLang && savedLang !== 'ru') {
        const langBtn = document.querySelector(`.lang-btn[data-lang="${savedLang}"]`);
        if (langBtn) {
            langBtn.click();
        }
    }
    
    // ==================== ВАЛИДАЦИЯ ТЕЛЕФОНА ====================
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    
    phoneInputs.forEach(input => {
        input.addEventListener('input', function() {
            // Оставляем только цифры и +
            this.value = this.value.replace(/[^\d+]/g, '');
        });
    });
    
    // ==================== АНИМАЦИЯ ПРИ СКРОЛЛЕ ====================
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Применяем анимацию к секциям
    document.querySelectorAll('section').forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(20px)';
        section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(section);
    });
    
    // Первая секция сразу видна
    const firstSection = document.querySelector('section');
    if (firstSection) {
        firstSection.style.opacity = '1';
        firstSection.style.transform = 'translateY(0)';
    }
});
