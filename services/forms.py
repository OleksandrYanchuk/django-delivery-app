from django import forms
from .models import Shop, Goods, ShoppingCart, CartItem, Order, OrderItem


class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ["name"]


class GoodsForm(forms.ModelForm):
    class Meta:
        model = Goods
        fields = ["name", "price", "shop_name"]


class ShoppingCartForm(forms.ModelForm):
    class Meta:
        model = ShoppingCart
        fields = ["user", "goods"]


class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ["shopping_cart", "goods", "quantity"]


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = []


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ["product", "quantity"]
