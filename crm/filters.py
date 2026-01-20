import django_filters
from .models import Customer, Product, Order


class CustomerFilter(django_filters.FilterSet):
    """
    Filter for Customer model
    Allows searching by name, email, phone, and creation date
    """
    
    # Name filter - case insensitive partial match
    # Example: name_icontains="Ali" matches "Alice", "Alicia", etc.
    name_icontains = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='Name contains (case-insensitive)'
    )
    
    # Email filter - case insensitive partial match
    email_icontains = django_filters.CharFilter(
        field_name='email',
        lookup_expr='icontains',
        label='Email contains'
    )
    
    # Creation date range filters
    # Example: created_at_gte="2025-01-01" means "created on or after Jan 1, 2025"
    created_at_gte = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created after (inclusive)'
    )
    
    created_at_lte = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created before (inclusive)'
    )
    
    # Custom filter: Phone starts with pattern
    # Example: phone_startswith="+1" matches US numbers
    phone_startswith = django_filters.CharFilter(
        field_name='phone',
        lookup_expr='startswith',
        label='Phone starts with'
    )
    
    class Meta:
        model = Customer
        fields = {
            'name': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
            'phone': ['exact', 'startswith'],
        }


class ProductFilter(django_filters.FilterSet):
    """
    Filter for Product model
    Allows searching by name, price range, and stock levels
    """
    
    # Name filter - case insensitive partial match
    name_icontains = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='Name contains'
    )
    
    # Price range filters
    # gte = greater than or equal
    # lte = less than or equal
    price_gte = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        label='Price greater than or equal'
    )
    
    price_lte = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        label='Price less than or equal'
    )
    
    # Stock filters
    stock_gte = django_filters.NumberFilter(
        field_name='stock',
        lookup_expr='gte',
        label='Stock greater than or equal'
    )
    
    stock_lte = django_filters.NumberFilter(
        field_name='stock',
        lookup_expr='lte',
        label='Stock less than or equal'
    )
    
    # Low stock filter (stock < 10)
    low_stock = django_filters.BooleanFilter(
        method='filter_low_stock',
        label='Low stock (less than 10)'
    )
    
    def filter_low_stock(self, queryset, name, value):
        """Custom method to filter products with stock < 10"""
        if value:
            return queryset.filter(stock__lt=10)
        return queryset
    
    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains'],
            'price': ['exact', 'gte', 'lte'],
            'stock': ['exact', 'gte', 'lte'],
        }


class OrderFilter(django_filters.FilterSet):
    """
    Filter for Order model
    Allows searching by amount, date, customer name, and product name
    """
    
    # Total amount range filters
    total_amount_gte = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='gte',
        label='Total amount greater than or equal'
    )
    
    total_amount_lte = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='lte',
        label='Total amount less than or equal'
    )
    
    # Order date range filters
    order_date_gte = django_filters.DateTimeFilter(
        field_name='order_date',
        lookup_expr='gte',
        label='Order date after (inclusive)'
    )
    
    order_date_lte = django_filters.DateTimeFilter(
        field_name='order_date',
        lookup_expr='lte',
        label='Order date before (inclusive)'
    )
    
    # Filter by customer name (related field)
    # The __ notation means "look in the related customer model"
    customer_name = django_filters.CharFilter(
        field_name='customer__name',
        lookup_expr='icontains',
        label='Customer name contains'
    )
    
    # Filter by product name (related field, many-to-many)
    product_name = django_filters.CharFilter(
        field_name='products__name',
        lookup_expr='icontains',
        label='Product name contains'
    )
    
    # Filter by specific product ID
    product_id = django_filters.NumberFilter(
        field_name='products__id',
        lookup_expr='exact',
        label='Product ID'
    )
    
    class Meta:
        model = Order
        fields = {
            'total_amount': ['exact', 'gte', 'lte'],
            'order_date': ['exact', 'gte', 'lte'],
        }
