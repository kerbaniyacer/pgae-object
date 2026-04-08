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
            // Check if already exists
            if (document.getElementById('truckLoaderOverlay')) return;
            
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
    // Help Modal Functions
    // ============================================

    const HelpModal = {
        modal: null,
        closeBtn: null,
        pageUrlInput: null,
        initialized: false,

        init: function() {
            // Don't initialize on auth pages
            if (isAuthPage()) return;
            
            // Prevent double initialization
            if (this.initialized) return;
            this.initialized = true;

            this.modal = document.getElementById('helpModal');
            this.closeBtn = this.modal ? this.modal.querySelector('.close-btn') : null;
            this.pageUrlInput = document.getElementById('page_url');
            
            if (!this.modal) {
                console.warn('helpModal not found!');
                return;
            }

            // Set current page URL
            if (this.pageUrlInput) {
                this.pageUrlInput.value = window.location.href;
            }

            // Close button handler
            if (this.closeBtn) {
                this.closeBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.hide();
                });
            }

            // Click outside modal to close
            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.hide();
                }
            });

            // ESC key to close
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.modal.style.display === 'flex') {
                    this.hide();
                }
            });

            // Attach click handler to help button
            const helpBtn = document.getElementById('helpBtn');
            if (helpBtn) {
                helpBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.show();
                });
                console.log('Help button handler attached');
            } else {
                console.warn('helpBtn not found!');
            }
        },

        show: function() {
            if (this.modal) {
                this.modal.style.display = 'flex';
                // Update page URL when showing
                if (this.pageUrlInput) {
                    this.pageUrlInput.value = window.location.href;
                }
            }
        },

        hide: function() {
            if (this.modal) {
                this.modal.style.display = 'none';
            }
        }
    };

    // ============================================
    // Cart Badge Update Functions
    // ============================================

    const CartBadge = {
        init: function() {
            if (isAuthPage()) return;
            this.updateBadge();
        },

        updateBadge: async function() {
            try {
                const response = await fetch('/cart/count/');
                const data = await response.json();
                
                if (data.success) {
                    const count = data.count;
                    
                    // Update all cart badges in the page
                    const badges = document.querySelectorAll('#cartCount, #cartCount_2, #floatingCartBadge');
                    badges.forEach(badge => {
                        badge.textContent = count;
                        if (count > 0) {
                            badge.classList.remove('hidden');
                            badge.style.display = 'flex';
                        } else {
                            badge.classList.add('hidden');
                            badge.style.display = 'none';
                        }
                    });
                }
            } catch (error) {
                console.error('Error fetching cart count:', error);
            }
        }
    };

    // ============================================
    // Search Modal Functions
    // ============================================

    const SearchModal = {
        init: function() {
            const searchBtn = document.getElementById('searchBtn');
            const searchModal = document.getElementById('searchModal');
            const closeSearch = document.getElementById('closeSearch');
            const searchInput = document.getElementById('searchInput');

            if (!searchBtn || !searchModal) return;

            searchBtn.addEventListener('click', () => {
                searchModal.style.display = 'flex';
                if (searchInput) {
                    setTimeout(() => searchInput.focus(), 100);
                }
            });

            if (closeSearch) {
                closeSearch.addEventListener('click', () => {
                    searchModal.style.display = 'none';
                });
            }

            searchModal.addEventListener('click', (e) => {
                if (e.target === searchModal) {
                    searchModal.style.display = 'none';
                }
            });

            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && searchModal.style.display === 'flex') {
                    searchModal.style.display = 'none';
                }
            });
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
        if (window.SouqUIInitialized) return;
        window.SouqUIInitialized = true;
        
        console.log('SouqUI initializing...');
        TruckLoader.init();
        HelpModal.init();
        CartBadge.init();
        SearchModal.init();
        setupOrderConfirmation();
        console.log('SouqUI initialized');
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
        HelpModal: HelpModal,
        CartBadge: CartBadge,
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
            CartBadge.updateBadge();
        },
        showHelpModal: function() {
            HelpModal.show();
        },
        hideHelpModal: function() {
            HelpModal.hide();
        }
    };

})();

