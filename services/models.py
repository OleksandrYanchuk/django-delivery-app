from django.db import models

from user.models import Customer


class Shop(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Goods(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(
        max_length=255, null=True, blank=True, decimal_places=2, max_digits=10
    )
    shop_name = models.ForeignKey(Shop, related_name="goods", on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ["name", "shop_name"]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        Customer, on_delete=models.CASCADE
    )  # Посилання на користувача, який володіє кошиком
    goods = models.ManyToManyField(
        "Goods", through="CartItem"
    )  # Товари в кошику через проміжну модель

    def __str__(self):
        return f"Shopping Cart for {self.user.name}"


class CartItem(models.Model):
    shopping_cart = models.ForeignKey(
        ShoppingCart, on_delete=models.CASCADE
    )  # Посилання на кошик
    goods = models.ForeignKey("Goods", on_delete=models.CASCADE)  # Посилання на товар
    quantity = models.PositiveIntegerField(default=1)  # Кількість товару в кошику

    def __str__(self):
        return f"{self.quantity} x {self.goods.name}"

    def total_price(self):
        return self.quantity * self.goods.price


class Order(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    goods = models.ManyToManyField(Goods, through="OrderItem")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name="order_items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(Goods, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
