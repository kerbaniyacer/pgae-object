/**
 * سوق - JavaScript الرئيسي
 * Cart functions sync with Django server ONLY - No localStorage
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

    // Add item to cart (SERVER ONLY)
    async addToCart(product) {
        try {
            const response = await fetch('/cart/add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    product_id: product.id,
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
        }
    },

    // Remove item from cart (SERVER ONLY)
    async removeFromCart(productId) {
        try {
            const response = await fetch('/cart/remove/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ product_id: productId })
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
    async updateCartQuantity(productId, quantity) {
        try {
            const response = await fetch('/cart/update/', {
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

    // Update cart badge
    updateCartBadge(count) {
        const cartCountEl = document.getElementById('cartCount');
        const cartCountEl_1 = document.getElementById('cartCount_1');
        const badges = document.querySelectorAll('.cart-badge, [data-cart-count]');
        
        if (cartCountEl) {
            cartCountEl.textContent = count;
            cartCountEl.style.display = count > 0 ? 'flex' : 'none';
        }
        
        if (cartCountEl_1) {
            cartCountEl_1.textContent = count;
            cartCountEl_1.style.display = count > 0 ? 'flex' : 'none';
        }

        badges.forEach(badge => {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
        });
    },

    // Toggle wishlist
    async toggleWishlist(product) {
        try {
            const response = await fetch('/wishlist/toggle/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ product_id: product.id })
            });

            const data = await response.json();

            if (data.success) {
                this.showToast(data.message, 'success');
            } else {
                this.showToast(data.message || 'حدث خطأ', 'error');
            }

            return data;
        } catch (error) {
            console.error('Toggle wishlist error:', error);
            this.showToast('يرجى تسجيل الدخول أولاً', 'error');
            return { success: false };
        }
    },

    // Show toast notification
    showToast(message, type = 'info') {
        const existingToasts = document.querySelectorAll('.toast-notification');
        existingToasts.forEach(t => t.remove());

        const toast = document.createElement('div');
        toast.className = `toast-notification fixed bottom-4 left-4 z-50 px-6 py-3 rounded-xl shadow-lg text-white transition-all duration-300 translate-y-full opacity-0`;
        
        if (type === 'success') toast.classList.add('bg-sage');
        else if (type === 'error') toast.classList.add('bg-rose');
        else toast.classList.add('bg-gray-800');

        toast.innerHTML = `
            <div class="flex items-center gap-3">
                ${type === 'success' ? '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>' : ''}
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

    // Initialize - مسح localStorage وجلب من السيرفر
    init() {
        // مسح أي بيانات قديمة
        localStorage.removeItem('souq_cart');
        localStorage.removeItem('cart');
        
        // جلب العدد من السيرفر فقط
        this.fetchCartCountFromServer();
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

async function removeCartItem(productId) {
    if (confirm('هل تريد إزالة هذا المنتج من السلة؟')) {
        const result = await Souq.removeFromCart(productId);
        if (result.success) {
            window.location.reload();
        }
    }
}

async function updateCartItemQuantity(productId, quantity) {
    if (quantity < 1) {
        if (confirm('هل تريد إزالة هذا المنتج من السلة؟')) {
            await Souq.removeFromCart(productId);
            window.location.reload();
        }
        return;
    }
    
    const result = await Souq.updateCartQuantity(productId, quantity);
    if (result.success) {
        window.location.reload();
    }
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
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');

    if (userMenuBtn && userDropdown) {
        userMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle('hidden');
        });

        document.addEventListener('click', (e) => {
            if (!userDropdown.contains(e.target) && !userMenuBtn.contains(e.target)) {
                userDropdown.classList.add('hidden');
            }
        });
    }

    // ============================================
    // MOBILE MENU ✅ (حل مشكلة الزرين)
    // ============================================
    const mobileMenuBtns = document.querySelectorAll('#mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    const mobileMenuOverlay = document.getElementById('mobileMenuOverlay');
    const closeMobileMenu = document.getElementById('closeMobileMenu');

    mobileMenuBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            mobileMenu.classList.add('open');
            mobileMenuOverlay.classList.remove('hidden');
        });
    });

    if (closeMobileMenu) {
        closeMobileMenu.addEventListener('click', () => {
            mobileMenu.classList.remove('open');
            mobileMenuOverlay.classList.add('hidden');
        });
    }

    if (mobileMenuOverlay) {
        mobileMenuOverlay.addEventListener('click', () => {
            mobileMenu.classList.remove('open');
            mobileMenuOverlay.classList.add('hidden');
        });
    }

    // ============================================
    // Quantity selector handlers (كودك كما هو) ✅
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