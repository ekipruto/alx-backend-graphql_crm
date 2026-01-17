from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class Customer(models.Model):
    """
    Customer model - stores customer information
    """
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)  # Unique email
    
    # Phone validator: +1234567890 or 123-456-7890
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$|^\d{3}-\d{3}-\d{4}$',
        message="Phone number must be in format: '+999999999' or '123-456-7890'"
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    
    def __str__(self):
        return f"{self.name} ({self.email})"


class Product(models.Model):
    """
    Product model - stores product information
    """
    name = models.CharField(max_length=255)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price must be positive"
    )
    stock = models.IntegerField(
        default=0,
        help_text="Stock cannot be negative"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
    
    def __str__(self):
        return f"{self.name} - ${self.price}"


class Order(models.Model):
    """
    Order model - stores order information
    Links customers to products
    """
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    products = models.ManyToManyField(
        Product,
        related_name='orders'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    order_date = models.DateTimeField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-order_date']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
    
    def __str__(self):
        return f"Order #{self.id} - {self.customer.name}"
    
    def calculate_total(self):
        """Calculate total amount from associated products"""
        total = sum(product.price for product in self.products.all())
        self.total_amount = total
        self.save()
        return total
