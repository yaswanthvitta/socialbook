from django.urls import path
from . import views

urlpatterns = [
    path('',views.index,name='index'),
    path('signup',views.signup,name='signup'),
    path('activate/<uid64>/<token>',views.activate,name="activate"),
    path('signin',views.signin,name='signin'),
    path('logout',views.logout,name='logout'),
    path('settings',views.settings1,name='settings'),
    path('upload',views.upload,name='upload'),
    path('like-post',views.like_post,name='like-post'),
    path('profile/<str:pk>',views.profile,name='profile'),
    path('follow',views.follow,name='follow'),
    path('search',views.search,name='search'),

]