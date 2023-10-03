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
        fields = ["name", "email", "phone_number", "address", "user_lat", "user_lng"]

    name = forms.CharField(max_length=255, required=True)
    email = forms.EmailField(max_length=255, required=True)
    phone_number = forms.CharField(max_length=14, required=True)
    address = forms.CharField(max_length=255, required=True)
    user_lat = forms.FloatField(required=False)
    user_lng = forms.FloatField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Заблокуйте поля name і email, щоб вони були лише для перегляду
        self.fields["name"].widget.attrs["readonly"] = True
        self.fields["email"].widget.attrs["readonly"] = True
        self.fields["user_lat"].widget.attrs["readonly"] = True
        self.fields["user_lng"].widget.attrs["readonly"] = True


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


# Форма для створення купону
class CreateCouponForm(forms.Form):
    pass


# Форма для відображення активних купонів
class ActiveCouponsForm(forms.Form):
    pass
