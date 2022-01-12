
from django.test import TestCase, RequestFactory
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Category, Notebook, Cart, CartProduct, Customer
from .views import recalc_cart, AddToCartView



User = get_user_model()


class ChopTestCases(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(username='testuser', password='password')
        self.category = Category.objects.create(name='Ноутбуки', slug='notebook')
        image = SimpleUploadedFile('notebook_image.jpg', content=b'', content_type='image/jpg')
        self.notebook = Notebook.objects.create(
            category=self.category,
            title='Test_notebook',
            image=image,
            price=Decimal('50000'),
            diagonal='15',
            display='IPS',
            processor_freq='3,4',
            ram='6 GB',
            video='GeForce',
            time_without_charge='10 hours'
        )
        self.customer = Customer.objects.create(user=self.user, phone='111111', address='Address')
        self.cart = Cart.objects.create(owner=self.customer)
        self.cart_product = CartProduct.objects.create(
            user=self.customer,
            cart=self.cart,
            content_object=self.notebook
        )

    def test_add_to_cart(self):
        self.cart.product.add(self.cart_product)
        recalc_cart(self.cart)
        self.assertIn(self.cart_product, self.cart.product.all())
        self.assertEqual(self.cart.product.count(), 1)
        self.assertEqual(self.cart.final_price, Decimal('50000'))

    def test_response_from_add_to_cart_view(self):
        factory = RequestFactory()
        request = factory.get('')
        request.user = self.user
        response = AddToCartView.as_view()(request, ct_model='notebook', slug='test-slug')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/cart/')

