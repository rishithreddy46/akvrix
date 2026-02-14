/* ===== AKVRIX — Shared App Logic ===== */
document.addEventListener('DOMContentLoaded', () => {
    initLoader(); initNav(); initDarkMode(); initSearch(); updateCartBadge(); initAOS();
});

function initLoader() {
    const l = document.getElementById('loader');
    if (!l) return;
    window.addEventListener('load', () => setTimeout(() => l.classList.add('hidden'), 600));
    setTimeout(() => l.classList.add('hidden'), 2500);
}

function initNav() {
    const nav = document.querySelector('.navbar');
    const toggle = document.querySelector('.nav-toggle');
    const menu = document.querySelector('.nav-menu');
    const overlay = document.querySelector('.nav-overlay');
    if (nav) {
        let last = 0;
        window.addEventListener('scroll', () => {
            const y = window.scrollY;
            nav.classList.toggle('scrolled', y > 50);
            nav.classList.toggle('nav-hidden', y > last && y > 200);
            last = y;
        });
    }
    if (toggle && menu) {
        toggle.addEventListener('click', () => {
            menu.classList.toggle('open'); toggle.classList.toggle('active');
            overlay && overlay.classList.toggle('open');
            document.body.classList.toggle('no-scroll');
        });
    }
    if (overlay) overlay.addEventListener('click', () => {
        menu && menu.classList.remove('open'); toggle && toggle.classList.remove('active');
        overlay.classList.remove('open'); document.body.classList.remove('no-scroll');
    });
}

function initDarkMode() {
    const btn = document.getElementById('darkModeToggle');
    const saved = localStorage.getItem('akvrix_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
    if (btn) {
        btn.innerHTML = saved === 'dark' ? '<i class="ri-sun-line"></i>' : '<i class="ri-moon-line"></i>';
        btn.addEventListener('click', () => {
            const t = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', t);
            localStorage.setItem('akvrix_theme', t);
            btn.innerHTML = t === 'dark' ? '<i class="ri-sun-line"></i>' : '<i class="ri-moon-line"></i>';
        });
    }
}

function initSearch() {
    const btn = document.getElementById('searchToggle'), modal = document.getElementById('searchModal');
    const close = document.getElementById('searchClose'), input = document.getElementById('searchInput');
    if (!btn || !modal) return;
    btn.addEventListener('click', () => { modal.classList.add('open'); input && input.focus(); });
    close && close.addEventListener('click', () => modal.classList.remove('open'));
    modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('open'); });
}

function updateCartBadge() {
    const badges = document.querySelectorAll('.cart-count');
    const count = parseInt(document.body.dataset.cartCount || '0');
    badges.forEach(b => { b.textContent = count; b.style.display = count > 0 ? 'flex' : 'none'; });
}

function initAOS() {
    const els = document.querySelectorAll('[data-aos]');
    if (!els.length) return;
    const obs = new IntersectionObserver(entries => {
        entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('aos-animate'); obs.unobserve(e.target); } });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
    els.forEach(el => obs.observe(el));
}

function starsHTML(r) {
    let s = ''; for (let i = 1; i <= 5; i++) s += `<i class="ri-star-${i <= Math.floor(r) ? 'fill' : i - .5 <= r ? 'half-fill' : 'line'}"></i>`; return s;
}

function showToast(msg, type = 'success') {
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.innerHTML = `<i class="ri-${type === 'success' ? 'check' : 'information'}-line"></i><span>${msg}</span>`;
    document.body.appendChild(t);
    requestAnimationFrame(() => t.classList.add('show'));
    setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 300); }, 3000);
}

function getCookie(name) {
    let v = null;
    document.cookie.split(';').forEach(c => { c = c.trim(); if (c.startsWith(name + '=')) v = decodeURIComponent(c.substring(name.length + 1)); });
    return v;
}

async function apiCall(url, data) {
    const res = await fetch(url, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(data)
    });
    const json = await res.json();
    if (json.cart_count !== undefined) {
        document.body.dataset.cartCount = json.cart_count;
        updateCartBadge();
    }
    return json;
}

async function addToCartAPI(productId, size, color, quantity) {
    const r = await apiCall('/api/cart/add/', { product_id: productId, size, color, quantity });
    if (r.success) showToast('Added to cart!');
    return r;
}

async function toggleWishlistAPI(productId, btn) {
    const r = await apiCall('/api/wishlist/toggle/', { product_id: productId });
    if (r.success) {
        if (btn) { btn.classList.toggle('active', r.added); btn.innerHTML = `<i class="ri-heart-${r.added ? 'fill' : 'line'}"></i>`; }
        showToast(r.added ? 'Added to wishlist' : 'Removed from wishlist');
    }
    return r;
}
