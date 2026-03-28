/**
 * UI Components JavaScript - متجر سوق
 * Handles: Truck Loader, Help Button, Cart Button, Search Loading
 */

(function() {
    'use strict';

    // ============================================
    // Helper: Check if current page is auth page
    // ============================================
    
    function isAuthPage() {
        const path = window.location.pathname;
        const authPages = ['/login/', '/register/', '/forgot-password/', '/reset-password/', '/change-password/'];
        return authPages.some(page => path.includes(page));
    }

    // ============================================
    // Truck Loader Functions
    // ============================================

    const TruckLoader = {
        overlay: null,

        init: function() {
            // Create loader HTML
            const loaderHTML = `
                <div id="truckLoaderOverlay" class="truck-loader-overlay">
                    <div class="truck-wrapper">
                        <div class="smoke"></div>
                        <div class="smoke"></div>
                        <div class="smoke"></div>
                        <div class="truck">
                            <div class="cargo"></div>
                            <div class="cabin"></div>
                            <div class="wheel wheel-front"></div>
                            <div class="wheel wheel-back"></div>
                        </div>
                        <div class="road"></div>
                    </div>
                    <p class="truck-loader-text">
                        <span id="loaderMessage">جاري معالجة طلبك</span>
                        <span class="dots"></span>
                    </p>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', loaderHTML);
            this.overlay = document.getElementById('truckLoaderOverlay');
        },

        show: function(message = 'جاري معالجة طلبك') {
            if (!this.overlay) this.init();
            
            const messageEl = document.getElementById('loaderMessage');
            if (messageEl) messageEl.textContent = message;
            
            this.overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        },

        hide: function() {
            if (this.overlay) {
                this.overlay.classList.remove('active');
                document.body.style.overflow = '';
            }
        },

        showFor: function(duration = 3000, message = 'جاري معالجة طلبك') {
            this.show(message);
            return new Promise(resolve => {
                setTimeout(() => {
                    this.hide();
                    resolve();
                }, duration);
            });
        }
    };

    // ============================================
    // Help Button Functions
    // ============================================

    const HelpButton = {
        container: null,

        init: function() {
            // Don't show on auth pages
            if (isAuthPage()) return;
            
            // Check if already exists
            if (document.getElementById('helpBtnContainer')) return;

            const helpHTML = `
                <div id="helpBtnContainer" class="help-btn-container">
                    <button class="help-btn" id="helpBtn" title="طلب المساعدة" aria-label="طلب المساعدة">
                        <div class="sparkles">
                            <span class="sparkle"></span>
                            <span class="sparkle"></span>
                            <span class="sparkle"></span>
                            <span class="sparkle"></span>
                            <span class="sparkle"></span>
                            <span class="sparkle"></span>
                        </div>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                            <line x1="12" y1="17" x2="12.01" y2="17"></line>
                        </svg>
                        <span class="help-tooltip">تحتاج مساعدة؟</span>
                    </button>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', helpHTML);
            this.container = document.getElementById('helpBtnContainer');

            const btn = document.getElementById('helpBtn');
            if (btn) {
                btn.addEventListener('click', this.handleClick);
            }
        },

        handleClick: function(e) {
            e.preventDefault();
            if (typeof Souq !== 'undefined' && Souq.showToast) {
                Souq.showToast('للمساعدة، تواصل معنا عبر WhatsApp أو البريد الإلكتروني', 'info');
            } else {
                alert('للمساعدة، تواصل معنا عبر:\nWhatsApp: +966 50 000 0000\nالبريد: support@souq.com');
            }
        },

        show: function() {
            if (this.container) {
                this.container.style.display = 'block';
            }
        },

        hide: function() {
            if (this.container) {
                this.container.style.display = 'none';
            }
        }
    };

    // ============================================
    // Floating Cart Button Functions
    // ============================================

    const FloatingCartButton = {
        container: null,

        init: function() {
            // Don't show on auth pages
            if (isAuthPage()) return;
            
            // Check if already exists
            if (document.getElementById('floatingCartBtnContainer')) return;

            const cartHTML = `
                <div id="floatingCartBtnContainer" class="floating-cart-btn-container">
                    <button class="floating-cart-btn" id="floatingCartBtn" title="عرض السلة" aria-label="عرض السلة">
                        <div class="sparkles-cart">
                            <span class="sparkle_cart"></span>
                            <span class="sparkle_cart"></span>
                            <span class="sparkle_cart"></span>
                            <span class="sparkle_cart"></span>
                            <span class="sparkle_cart"></span>
                            <span class="sparkle_cart"></span>
                        </div>
                        <!-- Cart Icon -->
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
                            <line x1="3" y1="6" x2="21" y2="6"></line>
                            <path d="M16 10a4 4 0 0 1-8 0"></path>
                        </svg>
                        <!-- Cart Badge -->
                        <span class="floating-cart-badge" id="floatingCartBadge">0</span>
                        <span class="cart-tooltip">السلة</span>
                    </button>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', cartHTML);
            this.container = document.getElementById('floatingCartBtnContainer');

            const btn = document.getElementById('floatingCartBtn');
            if (btn) {
                btn.addEventListener('click', this.handleClick);
            }

            // Fetch initial cart count
            this.updateBadge();
        },

        handleClick: function(e) {
            e.preventDefault();
            window.location.href = '/cart/';
        },

        updateBadge: async function() {
            try {
                const response = await fetch('/cart/count/');
                const data = await response.json();
                
                if (data.success) {
                    const badge = document.getElementById('floatingCartBadge');
                    if (badge) {
                        badge.textContent = data.count;
                        badge.style.display = data.count > 0 ? 'flex' : 'none';
                    }
                }
            } catch (error) {
                console.error('Error fetching cart count:', error);
            }
        },

        show: function() {
            if (this.container) {
                this.container.style.display = 'block';
            }
        },

        hide: function() {
            if (this.container) {
                this.container.style.display = 'none';
            }
        }
    };

    // ============================================
    // Search Loading State
    // ============================================

    const SearchLoading = {
        init: function() {
            const searchInput = document.getElementById('searchInput');

            if (searchInput) {
                searchInput.addEventListener('input', debounce(function() {
                    // Search logic here
                }, 300));
            }
        }
    };

    // ============================================
    // Order Confirmation Handler
    // ============================================

    function setupOrderConfirmation() {
        const checkoutForm = document.getElementById('checkoutForm');
        
        if (checkoutForm) {
            checkoutForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                TruckLoader.showFor(3000, 'جاري تأكيد طلبك').then(function() {
                    checkoutForm.submit();
                });
            });
        }
    }

    // ============================================
    // Utility Functions
    // ============================================

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // ============================================
    // Initialize on DOM Ready
    // ============================================

    function init() {
        TruckLoader.init();
        HelpButton.init();
        FloatingCartButton.init();
        SearchLoading.init();
        setupOrderConfirmation();
    }

    // Run initialization
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ============================================
    // Expose to Global Scope
    // ============================================

    window.SouqUI = {
        TruckLoader: TruckLoader,
        HelpButton: HelpButton,
        FloatingCartButton: FloatingCartButton,
        showLoading: function(message) {
            TruckLoader.show(message);
        },
        hideLoading: function() {
            TruckLoader.hide();
        },
        showLoadingFor: function(duration, message) {
            return TruckLoader.showFor(duration, message);
        },
        updateCartBadge: function() {
            FloatingCartButton.updateBadge();
        }
    };

})();
