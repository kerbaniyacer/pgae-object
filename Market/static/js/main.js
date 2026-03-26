/**
 * Main JavaScript for Souq E-Commerce Store
 * Handles: Cart, Wishlist, Search, Mobile Menu, Toasts, User Menu
 */

// ============================================
// Utility Functions
// ============================================

/**
 * Get cart from localStorage
 */
function getCart() {
    const cart = localStorage.getItem('souq_cart');
    return cart ? JSON.parse(cart) : [];
}

/**
 * Save cart to localStorage
 */
function saveCart(cart) {
    localStorage.setItem('souq_cart', JSON.stringify(cart));
    updateCartCount();
}

/**
 * Get wishlist from localStorage
 */
function getWishlist() {
    const wishlist = localStorage.getItem('souq_wishlist');
    return wishlist ? JSON.parse(wishlist) : [];
}

/**
 * Save wishlist to localStorage
 */
function saveWishlist(wishlist) {
    localStorage.setItem('souq_wishlist', JSON.stringify(wishlist));
    updateWishlistCount();
}

/**
 * Format price with currency
 */
function formatPrice(price) {
    return new Intl.NumberFormat('ar-SA', {
        style: 'currency',
        currency: 'SAR',
        minimumFractionDigits: 0
    }).format(price);
}

/**
 * Generate unique ID
 */
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// ============================================
// Cart Functions
// ============================================

/**
 * Add item to cart
 */
function addToCart(product) {
    const cart = getCart();
    const existingItem = cart.find(item => item.id === product.id);

    if (existingItem) {
        existingItem.quantity += product.quantity || 1;
    } else {
        cart.push({
            id: product.id,
            name: product.name,
            price: product.price,
            image: product.image,
            quantity: product.quantity || 1
        });
    }

    saveCart(cart);
    showToast('تمت إضافة المنتج إلى السلة', 'success');
}

/**
 * Remove item from cart
 */
function removeFromCart(productId) {
    let cart = getCart();
    cart = cart.filter(item => item.id !== productId);
    saveCart(cart);
    showToast('تم إزالة المنتج من السلة', 'info');
}

/**
 * Update item quantity
 */
function updateCartQuantity(productId, quantity) {
    const cart = getCart();
    const item = cart.find(item => item.id === productId);

    if (item) {
        item.quantity = Math.max(1, quantity);
        saveCart(cart);
    }
}

/**
 * Get cart total
 */
function getCartTotal() {
    const cart = getCart();
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
}

/**
 * Get cart items count
 */
function getCartItemsCount() {
    const cart = getCart();
    return cart.reduce((count, item) => count + item.quantity, 0);
}

/**
 * Update cart count badge
 */
function updateCartCount() {
    const count = getCartItemsCount();
    const badge = document.getElementById('cartCount');

    if (badge) {
        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }
}

/**
 * Clear cart
 */
function clearCart() {
    localStorage.removeItem('souq_cart');
    updateCartCount();
}

// ============================================
// Wishlist Functions
// ============================================

/**
 * Add item to wishlist
 */
function addToWishlist(product) {
    const wishlist = getWishlist();
    const exists = wishlist.find(item => item.id === product.id);

    if (!exists) {
        wishlist.push({
            id: product.id,
            name: product.name,
            price: product.price,
            image: product.image
        });
        saveWishlist(wishlist);
        showToast('تمت إضافة المنتج إلى المفضلة', 'success');
    } else {
        showToast('المنتج موجود بالفعل في المفضلة', 'info');
    }
}

/**
 * Remove item from wishlist
 */
function removeFromWishlist(productId) {
    let wishlist = getWishlist();
    wishlist = wishlist.filter(item => item.id !== productId);
    saveWishlist(wishlist);
    showToast('تم إزالة المنتج من المفضلة', 'info');
}

/**
 * Check if item is in wishlist
 */
function isInWishlist(productId) {
    const wishlist = getWishlist();
    return wishlist.some(item => item.id === productId);
}

/**
 * Toggle wishlist item
 */
function toggleWishlist(product) {
    if (isInWishlist(product.id)) {
        removeFromWishlist(product.id);
        return false;
    } else {
        addToWishlist(product);
        return true;
    }
}

/**
 * Update wishlist count badge
 */
function updateWishlistCount() {
    const wishlist = getWishlist();
    const badge = document.getElementById('wishlistCount');

    if (badge) {
        if (wishlist.length > 0) {
            badge.textContent = wishlist.length > 99 ? '99+' : wishlist.length;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }
}

// ============================================
// Toast Notifications
// ============================================

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');

    const bgColors = {
        success: 'bg-sage-mint text-sage',
        error: 'bg-rose-light text-rose',
        warning: 'bg-status-warning text-taupe',
        info: 'bg-status-blue-light text-status-blue'
    };

    const icons = {
        success: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>',
        error: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>',
        warning: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>',
        info: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
    };

    toast.className = `toast-enter flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg ${bgColors[type] || bgColors.info}`;
    toast.innerHTML = `
        ${icons[type] || icons.info}
        <span class="font-medium">${message}</span>
    `;

    container.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('toast-enter');
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================
// Mobile Menu
// ============================================

function initMobileMenu() {
    const menuBtn = document.getElementById('mobileMenuBtn');
    const closeBtn = document.getElementById('closeMobileMenu');
    const menu = document.getElementById('mobileMenu');
    const overlay = document.getElementById('mobileMenuOverlay');

    if (!menuBtn || !menu) return;

    function openMenu() {
        menu.classList.add('open');
        overlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeMenu() {
        menu.classList.remove('open');
        overlay.classList.add('hidden');
        document.body.style.overflow = '';
    }

    menuBtn.addEventListener('click', openMenu);
    closeBtn?.addEventListener('click', closeMenu);
    overlay?.addEventListener('click', closeMenu);
}

// ============================================
// User Menu Dropdown
// ============================================

function initUserMenu() {
    const menuBtn = document.getElementById('userMenuBtn');
    const dropdown = document.getElementById('userDropdown');

    if (!menuBtn || !dropdown) return;

    menuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('hidden');
    });

    document.addEventListener('click', () => {
        dropdown.classList.add('hidden');
    });
}

// ============================================
// Search Modal
// ============================================

function initSearchModal() {
    const searchBtn = document.getElementById('searchBtn');
    const searchModal = document.getElementById('searchModal');
    const closeSearch = document.getElementById('closeSearch');
    const searchInput = document.getElementById('searchInput');

    if (!searchBtn || !searchModal) return;

    searchBtn.addEventListener('click', () => {
        searchModal.classList.remove('hidden');
        searchModal.classList.add('flex');
        searchInput?.focus();
    });

    function closeModal() {
        searchModal.classList.add('hidden');
        searchModal.classList.remove('flex');
    }

    closeSearch?.addEventListener('click', closeModal);

    searchModal.addEventListener('click', (e) => {
        if (e.target === searchModal) closeModal();
    });

    // Handle search
    searchInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            if (query) {
                window.location.href = `/products/?search=${encodeURIComponent(query)}`;
            }
        }
    });
}

// ============================================
// Product Filters
// ============================================

function initProductFilters() {
    const filterForm = document.getElementById('filterForm');
    const sortSelect = document.getElementById('sortSelect');
    const categoryFilters = document.querySelectorAll('[data-category]');
    const priceRange = document.getElementById('priceRange');
    const priceValue = document.getElementById('priceValue');

    if (!filterForm) return;

    // Category filter
    categoryFilters.forEach(filter => {
        filter.addEventListener('change', () => {
            filterForm.submit();
        });
    });

    // Sort select
    sortSelect?.addEventListener('change', () => {
        filterForm.submit();
    });

    // Price range
    if (priceRange && priceValue) {
        priceRange.addEventListener('input', () => {
            priceValue.textContent = formatPrice(priceRange.value);
        });

        priceRange.addEventListener('change', () => {
            filterForm.submit();
        });
    }
}

// ============================================
// Lightbox
// ============================================

function initLightbox() {
    const lightbox = document.getElementById('lightbox');
    const lightboxImage = document.getElementById('lightboxImage');
    const lightboxClose = document.getElementById('lightboxClose');
    const galleryImages = document.querySelectorAll('[data-lightbox]');

    if (!lightbox) return;

    galleryImages.forEach(img => {
        img.addEventListener('click', () => {
            lightboxImage.src = img.src;
            lightbox.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    });

    function closeLightbox() {
        lightbox.classList.remove('active');
        document.body.style.overflow = '';
    }

    lightboxClose?.addEventListener('click', closeLightbox);
    lightbox?.addEventListener('click', (e) => {
        if (e.target === lightbox) closeLightbox();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && lightbox.classList.contains('active')) {
            closeLightbox();
        }
    });
}

// ============================================
// Form Validation
// ============================================

function initFormValidation() {
    const forms = document.querySelectorAll('[data-validate]');

    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            let isValid = true;
            const inputs = form.querySelectorAll('[required]');

            inputs.forEach(input => {
                const errorEl = input.nextElementSibling;

                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('border-rose');
                    if (errorEl && errorEl.classList.contains('error-message')) {
                        errorEl.classList.remove('hidden');
                    }
                } else {
                    input.classList.remove('border-rose');
                    if (errorEl && errorEl.classList.contains('error-message')) {
                        errorEl.classList.add('hidden');
                    }
                }

                // Email validation
                if (input.type === 'email' && input.value) {
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailRegex.test(input.value)) {
                        isValid = false;
                        input.classList.add('border-rose');
                    }
                }

                // Password confirmation
                if (input.name === 'password2' || input.name === 'confirm_password') {
                    const password = form.querySelector('[name="password1"], [name="password"]');
                    if (password && input.value !== password.value) {
                        isValid = false;
                        input.classList.add('border-rose');
                        showToast('كلمات المرور غير متطابقة', 'error');
                    }
                }
            });

            if (!isValid) {
                e.preventDefault();
                showToast('يرجى ملء جميع الحقول المطلوبة', 'error');
            }
        });
    });
}

// ============================================
// Animations
// ============================================

function initAnimations() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('[data-animate]').forEach(el => {
        observer.observe(el);
    });
}

// ============================================
// Image Gallery (Product Detail)
// ============================================

function initImageGallery() {
    const thumbnails = document.querySelectorAll('.thumbnail');
    const mainImage = document.getElementById('mainImage');

    if (!mainImage || thumbnails.length === 0) return;

    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', () => {
            // Update main image
            mainImage.src = thumb.dataset.image || thumb.src;

            // Update active state
            thumbnails.forEach(t => t.classList.remove('ring-2', 'ring-sage'));
            thumb.classList.add('ring-2', 'ring-sage');
        });
    });
}

// ============================================
// Quantity Selector
// ============================================

function initQuantitySelector() {
    const selectors = document.querySelectorAll('.quantity-selector');

    selectors.forEach(selector => {
        const minusBtn = selector.querySelector('[data-minus]');
        const plusBtn = selector.querySelector('[data-plus]');
        const input = selector.querySelector('input');

        if (!minusBtn || !plusBtn || !input) return;

        minusBtn.addEventListener('click', () => {
            const currentVal = parseInt(input.value) || 1;
            if (currentVal > 1) {
                input.value = currentVal - 1;
                input.dispatchEvent(new Event('change'));
            }
        });

        plusBtn.addEventListener('click', () => {
            const currentVal = parseInt(input.value) || 1;
            const max = parseInt(input.max) || 999;
            if (currentVal < max) {
                input.value = currentVal + 1;
                input.dispatchEvent(new Event('change'));
            }
        });
    });
}

// ============================================
// Coupon Code
// ============================================

function initCouponCode() {
    const couponForm = document.getElementById('couponForm');
    const couponInput = document.getElementById('couponInput');
    const discountDisplay = document.getElementById('discountDisplay');

    if (!couponForm) return;

    couponForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const code = couponInput.value.trim();
        if (!code) {
            showToast('يرجى إدخال كود الخصم', 'warning');
            return;
        }

        // Simulate coupon validation (replace with actual API call)
        const validCoupons = {
            'WELCOME10': { discount: 10, type: 'percent' },
            'SAVE50': { discount: 50, type: 'fixed' }
        };

        const coupon = validCoupons[code.toUpperCase()];

        if (coupon) {
            showToast('تم تطبيق كود الخصم بنجاح', 'success');
            if (discountDisplay) {
                discountDisplay.classList.remove('hidden');
                discountDisplay.querySelector('.discount-value').textContent =
                    coupon.type === 'percent' ? `${coupon.discount}%` : formatPrice(coupon.discount);
            }
        } else {
            showToast('كود الخصم غير صالح', 'error');
        }
    });
}

// ============================================
// Initialize Everything
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Core functionality
    updateCartCount();
    updateWishlistCount();

    // UI Components
    initMobileMenu();
    initUserMenu();
    initSearchModal();
    initLightbox();
    initAnimations();
    initImageGallery();
    initQuantitySelector();
    initFormValidation();
    initCouponCode();

    // Product page specific
    initProductFilters();
});

// ============================================
// Export functions for external use
// ============================================

window.Souq = {
    // Cart
    addToCart,
    removeFromCart,
    updateCartQuantity,
    getCart,
    getCartTotal,
    clearCart,

    // Wishlist
    addToWishlist,
    removeFromWishlist,
    isInWishlist,
    toggleWishlist,
    getWishlist,

    // Utils
    showToast,
    formatPrice
};
