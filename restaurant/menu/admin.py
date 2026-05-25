from django.contrib import admin
from .models import Dish_Categories, Dishes, Ingredients, Recipes, Customers, Orders

# Register your models here.
admin.site.site_header = 'Панель управления Рестораном'
admin.site.site_title = 'Ресторан'
admin.site.index_title = 'Добро пожаловать в панель управления'

admin.site.register(Dish_Categories)
admin.site.register(Dishes)
admin.site.register(Ingredients)
admin.site.register(Recipes)
admin.site.register(Customers)
admin.site.register(Orders)