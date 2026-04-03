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

    // ✅ تحديث شارة السلة فقط
    updateCartBadge(count) {
        const cartCountEl = document.getElementById('cartCount');
        const cartCountEl_1 = document.getElementById('cartCount_1');
        const badges = document.querySelectorAll('[data-cart-count]');
        
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

    // ============================================
    // WISHLIST FUNCTIONS
    // ============================================

    // ✅ Toggle wishlist - تم إصلاحها بالكامل
    async toggleWishlist(productId, buttonElement) {
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
                // ✅ رسالة مختلفة حسب الإجراء
                if (data.action === 'added') {
                    this.showToast(data.message || 'تمت إضافة المنتج للمفضلة', 'success');
                    this.activateWishlistIcon(buttonElement);
                } else if (data.action === 'removed') {
                    this.showToast(data.message || 'تم إزالة المنتج من المفضلة', 'success');
                    this.deactivateWishlistIcon(buttonElement);
                }
                
                // ✅ تحديث شارة المفضلة
                if (data.wishlist_count !== undefined) {
                    this.updateWishlistBadge(data.wishlist_count);
                } else {
                    this.fetchWishlistCountFromServer();
                }
            } else {
                // ✅ التعامل مع حالة عدم تسجيل الدخول
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
        }
        
        // تحديث كلاسات الزر
        btn.classList.add('text-rose');
        btn.classList.remove('text-gray-400', 'text-text-placeholder');
    },

    // ✅ NEW: إلغاء تفعيل أيقونة المفضلة (قلب فارغ)
    deactivateWishlistIcon(btn) {
        if (!btn) return;
        
        // تحديث SVG
        const svg = btn.querySelector('svg');
        if (svg) {
            svg.setAttribute('fill', 'none');  // ✅ إفراغ القلب
        }
        
        // تحديث كلاسات الزر
        btn.classList.remove('text-rose');
        btn.classList.add('text-gray-400', 'text-text-placeholder');
    },

    // ============================================
    // TOAST NOTIFICATION
    // ============================================

    showToast(message, type = 'info') {
        const existingToasts = document.querySelectorAll('.toast-notification');
        existingToasts.forEach(t => t.remove());

        const toast = document.createElement('div');
        toast.className = `toast-notification fixed bottom-4 left-4 z-50 px-6 py-3 rounded-xl shadow-lg text-white transition-all duration-300 translate-y-full opacity-0`;
        
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
    if (confirm('هل تريد إزالة هذا المنتج من السلة؟')) {
        const result = await Souq.removeFromCart(productId);
        if (result.success) {
            window.location.reload();
        }
    }
}

async function removeWishlistItem(productId) {
    if (confirm('هل تريد إزالة هذا المنتج من قائمة المفضلة؟')) {
        const result = await Souq.removeFromWishlist(productId);
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

async function updateWishlistItemQuantity(productId, quantity) {
    if (quantity < 1) {
        if (confirm('هل تريد إزالة هذا المنتج من قائمة المفضلة؟')) {
            await Souq.removeFromWishlist(productId);
            window.location.reload();
        }
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
    // MOBILE MENU ✅
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