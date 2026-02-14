from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import models
from .models import Product, CartItem, Wishlist, Order, OrderItem, Review
import json, random, string

def get_session(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key

def cart_count(request):
    sk = get_session(request)
    return CartItem.objects.filter(session_key=sk).aggregate(total=models.Sum('quantity'))['total'] or 0

def base_context(request):
    return {'cart_count': cart_count(request)}

# ===== PAGES =====

def home(request):
    ctx = base_context(request)
    ctx['best_sellers'] = Product.objects.filter(badge='Best Seller').order_by('-rating')[:8]
    if ctx['best_sellers'].count() < 4:
        ctx['best_sellers'] = Product.objects.all().order_by('-rating')[:8]
    ctx['categories'] = [
        {'name': 'Streetwear', 'slug': 'streetwear', 'img': 'https://images.unsplash.com/photo-1617137968427-85924c800a22?w=600&h=800&fit=crop'},
        {'name': 'Essentials', 'slug': 'essentials', 'img': 'https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?w=600&h=800&fit=crop'},
        {'name': 'New Arrivals', 'slug': 'new', 'img': 'https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=600&h=800&fit=crop'},
        {'name': 'Limited Edition', 'slug': 'limited', 'img': 'https://images.unsplash.com/photo-1520367445093-50dc08a59d9d?w=600&h=800&fit=crop'},
    ]
    ctx['wishlist_ids'] = list(Wishlist.objects.filter(session_key=get_session(request)).values_list('product_id', flat=True))
    return render(request, 'store/home.html', ctx)

def shop(request):
    ctx = base_context(request)
    products = Product.objects.all()
    cat = request.GET.get('cat')
    if cat:
        products = products.filter(category=cat)
    sort = request.GET.get('sort', 'featured')
    if sort == 'low': products = products.order_by('price')
    elif sort == 'high': products = products.order_by('-price')
    elif sort == 'newest': products = products.order_by('-created_at')
    elif sort == 'rating': products = products.order_by('-rating')
    ctx['products'] = products
    ctx['current_cat'] = cat or ''
    ctx['current_sort'] = sort
    ctx['wishlist_ids'] = list(Wishlist.objects.filter(session_key=get_session(request)).values_list('product_id', flat=True))
    return render(request, 'store/shop.html', ctx)

def product_detail(request, slug):
    ctx = base_context(request)
    p = get_object_or_404(Product, slug=slug)
    ctx['product'] = p
    ctx['related'] = Product.objects.filter(category=p.category).exclude(id=p.id)[:4]
    ctx['reviews'] = p.reviews.all().order_by('-created_at')
    ctx['in_wishlist'] = Wishlist.objects.filter(session_key=get_session(request), product=p).exists()
    return render(request, 'store/product_detail.html', ctx)

def cart_page(request):
    ctx = base_context(request)
    items = CartItem.objects.filter(session_key=get_session(request)).select_related('product')
    subtotal = sum(i.total for i in items)
    shipping = 0 if subtotal > 150 else 12
    ctx['items'] = items
    ctx['subtotal'] = subtotal
    ctx['shipping'] = shipping
    ctx['total'] = subtotal + shipping
    return render(request, 'store/cart.html', ctx)

def checkout_page(request):
    ctx = base_context(request)
    items = CartItem.objects.filter(session_key=get_session(request)).select_related('product')
    subtotal = sum(i.total for i in items)
    shipping = 0 if subtotal > 150 else 12
    ctx['items'] = items
    ctx['subtotal'] = subtotal
    ctx['shipping'] = shipping
    ctx['total'] = subtotal + shipping
    return render(request, 'store/checkout.html', ctx)

def login_page(request):
    return render(request, 'store/login.html', base_context(request))

def register_page(request):
    return render(request, 'store/register.html', base_context(request))

def account_page(request):
    ctx = base_context(request)
    ctx['orders'] = Order.objects.filter(session_key=get_session(request)).order_by('-created_at')
    ctx['wishlist'] = Wishlist.objects.filter(session_key=get_session(request)).select_related('product')
    return render(request, 'store/account.html', ctx)

# ===== API ENDPOINTS =====

@require_POST
def add_to_cart(request):
    data = json.loads(request.body)
    sk = get_session(request)
    product = get_object_or_404(Product, id=data['product_id'])
    item, created = CartItem.objects.get_or_create(
        session_key=sk, product=product,
        size=data.get('size', 'M'), color=data.get('color', '#000'),
        defaults={'quantity': data.get('quantity', 1)}
    )
    if not created:
        item.quantity += data.get('quantity', 1)
        item.save()
    return JsonResponse({'success': True, 'cart_count': cart_count(request)})

@require_POST
def update_cart(request):
    data = json.loads(request.body)
    sk = get_session(request)
    try:
        item = CartItem.objects.get(id=data['item_id'], session_key=sk)
        if data['action'] == 'increase':
            item.quantity += 1
            item.save()
        elif data['action'] == 'decrease':
            if item.quantity > 1:
                item.quantity -= 1
                item.save()
            else:
                item.delete()
        elif data['action'] == 'remove':
            item.delete()
    except CartItem.DoesNotExist:
        pass
    return JsonResponse({'success': True, 'cart_count': cart_count(request)})

@require_POST
def toggle_wishlist(request):
    data = json.loads(request.body)
    sk = get_session(request)
    product = get_object_or_404(Product, id=data['product_id'])
    wl, created = Wishlist.objects.get_or_create(session_key=sk, product=product)
    if not created:
        wl.delete()
    return JsonResponse({'success': True, 'added': created})

@require_POST
def place_order(request):
    data = json.loads(request.body)
    sk = get_session(request)
    items = CartItem.objects.filter(session_key=sk).select_related('product')
    if not items:
        return JsonResponse({'success': False, 'error': 'Cart is empty'})
    subtotal = sum(i.total for i in items)
    shipping = 0 if subtotal > 150 else 12
    order_num = 'AKV-' + ''.join(random.choices(string.digits, k=6))
    order = Order.objects.create(
        session_key=sk, order_number=order_num,
        first_name=data.get('first_name',''), last_name=data.get('last_name',''),
        email=data.get('email',''), phone=data.get('phone',''),
        address=data.get('address',''), city=data.get('city',''),
        state=data.get('state',''), zip_code=data.get('zip_code',''),
        country=data.get('country','India'), payment_method=data.get('payment_method','card'),
        subtotal=subtotal, shipping=shipping, total=subtotal+shipping
    )
    for item in items:
        OrderItem.objects.create(
            order=order, product=item.product, product_name=item.product.name,
            price=item.product.price, size=item.size, color=item.color, quantity=item.quantity
        )
    items.delete()
    return JsonResponse({'success': True, 'order_number': order_num})
