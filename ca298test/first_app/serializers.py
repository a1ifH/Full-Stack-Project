from django.urls import path, include
from .models import CaUser, Product  # Import your model
from rest_framework import serializers

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CaUser
        fields = '__all__'  # Note this is a double underscore !

class ProductSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'  # Note this is a double underscore !