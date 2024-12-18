from django.shortcuts import render
from .models import Product, CaUser, ShoppingBasket, ShoppingBasketItems, OrderItems
from .forms import *
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.views.generic import CreateView
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .permissions import admin_required
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.core import serializers
from rest_framework import viewsets
from .serializers import *
from rest_framework.authtoken.models import Token
from django.http import HttpResponseRedirect, HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authtoken.models import Token
import json
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def index(request):
    return render(request, 'index.html')

def register(request):
    return render(request, 'registration.html')

def all_products(request):
    all_p = Product.objects.all()
    flag = request.GET.get('format', '')
    if flag == "json":
        #return json data
        serialised_products = serializers.serialize("json", all_p)
        return HttpResponse(serialised_products, content_type="application/json")
    else:
        return render(request, 'all_products.html', {'products': all_p})

def singleproduct(request, prodid):
    prod = get_object_or_404(Product, pk=prodid)
    return render(request, 'single_product.html', {'product': prod})

#@admin_required()
@login_required()
def myform(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            new_product = form.save()
            return render(request, 'single_product.html', {'product': new_product})
    else:
        # we want to show the form
        form = ProductForm()
        return render(request, 'form.html', {'form': form})

# def productForm(request):


class CaUserSignupView(CreateView):
    model = CaUser
    form_class = CASignupForm
    template_name = 'causer_signup.html'
    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('/')

class AdminSignupView(CreateView):
    model = CaUser
    form_class = AdminSignupForm
    template_name = 'admin_signup.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('/')



from django.contrib.auth.views import LoginView

class Login(LoginView):
    template_name = 'login.html'

def logout_view(request):
    logout(request)
    return redirect('/')

def contact(request):
    return render(request, 'contact.html')

def about(request):
    return render(request, 'about.html')


@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
@login_required
def add_to_basket(request, prodid):
    user = request.user
    if user.is_anonymous:
        token = request.META.get('HTTP_AUTHORIZATION').split(" ")[1]
        user = Token.objects.get(key=token).user

    shopping_basket = ShoppingBasket.objects.filter(user_id=user).first()
    if not shopping_basket:
        shopping_basket = ShoppingBasket(user_id=user).save()
    # TODO: handle product ID gracefully
    product = Product.objects.get(pk=prodid)
    sbi = ShoppingBasketItems.objects.filter(basket_id=shopping_basket.id, products_id=product.id).first()
    if sbi is None:
        sbi = ShoppingBasketItems(basket_id=shopping_basket, products_id=product.id).save()
    else:
        sbi.quantity = sbi.quantity+1
        sbi.save()
    flag = request.GET.get('format', '')
    if flag == "json":
        return JsonResponse({'status': 'success'}) # HttpResponse({'status':'x'}, content_type='application/json)
    else:
        return render(request, 'single_product.html', {'product': product, 'added': True})

@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
@login_required
def get_basket(request):
    user = request.user
    if user.is_anonymous:
        token = request.META.get('HTTP_AUTHORIZATION').split(" ")[1]
        user = Token.objects.get(key=token).user
    shopping_basket = ShoppingBasket.objects.filter(user_id=user).first()
    if not shopping_basket:
        shopping_basket = ShoppingBasket(user_id=user).save()
    sbi = ShoppingBasketItems.objects.filter(basket_id=shopping_basket.id)
    flag = request.GET.get('format', '')
    if flag == "json":
        basket_array = []
        for basket_item in sbi:
            tmp = {}
            tmp['product'] = basket_item.product.name
            tmp['price'] = float(basket_item.product.price)
            tmp['quantity'] = int(basket_item.quantity)
            basket_array.append(tmp)
        return HttpResponse(json.dumps({'items': basket_array}), content_type="application/json")
    else:
        return render(request, 'shopping_basket.html', {'basket': shopping_basket, 'items': sbi})

@login_required
def remove_from_basket(request, sbi):
    sb = ShoppingBasketItems.objects.get(pk=sbi).delete()
    return redirect('/basket')

@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
@login_required
def order_form(request):
    user = request.user
    if user.is_anonymous:
        token = request.META.get('HTTP_AUTHORIZATION').split(" ")[1]
        user = Token.objects.get(key=token).user
    shopping_basket = ShoppingBasket.objects.filter(user_id=user).first()
    if not shopping_basket:
        return redirect(request, '/') #TODO: Notification that shopping basket is empty
    sbi = ShoppingBasketItems.objects.filter(basket_id=shopping_basket.id)
    if request.method == 'POST':
        if not request.POST: # if the data is not inside the request.POSt, it is inside the body
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            form = OrderForm(body)
        else:
            form = OrderForm(request.POST)
        print(form.errors)
        if form.is_valid():
            # create order item for each order in shopping basket

            order = form.save(commit=False)
            order.user_id = user
            order.save()
            order_items = []
            for basketitem in sbi:
                order_item = OrderItems(order_id=order, product_id=basketitem.product, quantity=basketitem.quantity)
                order_items.append(order_item)
            # delete the shopping basket
            shopping_basket.delete()
            flag = request.GET.get('format', '')  # url?format=json&name=John   {'format':'json', 'name':'John'}
            if flag == "json":
                return JsonResponse({"status": "success"})
            else:
                return render(request, 'order_complete.html', {'order': order, 'items':order_items})
    else:
        form = OrderForm()
        return render(request, 'order_form.html', {'form': form, 'basket':shopping_basket, 'items': sbi})


class UserViewSet(viewsets.ModelViewSet):
    queryset = CaUser.objects.all()
    serializer_class = UserSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer