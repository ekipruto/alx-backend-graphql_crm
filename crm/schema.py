import graphene
from graphene_django import DjangoObjectType
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Customer, Product, Order


# ==========================================
# GraphQL Types (represent database models)
# ==========================================

class CustomerType(DjangoObjectType):
    """GraphQL type for Customer model"""
    class Meta:
        model = Customer
        fields = ('id', 'name', 'email', 'phone', 'created_at', 'orders')


class ProductType(DjangoObjectType):
    """GraphQL type for Product model"""
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'stock', 'created_at')


class OrderType(DjangoObjectType):
    """GraphQL type for Order model"""
    class Meta:
        model = Order
        fields = ('id', 'customer', 'products', 'total_amount', 'order_date', 'created_at')


# ==========================================
# Input Types (for mutations)
# ==========================================

class CustomerInput(graphene.InputObjectType):
    """Input type for creating a customer"""
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class ProductInput(graphene.InputObjectType):
    """Input type for creating a product"""
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(required=False, default_value=0)


class OrderInput(graphene.InputObjectType):
    """Input type for creating an order"""
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime(required=False)


# ==========================================
# Mutations
# ==========================================

class CreateCustomer(graphene.Mutation):
    """
    Mutation to create a single customer
    """
    class Arguments:
        input = CustomerInput(required=True)
    
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    
    @staticmethod
    def mutate(root, info, input):
        try:
            # Check if email already exists
            if Customer.objects.filter(email=input.email).exists():
                raise ValidationError("Email already exists")
            
            # Create customer
            customer = Customer(
                name=input.name,
                email=input.email,
                phone=input.get('phone')
            )
            
            # This will trigger model validation (including phone format)
            customer.full_clean()
            customer.save()
            
            return CreateCustomer(
                customer=customer,
                message="Customer created successfully"
            )
        
        except ValidationError as e:
            raise Exception(str(e))


class BulkCreateCustomers(graphene.Mutation):
    """
    Mutation to create multiple customers at once
    Supports partial success - creates valid entries even if some fail
    """
    class Arguments:
        input = graphene.List(CustomerInput, required=True)
    
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    
    @staticmethod
    def mutate(root, info, input):
        customers_created = []
        errors = []
        
        for idx, customer_data in enumerate(input):
            try:
                # Check if email exists
                if Customer.objects.filter(email=customer_data.email).exists():
                    errors.append(f"Row {idx + 1}: Email {customer_data.email} already exists")
                    continue
                
                # Create customer
                customer = Customer(
                    name=customer_data.name,
                    email=customer_data.email,
                    phone=customer_data.get('phone')
                )
                
                # Validate
                customer.full_clean()
                customer.save()
                
                customers_created.append(customer)
            
            except ValidationError as e:
                errors.append(f"Row {idx + 1}: {str(e)}")
            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")
        
        return BulkCreateCustomers(
            customers=customers_created,
            errors=errors if errors else None
        )


class CreateProduct(graphene.Mutation):
    """
    Mutation to create a product
    """
    class Arguments:
        input = ProductInput(required=True)
    
    product = graphene.Field(ProductType)
    message = graphene.String()
    
    @staticmethod
    def mutate(root, info, input):
        try:
            # Validate price is positive
            if input.price <= 0:
                raise ValidationError("Price must be positive")
            
            # Validate stock is not negative
            stock = input.get('stock', 0)
            if stock < 0:
                raise ValidationError("Stock cannot be negative")
            
            # Create product
            product = Product(
                name=input.name,
                price=input.price,
                stock=stock
            )
            
            product.full_clean()
            product.save()
            
            return CreateProduct(
                product=product,
                message="Product created successfully"
            )
        
        except ValidationError as e:
            raise Exception(str(e))


class CreateOrder(graphene.Mutation):
    """
    Mutation to create an order with products
    """
    class Arguments:
        input = OrderInput(required=True)
    
    order = graphene.Field(OrderType)
    message = graphene.String()
    
    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(pk=input.customer_id)
            except Customer.DoesNotExist:
                raise ValidationError(f"Customer with ID {input.customer_id} does not exist")
            
            # Validate at least one product
            if not input.product_ids or len(input.product_ids) == 0:
                raise ValidationError("At least one product must be selected")
            
            # Validate all products exist
            products = []
            for product_id in input.product_ids:
                try:
                    product = Product.objects.get(pk=product_id)
                    products.append(product)
                except Product.DoesNotExist:
                    raise ValidationError(f"Product with ID {product_id} does not exist")
            
            # Create order
            order = Order(
                customer=customer,
                order_date=input.get('order_date')
            )
            order.save()
            
            # Add products
            order.products.set(products)
            
            # Calculate total amount
            order.calculate_total()
            
            return CreateOrder(
                order=order,
                message="Order created successfully"
            )
        
        except ValidationError as e:
            raise Exception(str(e))


# ==========================================
# Queries
# ==========================================

class Query(graphene.ObjectType):
    """
    CRM-specific queries
    """
    # List all customers
    all_customers = graphene.List(CustomerType)
    
    # Get single customer by ID
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    
    # List all products
    all_products = graphene.List(ProductType)
    
    # Get single product by ID
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    
    # List all orders
    all_orders = graphene.List(OrderType)
    
    # Get single order by ID
    order = graphene.Field(OrderType, id=graphene.ID(required=True))
    
    # Resolvers
    def resolve_all_customers(self, info):
        return Customer.objects.all()
    
    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(pk=id)
        except Customer.DoesNotExist:
            return None
    
    def resolve_all_products(self, info):
        return Product.objects.all()
    
    def resolve_product(self, info, id):
        try:
            return Product.objects.get(pk=id)
        except Product.DoesNotExist:
            return None
    
    def resolve_all_orders(self, info):
        return Order.objects.all()
    
    def resolve_order(self, info, id):
        try:
            return Order.objects.get(pk=id)
        except Order.DoesNotExist:
            return None


# ==========================================
# Combine Mutations
# ==========================================

class Mutation(graphene.ObjectType):
    """All CRM mutations"""
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
