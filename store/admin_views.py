"""Custom AKVRIX Admin Dashboard — linked to Django backend auth."""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from .models import Product, CartItem, Wishlist, Order, OrderItem, Review
import json


def admin_required(view_func):
    """Check user is authenticated AND is staff/superuser."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_login(request):
    ctx = {'error': ''}
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        ctx['error'] = 'Invalid credentials or insufficient permissions.'
    return render(request, 'store/admin/login.html', ctx)


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


@admin_required
def admin_dashboard(request):
    ctx = {
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
        'total_revenue': Order.objects.aggregate(t=Sum('total'))['t'] or 0,
        'total_reviews': Review.objects.count(),
        'total_customers': User.objects.filter(is_staff=False).count(),
        'recent_orders': Order.objects.order_by('-created_at')[:5],
        'low_stock': Product.objects.filter(in_stock=False),
        'top_products': Product.objects.order_by('-rating')[:5],
    }
    return render(request, 'store/admin/dashboard.html', ctx)


@admin_required
def admin_products(request):
    products = Product.objects.all().order_by('-created_at')
    cat = request.GET.get('cat')
    if cat:
        products = products.filter(category=cat)
    ctx = {
        'products': products,
        'categories': Product.CATEGORY_CHOICES,
        'current_cat': cat or '',
    }
    return render(request, 'store/admin/products.html', ctx)


@admin_required
def admin_product_edit(request, product_id=None):
    product = get_object_or_404(Product, id=product_id) if product_id else None
    if request.method == 'POST':
        data = request.POST
        fields = {
            'name': data.get('name', ''),
            'slug': data.get('slug', ''),
            'price': data.get('price', 0),
            'old_price': data.get('old_price') or None,
            'category': data.get('category', ''),
            'description': data.get('description', ''),
            'image': data.get('image', ''),
            'image_hover': data.get('image_hover', ''),
            'sizes': data.get('sizes', 'S,M,L,XL'),
            'colors': data.get('colors', '#000,#FFF'),
            'rating': data.get('rating', 4.5),
            'reviews_count': data.get('reviews_count', 0),
            'badge': data.get('badge', ''),
            'in_stock': data.get('in_stock') == 'on',
        }
        if product:
            for k, v in fields.items():
                setattr(product, k, v)
            product.save()
        else:
            product = Product.objects.create(**fields)
        return redirect('admin_products')
    ctx = {
        'product': product,
        'categories': Product.CATEGORY_CHOICES,
        'editing': product is not None,
    }
    return render(request, 'store/admin/product_form.html', ctx)


@admin_required
def admin_product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        return redirect('admin_products')
    return render(request, 'store/admin/product_delete.html', {'product': product})


@admin_required
def admin_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    ctx = {
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
        'current_status': status or '',
    }
    return render(request, 'store/admin/orders.html', ctx)


@admin_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        tracking_number = request.POST.get('tracking_number', '')
        carrier = request.POST.get('carrier', '')
        estimated_delivery = request.POST.get('estimated_delivery', '')
        if new_status:
            order.status = new_status
        if tracking_number:
            order.tracking_number = tracking_number
        if carrier:
            order.carrier = carrier
        if estimated_delivery:
            order.estimated_delivery = estimated_delivery
        order.save()
        return redirect('admin_order_detail', order_id=order.id)
    ctx = {
        'order': order,
        'items': order.items.all().select_related('product'),
        'status_choices': Order.STATUS_CHOICES,
        'tracking_steps': order.get_tracking_steps(),
    }
    return render(request, 'store/admin/order_detail.html', ctx)


@admin_required
def admin_reviews(request):
    reviews = Review.objects.all().order_by('-created_at').select_related('product')
    ctx = {'reviews': reviews}
    return render(request, 'store/admin/reviews.html', ctx)


@admin_required
@require_POST
def admin_review_delete(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.delete()
    return redirect('admin_reviews')


@admin_required
def admin_customers(request):
    customers = User.objects.filter(is_staff=False).order_by('-date_joined')
    customer_data = []
    for c in customers:
        orders = Order.objects.filter(user=c)
        total_spent = orders.aggregate(t=Sum('total'))['t'] or 0
        customer_data.append({
            'user': c,
            'order_count': orders.count(),
            'total_spent': total_spent,
        })
    ctx = {'customers': customer_data}
    return render(request, 'store/admin/customers.html', ctx)
