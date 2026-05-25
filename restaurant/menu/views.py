from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import RegisterForm, LoginForm
from .models import Customers, UserProfile
from .models import Dishes, Dish_Categories, Cart, CartItem
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
from .forms import RegisterForm, LoginForm


# Create your views here.

# Регистрация
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Создаем пользователя
            user = form.save()
            
            # Создаем запись в таблице Customers
            customer = Customers.objects.create(
                surname='',
                name=user.username,
                phone_number=form.cleaned_data.get('phone_number'),
                email=form.cleaned_data.get('email'),
                preferences=''
            )
            
            # Связываем профиль с созданным customer
            user.profile.phone_number = form.cleaned_data.get('phone_number')
            user.profile.customer = customer
            user.profile.save()
            
            # Автоматически входим после регистрации
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать!')
            return redirect('home')
        else:
            # Если есть ошибки в форме
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    else:
        form = RegisterForm()
    
    return render(request, 'menu/register.html', {'form': form, 'title': 'Регистрация'})

# Вход
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'С возвращением, {username}!')
                return redirect('home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    else:
        form = LoginForm()
    
    return render(request, 'menu/login.html', {'form': form, 'title': 'Вход'})

# Выход
def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы. Ждем вас снова!')
    return redirect('home')

def get_or_create_cart(user):
    cart, created = Cart.objects.get_or_create(
        user=user,
        is_active=True,
        defaults={'is_active': True}
    )
    return cart

# Добавление в корзину через POST
@login_required
def add_to_cart(request):
    if request.method == 'POST':
        dish_id = request.POST.get('dish_id')
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            dish = Dishes.objects.get(dish_id=dish_id)
            cart = get_or_create_cart(request.user)
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                dish=dish,
                defaults={
                    'quantity': quantity,
                    'price_at_time': dish.price
                }
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            messages.success(request, f'{dish.dish_name} добавлен в корзину')
        except Dishes.DoesNotExist:
            messages.error(request, 'Блюдо не найдено')
        
        # Возвращаемся на предыдущую страницу
        return redirect(request.META.get('HTTP_REFERER', 'home'))

# Страница корзины
@login_required
def cart_view(request):
    cart = get_or_create_cart(request.user)
    cart_items = cart.cart_items.all().select_related('dish')
    
    context = {
        'title': 'Корзина',
        'cart': cart,
        'cart_items': cart_items,
        'total_price': cart.get_total_price(),
        'total_items': cart.get_total_items()
    }
    return render(request, 'menu/cart.html', context)

# Обновление количества
@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            cart_item = CartItem.objects.get(cart_item_id=item_id, cart__user=request.user)
            
            if quantity <= 0:
                cart_item.delete()
                messages.success(request, 'Товар удален из корзины')
            else:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, 'Количество обновлено')
                
        except CartItem.DoesNotExist:
            messages.error(request, 'Товар не найден')
        
        return redirect('cart')

# Удаление из корзины
@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        try:
            cart_item = CartItem.objects.get(cart_item_id=item_id, cart__user=request.user)
            dish_name = cart_item.dish.dish_name
            cart_item.delete()
            messages.success(request, f'{dish_name} удален из корзины')
        except CartItem.DoesNotExist:
            messages.error(request, 'Товар не найден')
        
        return redirect('cart')

# Очистка корзины
@login_required
def clear_cart(request):
    if request.method == 'POST':
        cart = get_or_create_cart(request.user)
        cart.cart_items.all().delete()
        messages.success(request, 'Корзина очищена')
        return redirect('cart')

def index(request):
    # Перемещаем запросы внутрь функции
    dish_one_best = get_object_or_404(Dishes, dish_name="Стейк Рибай (300г)")
    dish_two_best = get_object_or_404(Dishes, dish_name="Лосось Терияки")
    dish_three_best = get_object_or_404(Dishes, dish_name="Чизкейк Нью-Йорк")
    dish_four_best = get_object_or_404(Dishes, dish_name="Тирамису")
    
    data_index = {
        'title': 'Главная страница',
        'dish_one_best': dish_one_best,
        'dish_dish_name_one_best': dish_one_best.dish_name,
        'dish_price_one_best': dish_one_best.price,
        'dish_two_best': dish_two_best,
        'dish_dish_name_two_best': dish_two_best.dish_name,
        'dish_price_two_best': dish_two_best.price,
        'dish_three_best': dish_three_best,
        'dish_dish_name_three_best': dish_three_best.dish_name,
        'dish_price_three_best': dish_three_best.price,
        'dish_four_best': dish_four_best,
        'dish_dish_name_four_best': dish_four_best.dish_name,
        'dish_price_four_best': dish_four_best.price,

    }
    return render(request, 'menu/index.html', data_index)

def menu(request):
    # Перемещаем все запросы внутрь функции menu
    dish_categories_one = get_object_or_404(Dish_Categories, category_name="Основные блюда")
    dish_categories_two = get_object_or_404(Dish_Categories, category_name="Супы")
    dish_categories_three = get_object_or_404(Dish_Categories, category_name="Салаты")
    dish_categories_four = get_object_or_404(Dish_Categories, category_name="Закуски")
    dish_categories_five = get_object_or_404(Dish_Categories, category_name="Десерты")
    dish_categories_seven = get_object_or_404(Dish_Categories, category_name="Горячие напитки")
    dish_categories_eight = get_object_or_404(Dish_Categories, category_name="Холодные напитки")

    dish_one = get_object_or_404(Dishes, dish_name="Брускетта Классическая")
    dish_two = get_object_or_404(Dishes, dish_name="Салат Цезарь")
    dish_three = get_object_or_404(Dishes, dish_name="Стейк Рибай (300г)")
    dish_four = get_object_or_404(Dishes, dish_name="Лосось Терияки")
    dish_five = get_object_or_404(Dishes, dish_name="Крем-суп из грибов")
    dish_six = get_object_or_404(Dishes, dish_name="Пицца Маргарита")
    dish_seven = get_object_or_404(Dishes, dish_name="Тирамису")
    dish_eight = get_object_or_404(Dishes, dish_name="Капучино")
    dish_nine = get_object_or_404(Dishes, dish_name="Свежевыжатый апельсиновый сок")
    dish_ten = get_object_or_404(Dishes, dish_name="Бургер говяжий с картошкой")
    dish_eleven = get_object_or_404(Dishes, dish_name="Греческий салат")
    dish_twelve = get_object_or_404(Dishes, dish_name="Вегетарианские спринг-роллы (4 шт)")
    dish_thirteen = get_object_or_404(Dishes, dish_name="Шоколадный лава-кейк")
    dish_fourteen = get_object_or_404(Dishes, dish_name="Эспрессо")
    dish_fiveteen = get_object_or_404(Dishes, dish_name="Лимонад")
    dish_sixteen = get_object_or_404(Dishes, dish_name="Борщ")
    dish_seventeen = get_object_or_404(Dishes, dish_name="Куриная грудка на гриле")
    dish_eighteen = get_object_or_404(Dishes, dish_name="Чизкейк Нью-Йорк")
    dish_nineteen = get_object_or_404(Dishes, dish_name="Зеленый чай")
    dish_twenty = get_object_or_404(Dishes, dish_name="Айс Американо")
    
    data_menu = {
        'title': 'Меню',

        'dish_categories_one': dish_categories_one,
        'dish_categories_one_category_name': dish_categories_one.category_name,
        'dish_categories_one_category_description': dish_categories_one.category_description,
        'dish_categories_two': dish_categories_two,
        'dish_categories_two_category_name': dish_categories_two.category_name,
        'dish_categories_two_category_description': dish_categories_two.category_description,
        'dish_categories_three': dish_categories_three,
        'dish_categories_three_category_name': dish_categories_three.category_name,
        'dish_categories_three_category_description': dish_categories_three.category_description,
        'dish_categories_four': dish_categories_four,
        'dish_categories_four_category_name': dish_categories_four.category_name,
        'dish_categories_four_category_description': dish_categories_four.category_description,
        'dish_categories_five': dish_categories_five,
        'dish_categories_five_category_name': dish_categories_five.category_name,
        'dish_categories_five_category_description': dish_categories_five.category_description,
        'dish_categories_seven': dish_categories_seven,
        'dish_categories_seven_category_name': dish_categories_seven.category_name,
        'dish_categories_seven_category_description': dish_categories_seven.category_description,
        'dish_categories_eight': dish_categories_eight,
        'dish_categories_eight_category_name': dish_categories_eight.category_name,
        'dish_categories_eight_category_description': dish_categories_eight.category_description,

        'dish_one': dish_one,
        'dish_one_name': dish_one.dish_name,
        'dish_one_description': dish_one.description,
        'dish_one_price': dish_one.price,
        'dish_one_is_avaible': dish_one.is_available,
        'dish_one_cooking_time_min': dish_one.cooking_time_min,
        'dish_one_calories': dish_one.calories,
        'dish_one_allergens': dish_one.allergens,

        'dish_two': dish_two,
        'dish_two_name': dish_two.dish_name,
        'dish_two_description': dish_two.description,
        'dish_two_price': dish_two.price,
        'dish_two_is_avaible': dish_two.is_available,
        'dish_two_cooking_time_min': dish_two.cooking_time_min,
        'dish_two_calories': dish_two.calories,
        'dish_two_allergens': dish_two.allergens,

        'dish_three': dish_three,
        'dish_three_name': dish_three.dish_name,
        'dish_three_description': dish_three.description,
        'dish_three_price': dish_three.price,
        'dish_three_is_avaible': dish_three.is_available,
        'dish_three_cooking_time_min': dish_three.cooking_time_min,
        'dish_three_calories': dish_three.calories,
        'dish_three_allergens': dish_three.allergens,

        'dish_four': dish_four,
        'dish_four_name': dish_four.dish_name,
        'dish_four_description': dish_four.description,
        'dish_four_price': dish_four.price,
        'dish_four_is_avaible': dish_four.is_available,
        'dish_four_cooking_time_min': dish_four.cooking_time_min,
        'dish_four_calories': dish_four.calories,
        'dish_four_allergens': dish_four.allergens,

        'dish_five': dish_five,
        'dish_five_name': dish_five.dish_name,
        'dish_five_description': dish_five.description,
        'dish_five_price': dish_five.price,
        'dish_five_is_avaible': dish_five.is_available,
        'dish_five_cooking_time_min': dish_five.cooking_time_min,
        'dish_five_calories': dish_five.calories,
        'dish_five_allergens': dish_five.allergens,

        'dish_six': dish_six,
        'dish_six_name': dish_six.dish_name,
        'dish_six_description': dish_six.description,
        'dish_six_price': dish_six.price,
        'dish_six_is_avaible': dish_six.is_available,
        'dish_six_cooking_time_min': dish_six.cooking_time_min,
        'dish_six_calories': dish_six.calories,
        'dish_six_allergens': dish_six.allergens,

        'dish_seven': dish_seven,
        'dish_seven_name': dish_seven.dish_name,
        'dish_seven_description': dish_seven.description,
        'dish_seven_price': dish_seven.price,
        'dish_seven_is_avaible': dish_seven.is_available,
        'dish_seven_cooking_time_min': dish_seven.cooking_time_min,
        'dish_seven_calories': dish_seven.calories,
        'dish_seven_allergens': dish_seven.allergens,

        'dish_eight': dish_eight,
        'dish_eight_name': dish_eight.dish_name,
        'dish_eight_description': dish_eight.description,
        'dish_eight_price': dish_eight.price,
        'dish_eight_is_avaible': dish_eight.is_available,
        'dish_eight_cooking_time_min': dish_eight.cooking_time_min,
        'dish_eight_calories': dish_eight.calories,
        'dish_eight_allergens': dish_eight.allergens,

        'dish_nine': dish_nine,
        'dish_nine_name': dish_nine.dish_name,
        'dish_nine_description': dish_nine.description,
        'dish_nine_price': dish_nine.price,
        'dish_nine_is_avaible': dish_nine.is_available,
        'dish_nine_cooking_time_min': dish_nine.cooking_time_min,
        'dish_nine_calories': dish_nine.calories,
        'dish_nine_allergens': dish_nine.allergens,

        'dish_ten': dish_ten,
        'dish_ten_name': dish_ten.dish_name,
        'dish_ten_description': dish_ten.description,
        'dish_ten_price': dish_ten.price,
        'dish_ten_is_avaible': dish_ten.is_available,
        'dish_ten_cooking_time_min': dish_ten.cooking_time_min,
        'dish_ten_calories': dish_ten.calories,
        'dish_ten_allergens': dish_ten.allergens,

        'dish_eleven': dish_eleven,
        'dish_eleven_name': dish_eleven.dish_name,
        'dish_eleven_description': dish_eleven.description,
        'dish_eleven_price': dish_eleven.price,
        'dish_eleven_is_avaible': dish_eleven.is_available,
        'dish_eleven_cooking_time_min': dish_eleven.cooking_time_min,
        'dish_eleven_calories': dish_eleven.calories,
        'dish_eleven_allergens': dish_eleven.allergens,

        'dish_twelve': dish_twelve,
        'dish_twelve_name': dish_twelve.dish_name,
        'dish_twelve_description': dish_twelve.description,
        'dish_twelve_price': dish_twelve.price,
        'dish_twelve_is_avaible': dish_twelve.is_available,
        'dish_twelve_cooking_time_min': dish_twelve.cooking_time_min,
        'dish_twelve_calories': dish_twelve.calories,
        'dish_twelve_allergens': dish_one.allergens,

        'dish_thirteen': dish_thirteen,
        'dish_thirteen_name': dish_thirteen.dish_name,
        'dish_thirteen_description': dish_thirteen.description,
        'dish_thirteen_price': dish_thirteen.price,
        'dish_thirteen_is_avaible': dish_thirteen.is_available,
        'dish_thirteen_cooking_time_min': dish_thirteen.cooking_time_min,
        'dish_thirteen_calories': dish_thirteen.calories,
        'dish_thirteen_allergens': dish_thirteen.allergens,

        'dish_fourteen': dish_fourteen,
        'dish_fourteen_name': dish_fourteen.dish_name,
        'dish_fourteen_description': dish_fourteen.description,
        'dish_fourteen_price': dish_fourteen.price,
        'dish_fourteen_is_avaible': dish_fourteen.is_available,
        'dish_fourteen_cooking_time_min': dish_fourteen.cooking_time_min,
        'dish_fourteen_calories': dish_fourteen.calories,
        'dish_fourteen_allergens': dish_fourteen.allergens,

        'dish_fiveteen': dish_fiveteen,
        'dish_fiveteen_name': dish_fiveteen.dish_name,
        'dish_fiveteen_description': dish_fiveteen.description,
        'dish_fiveteen_price': dish_fiveteen.price,
        'dish_fiveteen_is_avaible': dish_fiveteen.is_available,
        'dish_fiveteen_cooking_time_min': dish_fiveteen.cooking_time_min,
        'dish_fiveteen_calories': dish_fiveteen.calories,
        'dish_fiveteen_allergens': dish_fiveteen.allergens,

        'dish_sixteen': dish_sixteen,
        'dish_sixteen_name': dish_sixteen.dish_name,
        'dish_sixteen_description': dish_sixteen.description,
        'dish_sixteen_price': dish_sixteen.price,
        'dish_sixteen_is_avaible': dish_sixteen.is_available,
        'dish_sixteen_cooking_time_min': dish_sixteen.cooking_time_min,
        'dish_sixteen_calories': dish_sixteen.calories,
        'dish_sixteen_allergens': dish_sixteen.allergens,

        'dish_seventeen': dish_seventeen,
        'dish_seventeen_name': dish_seventeen.dish_name,
        'dish_seventeen_description': dish_seventeen.description,
        'dish_seventeen_price': dish_seventeen.price,
        'dish_seventeen_is_avaible': dish_seventeen.is_available,
        'dish_seventeen_cooking_time_min': dish_seventeen.cooking_time_min,
        'dish_seventeen_calories': dish_seventeen.calories,
        'dish_seventeen_allergens': dish_seventeen.allergens,

        'dish_eighteen': dish_eighteen,
        'dish_eighteen_name': dish_eighteen.dish_name,
        'dish_eighteen_description': dish_eighteen.description,
        'dish_eighteen_price': dish_eighteen.price,
        'dish_eighteen_is_avaible': dish_eighteen.is_available,
        'dish_eighteen_cooking_time_min': dish_eighteen.cooking_time_min,
        'dish_eighteen_calories': dish_eighteen.calories,
        'dish_eighteen_allergens': dish_eighteen.allergens,

        'dish_nineteen': dish_nineteen,
        'dish_nineteen_name': dish_nineteen.dish_name,
        'dish_nineteen_description': dish_nineteen.description,
        'dish_nineteen_price': dish_nineteen.price,
        'dish_nineteen_is_avaible': dish_nineteen.is_available,
        'dish_nineteen_cooking_time_min': dish_nineteen.cooking_time_min,
        'dish_nineteen_calories': dish_nineteen.calories,
        'dish_nineteen_allergens': dish_nineteen.allergens,

        'dish_twenty': dish_twenty,
        'dish_twenty_name': dish_twenty.dish_name,
        'dish_twenty_description': dish_twenty.description,
        'dish_twenty_price': dish_twenty.price,
        'dish_twenty_is_avaible': dish_twenty.is_available,
        'dish_twenty_cooking_time_min': dish_twenty.cooking_time_min,
        'dish_twenty_calories': dish_twenty.calories,
        'dish_twenty_allergens': dish_twenty.allergens,

    }
    return render(request, 'menu/menu.html', data_menu)

def contact(request):
    data_contact = {
        'title': 'Контакты',
    }
    return render(request, 'menu/contact.html', data_contact)