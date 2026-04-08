/**
 * سوق - JavaScript الرئيسي
 * Cart & Wishlist functions sync with Django server ONLY
 */

// ============================================
// SOUQ NAMESPACE
// ============================================
const Souq = {
    // Get CSRF token from cookies
    getCSRFToken() {
        const name = 'csrftoken';
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                return cookie.substring(name.length + 1);
            }
        }
        return '';
    },

    // ============================================
    // CART FUNCTIONS
    // ============================================

    // Add item to cart (SERVER ONLY)
    async addToCart(product, buttonElement = null) {
        if (buttonElement) this.setLoading(buttonElement, true);
        try {
            const response = await fetch('/cart/add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    product_id: product.id,
                    variant_id: product.variant_id,
                    quantity: product.quantity || 1
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showToast(data.message || 'تمت إضافة المنتج للسلة', 'success');
                
                if (data.cart_count !== undefined) {
                    this.updateCartBadge(data.cart_count);
                } else {
                    this.fetchCartCountFromServer();
                }
            } else {
                this.showToast(data.message || 'حدث خطأ', 'error');
            }

            return data;
        } catch (error) {
            console.error('Add to cart error:', error);
            this.showToast('حدث خطأ في الاتصال', 'error');
            return { success: false };
        } finally {
            if (buttonElement) this.setLoading(buttonElement, false);
        }
    },

    // Remove item from cart (SERVER ONLY)
    async removeFromCart(variantId) {
        try {
            const response = await fetch('/cart/remove/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ variant_id: variantId })
            });

            const data = await response.json();

            if (data.success && data.cart_count !== undefined) {
                this.updateCartBadge(data.cart_count);
            }

            return data;
        } catch (error) {
            console.error('Remove from cart error:', error);
            return { success: false };
        }
    },

    // Update cart quantity (SERVER ONLY)
    async updateCartQuantity(variantId, quantity) {
        try {
            const response = await fetch('/cart/update/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    variant_id: variantId,
                    quantity: quantity
                })
            });

            const data = await response.json();

            if (data.success && data.cart_count !== undefined) {
                this.updateCartBadge(data.cart_count);
            }

            return data;
        } catch (error) {
            console.error('Update cart error:', error);
            return { success: false };
        }
    },

    // Fetch cart count from server
    async fetchCartCountFromServer() {
        try {
            const response = await fetch('/cart/count/');
            const data = await response.json();
            
            if (data.success && data.count !== undefined) {
                this.updateCartBadge(data.count);
                return data.count;
            }
        } catch (error) {
            console.error('Fetch cart count error:', error);
        }
        
        this.updateCartBadge(0);
        return 0;
    },

    // ✅ تحديث شارة السلة فقط
    updateCartBadge(count) {
        const cartCountEl = document.getElementById('cartCount');
        const cartCountEl_1 = document.getElementById('cartCount_1');
        const badges = document.querySelectorAll('[data-cart-count]');
        
        if (cartCountEl) {
            cartCountEl.textContent = count;
            cartCountEl.style.display = count > 0 ? 'flex' : 'none';
            if (count > 0) cartCountEl.classList.remove('hidden');
            else cartCountEl.classList.add('hidden');
        }
        
        if (cartCountEl_1) {
            cartCountEl_1.textContent = count;
            cartCountEl_1.style.display = count > 0 ? 'flex' : 'none';
            if (count > 0) cartCountEl_1.classList.remove('hidden');
            else cartCountEl_1.classList.add('hidden');
        }

        const cartCountEl_2 = document.getElementById('cartCount_2');
        if (cartCountEl_2) {
            cartCountEl_2.textContent = count;
            cartCountEl_2.style.display = count > 0 ? 'flex' : 'none';
            if (count > 0) cartCountEl_2.classList.remove('hidden');
            else cartCountEl_2.classList.add('hidden');
        }

        badges.forEach(badge => {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
        });
    },

    // ============================================
    // WISHLIST FUNCTIONS
    // ============================================

    // ✅ Toggle wishlist - تم إصلاحها بالكامل ومعالجة مشكلة الـ Spinner
    async toggleWishlist(productId, buttonElement) {
        if (buttonElement) {
            buttonElement.classList.add('pointer-events-none', 'opacity-50');
        }
        try {
            const response = await fetch('/wishlist/toggle/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    product_id: productId
                })
            });

            const data = await response.json();

            if (data.success) {
                // ✅ تحديث الحالات فوراً قبل أي عملية أخرى
                if (data.action === 'added') {
                    this.activateWishlistIcon(buttonElement);
                    this.showToast(data.message || 'تمت إضافة المنتج للمفضلة', 'success');
                } else if (data.action === 'removed') {
                    this.deactivateWishlistIcon(buttonElement);
                    this.showToast(data.message || 'تم إزالة المنتج من المفضلة', 'success');
                }
                
                // ✅ تحديث شارة المفضلة
                if (data.wishlist_count !== undefined) {
                    this.updateWishlistBadge(data.wishlist_count);
                } else {
                    this.fetchWishlistCountFromServer();
                }
            } else {
                if (data.redirect) {
                    this.showToast(data.message || 'يرجى تسجيل الدخول', 'error');
                    setTimeout(() => {
                        window.location.href = data.redirect;
                    }, 1000);
                } else {
                    this.showToast(data.message || 'حدث خطأ', 'error');
                }
            }

            return data;
        } catch (error) {
            console.error('Toggle wishlist error:', error);
            this.showToast('يرجى تسجيل الدخول أولاً', 'error');
            return { success: false };
        } finally {
            if (buttonElement) {
                buttonElement.classList.remove('pointer-events-none', 'opacity-50');
            }
        }
    },

    // Remove from wishlist
    async removeFromWishlist(productId) {
        try {
            const response = await fetch('/wishlist/remove/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ product_id: productId })
            });

            const data = await response.json();

            if (data.success && data.wishlist_count !== undefined) {
                this.updateWishlistBadge(data.wishlist_count);  // ✅ تم الإصلاح
            }

            return data;
        } catch (error) {
            console.error('Remove from wishlist error:', error);
            return { success: false };
        }
    },

    // Update wishlist quantity
    async updateWishlistQuantity(productId, quantity) {
        try {
            const response = await fetch('/wishlist/update/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    product_id: productId,
                    quantity: quantity
                })
            });

            const data = await response.json();

            if (data.success && data.wishlist_count !== undefined) {
                this.updateWishlistBadge(data.wishlist_count);  // ✅ تم الإصلاح
            }

            return data;
        } catch (error) {
            console.error('Update wishlist error:', error);
            return { success: false };
        }
    },

    // ✅ Fetch wishlist count - تم إصلاح data.count
    async fetchWishlistCountFromServer() {
        try {
            const response = await fetch('/wishlist/count/');
            const data = await response.json();
            
            if (data.success && data.count !== undefined) {  // ✅ كان data.Wcount
                this.updateWishlistBadge(data.count);
                return data.count;
            }
        } catch (error) {
            console.error('Fetch wishlist count error:', error);
        }
        
        this.updateWishlistBadge(0);
        return 0;
    },

    // ✅ تحديث شارة المفضلة فقط - اسم مختلف عن شارة السلة
    updateWishlistBadge(count) {
        const wishlistCountEl = document.getElementById('wishlistCount');
        const wishlistCountEl_1 = document.getElementById('wishlistCount_1');
        const badges = document.querySelectorAll('[data-wishlist-count]');
        
        if (wishlistCountEl) {
            wishlistCountEl.textContent = count;
            wishlistCountEl.style.display = count > 0 ? 'flex' : 'none';
        }
        
        if (wishlistCountEl_1) {
            wishlistCountEl_1.textContent = count;
            wishlistCountEl_1.style.display = count > 0 ? 'flex' : 'none';
        }

        badges.forEach(badge => {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
        });
    },

    // ✅ NEW: تفعيل أيقونة المفضلة (قلب مملوء)
    activateWishlistIcon(btn) {
        if (!btn) return;
        
        // تحديث SVG
        const svg = btn.querySelector('svg');
        if (svg) {
            svg.setAttribute('fill', 'currentColor');  // ✅ ملء القلب
            svg.setAttribute('stroke', 'currentColor');
            // تأكد من عدم وجود fill none
            svg.classList.remove('fill-none');
        }
        
        // تحديث كلاسات الزر
        btn.classList.add('text-rose');
        btn.classList.remove('text-gray-500', 'text-gray-400', 'text-text-placeholder');
    },

    // ✅ NEW: إلغاء تفعيل أيقونة المفضلة (قلب فارغ)
    deactivateWishlistIcon(btn) {
        if (!btn) return;
        
        // تحديث SVG
        const svg = btn.querySelector('svg');
        if (svg) {
            svg.setAttribute('fill', 'none');  // ✅ إفراغ القلب
            svg.setAttribute('stroke', 'currentColor');
        }
        
        // تحديث كلاسات الزر
        btn.classList.remove('text-rose');
        btn.classList.add('text-gray-500'); // الاسترجاع للون الرمادي المتعارف عليه
        btn.classList.remove('text-gray-400', 'text-text-placeholder');
    },

    // ============================================
    // CONFIRMATION DIALOG (CUSTOM MODAL)
    // ============================================

    showConfirm(message, onConfirm) {
        // Remove existing if any
        const existing = document.getElementById('customConfirmModal');
        if (existing) existing.remove();

        const modal = document.createElement('div');
        modal.id = 'customConfirmModal';
        modal.className = 'fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm transition-opacity duration-300';
        modal.innerHTML = `
            <div class="bg-surface dark:bg-dark-secondary rounded-2xl shadow-2xl p-6 max-w-sm w-full transform scale-95 opacity-0 transition-all duration-300">
                <div class="w-12 h-12 bg-sage-light dark:bg-sage/20 rounded-full flex items-center justify-center text-sage mx-auto mb-4">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <h3 class="text-lg font-bold text-text-primary dark:text-dark-text text-center mb-2">تأكيد الإجراء</h3>
                <p class="text-text-secondary dark:text-dark-text-secondary text-center mb-6">${message}</p>
                <div class="flex gap-3">
                    <button id="confirmCancel" class="flex-1 px-4 py-2 bg-page-bg dark:bg-dark-tertiary text-text-primary dark:text-dark-text rounded-xl font-medium hover:bg-surface-dark transition-colors">إلغاء</button>
                    <button id="confirmOk" class="flex-1 px-4 py-2 bg-sage text-white rounded-xl font-medium hover:bg-sage-dark transition-colors shadow-lg shadow-sage/20">تأكيد</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Animate in
        requestAnimationFrame(() => {
            modal.querySelector('div').classList.remove('scale-95', 'opacity-0');
        });

        const close = () => {
            modal.querySelector('div').classList.add('scale-95', 'opacity-0');
            modal.classList.add('opacity-0');
            setTimeout(() => modal.remove(), 300);
        };

        modal.getElementById('confirmCancel').onclick = close;
        modal.getElementById('confirmOk').onclick = () => {
            close();
            onConfirm();
        };

        // Close on overlay click
        modal.onclick = (e) => {
            if (e.target === modal) close();
        };
    },

    // ============================================
    // TOAST NOTIFICATION
    // ============================================

    showToast(message, type = 'info') {
        const existingToasts = document.querySelectorAll('.toast-notification');
        existingToasts.forEach(t => t.remove());

        const toast = document.createElement('div');
        toast.className = `toast-notification fixed bottom-4 right-4 z-50 px-6 py-3 rounded-xl shadow-lg text-white transition-all duration-300 translate-y-full opacity-0`;
        
        if (type === 'success') toast.classList.add('bg-sage');
        else if (type === 'error') toast.classList.add('bg-rose');
        else toast.classList.add('bg-gray-800');

        const icon = type === 'success' 
            ? '<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>'
            : type === 'error'
            ? '<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>'
            : '';

        toast.innerHTML = `
            <div class="flex items-center gap-3">
                ${icon}
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(toast);

        requestAnimationFrame(() => {
            toast.classList.remove('translate-y-full', 'opacity-0');
        });

        setTimeout(() => {
            toast.classList.add('translate-y-full', 'opacity-0');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    // ============================================
    // INITIALIZATION
    // ============================================

    // Helper: Set button loading state
    setLoading(btn, isLoading) {
        if (!btn) return;
        if (isLoading) {
            btn.classList.add('pointer-events-none', 'opacity-70');
            const originalContent = btn.innerHTML;
            btn.dataset.originalContent = originalContent;
            btn.innerHTML = `
                <svg class="animate-spin h-4 w-4 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
            `;
        } else {
            btn.classList.remove('pointer-events-none', 'opacity-70');
            if (btn.dataset.originalContent) {
                btn.innerHTML = btn.dataset.originalContent;
            }
        }
    },

    init() {
        // ✅ مسح أي بيانات قديمة - تم إصلاح الأسماء
        localStorage.removeItem('souq_cart');
        localStorage.removeItem('cart');
        localStorage.removeItem('souq_wishlist');  // ✅ كان removeWishlistItem
        localStorage.removeItem('wishlist');        // ✅ كان removeWishlistItem
        
        // جلب العدد من السيرفر فقط
        this.fetchCartCountFromServer();
        this.fetchWishlistCountFromServer();  // ✅ إضافة استدعاء المفضلة
    }
};

// ============================================
// GLOBAL FUNCTIONS (for onclick handlers)
// ============================================

async function addToCartWithQuantity(productId, name, price, image) {
    const quantityInput = document.querySelector('input[name="quantity"]');
    const quantity = quantityInput ? parseInt(quantityInput.value) || 1 : 1;
    
    await Souq.addToCart({
        id: productId,
        name: name,
        price: price,
        image: image,
        quantity: quantity
    });
}

// ✅ الدالة الرئيسية للمفضلة - تستقبل الزر لتغيير الأيقونة
async function toggleWishlist(productId, buttonElement) {
    await Souq.toggleWishlist(productId, buttonElement);
}

async function removeCartItem(productId) {
    Souq.showConfirm('هل تريد إزالة هذا المنتج من السلة؟', async () => {
        const result = await Souq.removeFromCart(productId);
        if (result.success) {
            window.location.reload();
        }
    });
}

async function removeWishlistItem(productId) {
    Souq.showConfirm('هل تريد إزالة هذا المنتج من قائمة المفضلة؟', async () => {
        const result = await Souq.removeFromWishlist(productId);
        if (result.success) {
            window.location.reload();
        }
    });
}

async function updateCartItemQuantity(productId, quantity) {
    if (quantity < 1) {
        Souq.showConfirm('هل تريد إزالة هذا المنتج من السلة؟', async () => {
            await Souq.removeFromCart(productId);
            window.location.reload();
        });
        return;
    }
    
    const result = await Souq.updateCartQuantity(productId, quantity);
    if (result.success) {
        window.location.reload();
    }
}

async function updateWishlistItemQuantity(productId, quantity) {
    if (quantity < 1) {
        Souq.showConfirm('هل تريد إزالة هذا المنتج من قائمة المفضلة؟', async () => {
            await Souq.removeFromWishlist(productId);
            window.location.reload();
        });
        return;
    }
    
    const result = await Souq.updateWishlistQuantity(productId, quantity);
    if (result.success) {
        window.location.reload();
    }
}

async function buyNow(productId, name, price, image) {
    const quantityInput = document.querySelector('input[name="quantity"]');
    const quantity = quantityInput ? parseInt(quantityInput.value) || 1 : 1;
    
    await Souq.addToCart({
        id: productId,
        name: name,
        price: price,
        image: image,
        quantity: quantity
    });
    
    window.location.href = '/cart/';
}

function getCSRFToken() {
    return Souq.getCSRFToken();
}

// دعم الأسماء القديمة
const removeItem = removeCartItem;
const updateQuantity = updateCartItemQuantity;

// ============================================
// INITIALIZE ON DOM READY
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    Souq.init();

    // ============================================
    // USER DROPDOWN MENU ✅
    // ============================================
    const userMenuBtns = document.querySelectorAll('#userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');

    if (userMenuBtns.length > 0 && userDropdown) {
        userMenuBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                userDropdown.classList.toggle('hidden');
                // Optional: Add animation class
                userDropdown.classList.add('animate-dropdown');
            });
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            let isClickInside = false;
            userMenuBtns.forEach(btn => {
                if (btn.contains(e.target)) isClickInside = true;
            });
            
            if (!isClickInside && !userDropdown.contains(e.target)) {
                userDropdown.classList.add('hidden');
            }
        });
    }

    // ============================================
    // MOBILE MENU ✅
    // ============================================
    const mobileMenuBtns = document.querySelectorAll('.mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobileMenu');
    const mobileMenuOverlay = document.getElementById('mobileMenuOverlay');
    const closeMobileMenu = document.getElementById('closeMobileMenu');

    if (mobileMenu && !mobileMenu.dataset.initialized) {
        mobileMenu.dataset.initialized = 'true';

        const openHandler = (e) => {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            mobileMenu.classList.add('open');
            if (mobileMenuOverlay) {
                mobileMenuOverlay.classList.remove('hidden');
                mobileMenuOverlay.style.display = 'block';
                mobileMenuOverlay.style.opacity = '1';
                mobileMenuOverlay.style.pointerEvents = 'auto';
            }
        };

        const closeHandler = (e) => {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            mobileMenu.classList.remove('open');
            if (mobileMenuOverlay) {
                mobileMenuOverlay.classList.add('hidden');
                mobileMenuOverlay.style.display = 'none';
                mobileMenuOverlay.style.opacity = '0';
                mobileMenuOverlay.style.pointerEvents = 'none';
            }
        };

        mobileMenuBtns.forEach(btn => {
            btn.onclick = openHandler;
        });

        if (closeMobileMenu) {
            closeMobileMenu.onclick = closeHandler;
        }
        if (mobileMenuOverlay) {
            mobileMenuOverlay.onclick = closeHandler;
        }

        // إغلاق عند الضغط على مفتاح Esc
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && mobileMenu.classList.contains('open')) {
                closeHandler();
            }
        });
    }

    // ============================================
    // QUANTITY SELECTORS ✅
    // ============================================
    document.querySelectorAll('[data-minus]').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = btn.parentElement.querySelector('input[name="quantity"]');
            if (input) {
                const currentVal = parseInt(input.value) || 1;
                if (currentVal > 1) {
                    input.value = currentVal - 1;
                }
            }
        });
    });

    document.querySelectorAll('[data-plus]').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = btn.parentElement.querySelector('input[name="quantity"]');
            if (input) {
                const currentVal = parseInt(input.value) || 1;
                const max = parseInt(input.max) || 99;
                if (currentVal < max) {
                    input.value = currentVal + 1;
                }
            }
        });
    });
});