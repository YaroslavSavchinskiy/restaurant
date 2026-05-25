from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class Dish_Categories(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=100, null=False)
    category_description = models.TextField(null=True)
    display_order = models.IntegerField(null=False)
    is_active = models.BooleanField(null=False, default=True)

    class Meta:
        db_table = 'dish_categories'

class Dishes(models.Model):
    dish_id = models.AutoField(primary_key=True)
    dish_name = models.CharField(max_length=200, null=False)
    description = models.TextField(null=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    category_id = models.ForeignKey('Dish_Categories', on_delete=models.PROTECT, null=False, to_field='category_id')
    display_order = models.IntegerField(null=False)
    is_available = models.BooleanField(null=False, default=True)
    cooking_time_min = models.IntegerField(null=False)
    calories = models.IntegerField(null=False)
    allergens = models.CharField(max_length=255)

    class Meta:
        db_table = 'dishes'

class Ingredients(models.Model):
    ingredient_id = models.AutoField(primary_key=True)
    ingredient_name = models.CharField(max_length=150, null=False)
    unit_of_measure = models.CharField(max_length=20, null=False)
    current_stock = models.DecimalField(max_digits=10, decimal_places=3, null=False)
    min_stock_threshold = models.DecimalField(max_digits=10, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=False)

    class Meta:
        db_table = 'ingredients'

class Recipes(models.Model):
    recipe_id = models.AutoField(primary_key=True)
    dish_id = models.ForeignKey('Dishes', on_delete=models.PROTECT, null=False, to_field='dish_id')
    ingredient_id = models.ForeignKey('Ingredients', on_delete=models.PROTECT, null=False, to_field='ingredient_id')
    quantity_required = models.DecimalField(max_digits=7, decimal_places=3, null=False)

    class Meta:
        db_table = 'recipes'

class Customers(models.Model):
    customer_id = models.AutoField(primary_key=True)
    surname = models.CharField(max_length=100, null=False)
    name = models.CharField(max_length=100, null=False)
    phone_number = models.CharField(max_length=20, unique=True, null=False)
    email = models.CharField(max_length=255, unique=True)
    preferences = models.TextField()

    class Meta:
        db_table = 'customers'

class Orders(models.Model):
    order_id = models.AutoField(primary_key=True)
    customer_id = models.ForeignKey('Customers', on_delete=models.PROTECT, null=False, to_field='customer_id')
    order_type = models.CharField(max_length=50, null=False)
    delivery_address = models.TextField(null=False)
    customer_phone = models.CharField(max_length=20, null=False)
    status = models.CharField(max_length=50, null=False)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    notes = models.TextField()
    created_at = models.DateTimeField(null=False)

    class Meta:
        db_table = 'orders'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True)
    customer = models.OneToOneField('Customers', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f'Профиль {self.user.username}'

    class Meta:
        db_table = 'user_profiles'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

# Добавьте в конец файла menu/models.py

class Cart(models.Model):
    """Корзина пользователя"""
    cart_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)  # Активная корзина или уже оформленная
    
    class Meta:
        db_table = 'carts'
    
    def __str__(self):
        return f'Корзина {self.user.username} от {self.created_at}'
    
    def get_total_price(self):
        """Получить общую сумму корзины"""
        items = self.cart_items.all()
        total = sum(item.get_total_price() for item in items)
        return total
    
    def get_total_items(self):
        """Получить общее количество товаров"""
        items = self.cart_items.all()
        return sum(item.quantity for item in items)

class CartItem(models.Model):
    """Товар в корзине"""
    cart_item_id = models.AutoField(primary_key=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    dish = models.ForeignKey(Dishes, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2)  # Цена на момент добавления
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cart_items'
        unique_together = ['cart', 'dish']  # Чтобы не было дублей одного блюда
    
    def __str__(self):
        return f'{self.dish.dish_name} x{self.quantity}'
    
    def get_total_price(self):
        return self.price_at_time * self.quantity