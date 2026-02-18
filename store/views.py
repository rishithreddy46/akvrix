from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.db import models
from .models import Product, CartItem, Wishlist, Order, OrderItem, Review, Address
import json, random, string


def get_session(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def is_logged_in(request):
    return request.user.is_authenticated


def login_required_view(view_func):
    def wrapper(request, *args, **kwargs):
        if not is_logged_in(request):
            return redirect('/login/?next=' + request.path)
        return view_func(request, *args, **kwargs)
    return wrapper


def cart_count(request):
    if request.user.is_authenticated:
        return CartItem.objects.filter(user=request.user).aggregate(total=models.Sum('quantity'))['total'] or 0
    sk = get_session(request)
    return CartItem.objects.filter(session_key=sk, user__isnull=True).aggregate(total=models.Sum('quantity'))['total'] or 0


def base_context(request):
    user_name = ''
    user_email = ''
    if request.user.is_authenticated:
        user_name = request.user.get_full_name() or request.user.username
        user_email = request.user.email
    return {
        'cart_count': cart_count(request),
        'is_logged_in': request.user.is_authenticated,
        'user_name': user_name,
        'user_email': user_email,
    }


# ===== PUBLIC PAGES =====

def home(request):
    # Logged-in users go directly to shop
    if request.user.is_authenticated:
        return redirect('shop')
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
    if request.user.is_authenticated:
        ctx['wishlist_ids'] = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))
    else:
        ctx['wishlist_ids'] = list(Wishlist.objects.filter(session_key=get_session(request)).values_list('product_id', flat=True))
    return render(request, 'store/shop.html', ctx)


def product_detail(request, slug):
    ctx = base_context(request)
    p = get_object_or_404(Product, slug=slug)
    ctx['product'] = p
    ctx['related'] = Product.objects.filter(category=p.category).exclude(id=p.id)[:4]
    ctx['reviews'] = p.reviews.all().order_by('-created_at')
    if request.user.is_authenticated:
        ctx['in_wishlist'] = Wishlist.objects.filter(user=request.user, product=p).exists()
        ctx['has_reviewed'] = Review.objects.filter(user=request.user, product=p).exists()
    else:
        ctx['in_wishlist'] = Wishlist.objects.filter(session_key=get_session(request), product=p).exists()
        ctx['has_reviewed'] = False
    return render(request, 'store/product_detail.html', ctx)


# ===== AUTH PAGES =====

def login_page(request):
    ctx = base_context(request)
    if request.user.is_authenticated:
        return redirect('shop')
    if request.method == 'POST':
        identifier = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = None
        # Try by email first
        try:
            user_obj = User.objects.get(email=identifier)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            pass
        # Try by username if email didn't work
        if user is None:
            user = authenticate(request, username=identifier, password=password)
        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            # Migrate session cart/wishlist to user
            sk = get_session(request)
            CartItem.objects.filter(session_key=sk, user__isnull=True).update(user=user)
            Wishlist.objects.filter(session_key=sk, user__isnull=True).update(user=user)
            next_url = request.GET.get('next', '/shop/')
            return redirect(next_url)
        ctx['error'] = 'Invalid email/username or password. Please try again.'
    return render(request, 'store/login.html', ctx)


def register_page(request):
    ctx = base_context(request)
    if request.user.is_authenticated:
        return redirect('shop')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        if not all([name, email, password]):
            ctx['error'] = 'All fields are required.'
        elif password != confirm:
            ctx['error'] = 'Passwords do not match.'
        elif User.objects.filter(email=email).exists():
            ctx['error'] = 'An account with this email already exists.'
        else:
            # Create Django user
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            name_parts = name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name
            )
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            sk = get_session(request)
            CartItem.objects.filter(session_key=sk, user__isnull=True).update(user=user)
            Wishlist.objects.filter(session_key=sk, user__isnull=True).update(user=user)
            next_url = request.GET.get('next', '/shop/')
            return redirect(next_url)
    return render(request, 'store/register.html', ctx)


def forgot_password_page(request):
    ctx = base_context(request)
    ctx['sent'] = False
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            ctx['sent'] = True
            ctx['reset_email'] = email
    return render(request, 'store/forgot_password.html', ctx)


def logout_view(request):
    logout(request)
    return redirect('home')


# ===== PROTECTED PAGES =====

@login_required_view
def cart_page(request):
    ctx = base_context(request)
    items = CartItem.objects.filter(user=request.user).select_related('product')
    subtotal = sum(i.total for i in items)
    shipping = 0 if subtotal > 150 else 12
    ctx['items'] = items
    ctx['subtotal'] = subtotal
    ctx['shipping'] = shipping
    ctx['total'] = subtotal + shipping
    return render(request, 'store/cart.html', ctx)


@login_required_view
def checkout_page(request):
    ctx = base_context(request)
    items = CartItem.objects.filter(user=request.user).select_related('product')
    subtotal = sum(i.total for i in items)
    shipping = 0 if subtotal > 150 else 12
    ctx['items'] = items
    ctx['subtotal'] = subtotal
    ctx['shipping'] = shipping
    ctx['total'] = subtotal + shipping
    ctx['addresses'] = Address.objects.filter(user=request.user)
    return render(request, 'store/checkout.html', ctx)


@login_required_view
def wishlist_page(request):
    ctx = base_context(request)
    ctx['wishlist_items'] = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'store/wishlist.html', ctx)


@login_required_view
def account_page(request):
    ctx = base_context(request)
    ctx['user'] = request.user
    ctx['orders'] = Order.objects.filter(user=request.user).order_by('-created_at')
    ctx['wishlist'] = Wishlist.objects.filter(user=request.user).select_related('product')
    ctx['addresses'] = Address.objects.filter(user=request.user)
    return render(request, 'store/account.html', ctx)


@login_required_view
def my_orders_page(request):
    ctx = base_context(request)
    ctx['orders'] = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/my_orders.html', ctx)


@login_required_view
def order_detail_page(request, order_number):
    ctx = base_context(request)
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    ctx['order'] = order
    ctx['items'] = order.items.all().select_related('product')
    ctx['tracking_steps'] = order.get_tracking_steps()
    return render(request, 'store/order_detail.html', ctx)


# ===== PROFILE & PASSWORD APIS =====

@login_required_view
@require_POST
def update_profile(request):
    data = json.loads(request.body)
    user = request.user
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    if email and email != user.email:
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            return JsonResponse({'success': False, 'error': 'Email already in use.'})
        user.email = email
    user.save()
    return JsonResponse({
        'success': True,
        'user_name': user.get_full_name() or user.username,
        'email': user.email,
    })


@login_required_view
@require_POST
def change_password(request):
    data = json.loads(request.body)
    current = data.get('current_password', '')
    new_pass = data.get('new_password', '')
    confirm = data.get('confirm_password', '')
    user = request.user
    if not user.check_password(current):
        return JsonResponse({'success': False, 'error': 'Current password is incorrect.'})
    if len(new_pass) < 6:
        return JsonResponse({'success': False, 'error': 'New password must be at least 6 characters.'})
    if new_pass != confirm:
        return JsonResponse({'success': False, 'error': 'New passwords do not match.'})
    user.set_password(new_pass)
    user.save()
    update_session_auth_hash(request, user)
    return JsonResponse({'success': True})


# ===== API ENDPOINTS =====

@require_POST
def add_to_cart(request):
    data = json.loads(request.body)
    sk = get_session(request)
    product = get_object_or_404(Product, id=data['product_id'])
    user = request.user if request.user.is_authenticated else None
    if user:
        item, created = CartItem.objects.get_or_create(
            user=user, product=product,
            size=data.get('size', 'M'), color=data.get('color', '#000'),
            defaults={'quantity': data.get('quantity', 1), 'session_key': sk}
        )
    else:
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
    try:
        if request.user.is_authenticated:
            item = CartItem.objects.get(id=data['item_id'], user=request.user)
        else:
            item = CartItem.objects.get(id=data['item_id'], session_key=get_session(request))
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
    product = get_object_or_404(Product, id=data['product_id'])
    if request.user.is_authenticated:
        wl, created = Wishlist.objects.get_or_create(
            user=request.user, product=product,
            defaults={'session_key': get_session(request)}
        )
    else:
        sk = get_session(request)
        wl, created = Wishlist.objects.get_or_create(
            session_key=sk, product=product,
        )
    if not created:
        wl.delete()
    return JsonResponse({'success': True, 'added': created})


@require_POST
def place_order(request):
    data = json.loads(request.body)
    sk = get_session(request)
    if request.user.is_authenticated:
        items = CartItem.objects.filter(user=request.user).select_related('product')
    else:
        items = CartItem.objects.filter(session_key=sk, user__isnull=True).select_related('product')
    if not items:
        return JsonResponse({'success': False, 'error': 'Cart is empty'})
    subtotal = sum(i.total for i in items)
    shipping = 0 if subtotal > 150 else 12
    order_num = 'AKV-' + ''.join(random.choices(string.digits, k=6))
    order = Order.objects.create(
        session_key=sk,
        user=request.user if request.user.is_authenticated else None,
        order_number=order_num,
        first_name=data.get('first_name', ''), last_name=data.get('last_name', ''),
        email=data.get('email', ''), phone=data.get('phone', ''),
        address=data.get('address', ''), city=data.get('city', ''),
        state=data.get('state', ''), zip_code=data.get('zip_code', ''),
        country=data.get('country', 'India'), payment_method=data.get('payment_method', 'card'),
        subtotal=subtotal, shipping=shipping, total=subtotal + shipping
    )
    for item in items:
        OrderItem.objects.create(
            order=order, product=item.product, product_name=item.product.name,
            price=item.product.price, size=item.size, color=item.color, quantity=item.quantity
        )
    items.delete()
    return JsonResponse({'success': True, 'order_number': order_num})


# ===== REVIEWS =====

@login_required_view
@require_POST
def submit_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    # One review per user per product
    if Review.objects.filter(user=request.user, product=product).exists():
        return JsonResponse({'success': False, 'error': 'You have already reviewed this product.'}, status=400)
    try:
        data = json.loads(request.body)
        rating = int(data.get('rating', 0))
        text = data.get('text', '').strip()
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)

    if not (1 <= rating <= 5):
        return JsonResponse({'success': False, 'error': 'Rating must be 1-5'}, status=400)
    if not text:
        return JsonResponse({'success': False, 'error': 'Review text is required'}, status=400)

    name = request.user.get_full_name() or request.user.username
    Review.objects.create(
        product=product,
        user=request.user,
        name=name,
        rating=rating,
        text=text,
    )
    return JsonResponse({'success': True})


# ===== ADDRESSES =====

@login_required_view
def address_list(request):
    addrs = Address.objects.filter(user=request.user)
    data = [{
        'id': a.id, 'label': a.label, 'full_name': a.full_name,
        'phone': a.phone, 'address_line': a.address_line,
        'city': a.city, 'state': a.state, 'pincode': a.pincode,
        'is_default': a.is_default,
    } for a in addrs]
    return JsonResponse({'success': True, 'addresses': data})


@login_required_view
@require_POST
def address_save(request):
    data = json.loads(request.body)
    addr_id = data.get('id')
    if addr_id:
        addr = get_object_or_404(Address, id=addr_id, user=request.user)
    else:
        addr = Address(user=request.user)
    addr.label = data.get('label', 'home')
    addr.full_name = data.get('full_name', '').strip()
    addr.phone = data.get('phone', '').strip()
    addr.address_line = data.get('address_line', '').strip()
    addr.city = data.get('city', '').strip()
    addr.state = data.get('state', '').strip()
    addr.pincode = data.get('pincode', '').strip()
    if not all([addr.full_name, addr.phone, addr.address_line, addr.city, addr.state, addr.pincode]):
        return JsonResponse({'success': False, 'error': 'All fields are required.'})
    is_default = data.get('is_default', False)
    if is_default:
        Address.objects.filter(user=request.user).update(is_default=False)
        addr.is_default = True
    elif not Address.objects.filter(user=request.user).exclude(id=addr.id if addr.id else 0).exists():
        addr.is_default = True
    addr.save()
    return JsonResponse({'success': True, 'id': addr.id})


@login_required_view
@require_POST
def address_delete(request, address_id):
    addr = get_object_or_404(Address, id=address_id, user=request.user)
    was_default = addr.is_default
    addr.delete()
    if was_default:
        first = Address.objects.filter(user=request.user).first()
        if first:
            first.is_default = True
            first.save()
    return JsonResponse({'success': True})


@login_required_view
@require_POST
def address_set_default(request, address_id):
    addr = get_object_or_404(Address, id=address_id, user=request.user)
    Address.objects.filter(user=request.user).update(is_default=False)
    addr.is_default = True
    addr.save()
    return JsonResponse({'success': True})

