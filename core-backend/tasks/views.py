from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import generics, permissions
from .serializers import TaskSerializer
from .models import Task
from django.contrib.auth.models import User
# Create your views here.


def index(request):
    return HttpResponse("Tasks")

class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user__username=self.request.user)
    
    def perform_create(self, serializer):
        user = User.objects.get(username=self.request.user)
        return serializer.save(user=user)

