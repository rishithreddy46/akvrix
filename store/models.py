from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('streetwear', 'Streetwear'),
        ('essentials', 'Essentials'),
        ('outerwear', 'Outerwear'),
        ('new', 'New Arrivals'),
        ('limited', 'Limited Edition'),
    ]
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    image = models.URLField()
    image_hover = models.URLField(blank=True)
    sizes = models.CharField(max_length=100, default='S,M,L,XL')
    colors = models.CharField(max_length=200, default='#000,#FFF')
    rating = models.FloatField(default=4.5)
    reviews_count = models.IntegerField(default=0)
    badge = models.CharField(max_length=50, blank=True)
    in_stock = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_sizes_list(self):
        return [s.strip() for s in self.sizes.split(',')]

    def get_colors_list(self):
        return [c.strip() for c in self.colors.split(',')]

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int(((self.old_price - self.price) / self.old_price) * 100)
        return 0


class CartItem(models.Model):
    session_key = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=20)
    quantity = models.IntegerField(default=1)

    class Meta:
        unique_together = ('session_key', 'product', 'size', 'color')

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    @property
    def total(self):
        return self.product.price * self.quantity


class Wishlist(models.Model):
    session_key = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('session_key', 'product')


class Order(models.Model):
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    session_key = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='India')
    payment_method = models.CharField(max_length=50)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    # Tracking fields
    tracking_number = models.CharField(max_length=100, blank=True)
    carrier = models.CharField(max_length=100, blank=True, help_text='e.g. Delhivery, BlueDart, DTDC')
    estimated_delivery = models.DateField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    order_number = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"Order #{self.order_number}"

    def get_tracking_steps(self):
        """Returns list of tracking steps with their completed status."""
        status_order = ['processing', 'confirmed', 'shipped', 'out_for_delivery', 'delivered']
        steps = [
            {'key': 'processing', 'label': 'Order Placed', 'icon': 'ri-checkbox-circle-line'},
            {'key': 'confirmed', 'label': 'Confirmed', 'icon': 'ri-check-double-line'},
            {'key': 'shipped', 'label': 'Shipped', 'icon': 'ri-truck-line'},
            {'key': 'out_for_delivery', 'label': 'Out for Delivery', 'icon': 'ri-e-bike-line'},
            {'key': 'delivered', 'label': 'Delivered', 'icon': 'ri-home-smile-line'},
        ]
        if self.status == 'cancelled':
            for s in steps:
                s['completed'] = False
                s['active'] = False
            return steps
        current_idx = status_order.index(self.status) if self.status in status_order else 0
        for i, s in enumerate(steps):
            s['completed'] = i <= current_idx
            s['active'] = i == current_idx
        return steps


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=20)
    quantity = models.IntegerField()


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    rating = models.IntegerField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.product.name}"
