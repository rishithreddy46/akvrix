from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Product, CartItem, Wishlist, Order, OrderItem, Review


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'old_price', 'badge', 'in_stock', 'rating', 'reviews_count', 'created_at')
    list_filter = ('category', 'badge', 'in_stock')
    list_editable = ('price', 'old_price', 'badge', 'in_stock')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created_at',)
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'slug', 'category', 'badge', 'description')}),
        ('Pricing', {'fields': ('price', 'old_price', 'in_stock')}),
        ('Media', {'fields': ('image', 'image_hover')}),
        ('Variants', {'fields': ('sizes', 'colors')}),
        ('Stats', {'fields': ('rating', 'reviews_count'), 'classes': ('collapse',)}),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'size', 'color', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'first_name', 'last_name', 'email', 'total', 'status', 'payment_method', 'carrier', 'tracking_number', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    list_editable = ('status',)
    search_fields = ('order_number', 'first_name', 'last_name', 'email', 'tracking_number')
    inlines = [OrderItemInline]
    readonly_fields = ('order_number', 'session_key', 'subtotal', 'shipping', 'total', 'created_at')
    ordering = ('-created_at',)
    fieldsets = (
        ('Order Info', {'fields': ('order_number', 'user', 'session_key', 'status', 'payment_method')}),
        ('Customer', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Shipping Address', {'fields': ('address', 'city', 'state', 'zip_code', 'country')}),
        ('Tracking', {'fields': ('tracking_number', 'carrier', 'estimated_delivery', 'shipped_at', 'delivered_at')}),
        ('Financials', {'fields': ('subtotal', 'shipping', 'total'), 'classes': ('collapse',)}),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('name', 'text', 'product__name')
    ordering = ('-created_at',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'session_key', 'size', 'color', 'quantity')
    list_filter = ('size',)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'session_key')
