import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import (
    HttpResponseRedirect,
    JsonResponse,
    HttpResponseBadRequest,
    HttpResponse,
)
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from .models import Shop, Goods, ShoppingCart, CartItem, Order, OrderItem
from .forms import (
    ShopForm,
    GoodsForm,
    ShoppingCartForm,
    CartItemForm,
    OrderForm,
)


class ShopListView(ListView):
    model = Shop
    template_name = "shop/shop_list.html"
    context_object_name = "shop_list"


class ShopDetailView(DetailView):
    model = Shop
    template_name = "shop/shop_detail.html"
    context_object_name = "shop"


class CreateShopView(CreateView):
    model = Shop
    form_class = ShopForm
    template_name = "create_shop.html"
    success_url = reverse_lazy("shop_list")


# Аналогічно, додайте класи для Goods, ShoppingCart і CartItem


class GoodsListView(ListView):
    model = Goods
    template_name = "goods_list.html"
    context_object_name = "goods"


class CreateGoodsView(CreateView):
    model = Goods
    form_class = GoodsForm
    template_name = "create_goods.html"
    success_url = reverse_lazy("goods_list")


class ShoppingCartView(CreateView):
    model = ShoppingCart
    form_class = ShoppingCartForm
    template_name = "shopping_cart/shopping_cart.html"
    success_url = reverse_lazy("shopping_cart")


class ShoppingCartDetailView(DetailView):
    model = ShoppingCart
    template_name = "shopping_cart_detail.html"
    context_object_name = "shopping_cart_detail"


class CartItemView(CreateView):
    model = CartItem
    form_class = CartItemForm
    template_name = "cart_item.html"
    success_url = reverse_lazy("cart_item")


class CartItemDetailView(DetailView):
    model = CartItem
    template_name = "cart_item_detail.html"
    context_object_name = "cart_item_detail"


class ShopGoodsDetailView(DetailView):
    model = Shop
    template_name = "shop/shop_goods_detail.html"
    context_object_name = "shop"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop = self.get_object()  # Отримуємо об'єкт магазину
        goods = Goods.objects.filter(shop_name=shop)  # Фільтруємо товари за магазином
        context["goods"] = goods  # Передаємо список товарів у контекст
        context["shop_list"] = Shop.objects.all()
        return context


@login_required
def add_to_cart(request):
    if request.method == "POST":
        goods_id = request.POST.get("goods", None)
        if goods_id:
            goods = get_object_or_404(Goods, id=goods_id)

            # Перевірка, чи у користувача вже є кошик для покупок
            shopping_cart, created = ShoppingCart.objects.get_or_create(
                user=request.user
            )

            # Перевірка, чи всі товари в кошику належать до одного магазину
            if (
                shopping_cart.goods.filter(shop_name=goods.shop_name).exists()
                or not shopping_cart.goods.all()
            ):
                # Створення нового елемента кошика з товаром і додавання до кошика
                cart_item, created = CartItem.objects.get_or_create(
                    shopping_cart=shopping_cart, goods=goods
                )

                # Якщо товар вже був у кошику, збільшуємо кількість на одиницю
                if not created:
                    cart_item.quantity += 1
                    cart_item.save()

                return HttpResponseRedirect(
                    reverse("services:shop_goods_detail", args=[goods.shop_name.id])
                )
            else:
                # Додайте повідомлення про помилку до контексту
                messages.error(
                    request, "Cannot add items from different shops to the cart"
                )
                return HttpResponseRedirect(reverse("services:shop_goods_detail"))

    # Якщо дані некоректні або HTTP метод GET
    return HttpResponseRedirect(reverse("services:shop_goods_detail"))


def shopping_cart(request):
    # Отримайте кошик поточного користувача
    shopping_cart, created = ShoppingCart.objects.get_or_create(user=request.user)

    # Отримайте всі товари у кошику
    cart_items = CartItem.objects.filter(shopping_cart=shopping_cart)
    totals = get_totals(cart_items)
    lat = 0
    lng = 0
    for cart_item in cart_items:
        lat = cart_item.goods.shop_name.lat
        lng = cart_item.goods.shop_name.lng

    context = {
        "cart_items": cart_items,
        "totals": totals,
        "name": shopping_cart.user.name,
        "email": shopping_cart.user.email,
        "phone_number": shopping_cart.user.phone_number,
        "address": shopping_cart.user.address,
        "lat": lat,
        "lng": lng,
    }
    # Додайте вивід для перевірки координат
    for cart_item in cart_items:
        print(
            f"Координати магазину для товару {cart_item.goods.shop_name.name}: lat {cart_item.goods.shop_name.lat}, lng {cart_item.goods.shop_name.lng}"
        )

    return render(request, "shopping_cart/shopping_cart.html", context)


def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    totals = get_totals(cart_items)
    return render(
        request,
        "shopping_cart/checkout.html",
        {"cart_items": cart_items, "totals": totals},
    )


@login_required
def update_cart_item(request):
    if (
        request.method == "POST"
        and request.headers.get("x-requested-with") == "XMLHttpRequest"
    ):
        item_id = request.POST.get("item_id")
        new_quantity = int(request.POST.get("new_quantity", 1))

        # Отримайте об'єкт cart_item за його ідентифікатором item_id
        cart_item = get_object_or_404(CartItem, id=item_id)

        # Оновіть кількість товару
        cart_item.quantity = new_quantity
        cart_item.save()

        # Отримайте оновлену інформацію про товар для повернення на клієнтський бік
        updated_item_html = render_to_string(
            "shopping_cart/cart_item.html", {"item": cart_item}
        )

        response_data = {"updated_item_html": updated_item_html}
        return JsonResponse(response_data)

    return HttpResponseBadRequest()


@login_required
def remove_cart_item(request):
    if (
        request.method == "POST"
        and request.headers.get("x-requested-with") == "XMLHttpRequest"
    ):
        item_id = request.POST.get("item_id")

        cart_item = get_object_or_404(CartItem, id=item_id)
        cart_item.delete()

        return JsonResponse({"success": True})

    return HttpResponseBadRequest()


def get_totals(cart_items):
    totals = [item.quantity * item.goods.price for item in cart_items]
    return totals


class OrderCreateView(CreateView):
    model = Order
    form_class = OrderForm
    template_name = "order/order_create.html"
    success_url = "/delivery/order-list/"

    @transaction.atomic
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.total_amount = 0  # Початкова сума замовлення

        # Створіть номер замовлення на основі поточного часу та дати
        now = timezone.now()
        order_number = f"{now.strftime('%Y%m%d%H%M%S')}_{self.request.user.id}"

        form.instance.order_number = order_number  # Встановіть номер замовлення

        # Отримайте кошик поточного користувача
        shopping_cart, created = ShoppingCart.objects.get_or_create(
            user=self.request.user
        )

        # Отримайте всі товари у кошику
        cart_items = CartItem.objects.filter(shopping_cart=shopping_cart)

        # Обчисліть суму всіх товарів у кошику і встановіть її як total_amount
        total_amount = sum(item.quantity * item.goods.price for item in cart_items)
        form.instance.total_amount = total_amount

        # Збережіть об'єкт Order
        order = form.save()

        # Створіть об'єкти OrderItem для всіх товарів у кошику
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.goods,
                quantity=cart_item.quantity,
            )

        # Видаліть всі елементи кошика, пов'язані з поточним користувачем
        cart_items.delete()

        return super().form_valid(form)


# Class-based view для відображення списку замовлень (order list view)
class OrderListView(ListView):
    model = Order
    template_name = "order/order_list.html"
    context_object_name = (
        "orders"  # Ім'я змінної, яку ви будете використовувати у шаблоні
    )


class OrderDetailView(DetailView):
    model = Order
    template_name = "order/order_detail.html"
    context_object_name = "order"


# Class-based view для редагування/видалення елементу замовлення (order item view)
class OrderItemDetailView(DetailView):
    model = OrderItem
    template_name = "order/order_item_detail.html"
    context_object_name = "order_item"


def update_user_info(request):
    if (
        request.method == "POST"
        and request.headers.get("x-requested-with") == "XMLHttpRequest"
    ):
        new_phone_number = request.POST.get("phone_number")
        new_address = request.POST.get("address")

        # Отримайте користувача з об'єкта запиту
        user = request.user

        # Оновіть дані користувача
        user.phone_number = new_phone_number
        user.address = new_address
        user.save()

        return JsonResponse({"success": True})

    return JsonResponse({"message": "Not an AJAX request"}, status=400)
