from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.models import User,auth 
from django.contrib import messages
from .models import Profile,Post,LikePost,FollowersCount
from django.contrib.auth.decorators import login_required
from itertools import chain
from socialbook import settings
import random
from django.contrib.auth import authenticate, login , logout
from django.core.mail import send_mail, EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes,force_str
from .tokens import generate_token
# Create your views here.


@login_required(login_url='signin')
def index(request):
    user_object=User.objects.get(username=request.user.username)
    try:
        user_profile=Profile.objects.get(user=user_object)
    except Profile.DoesNotExist:
        pass
    user_following_list =[]
    feed =[]

    user_following=FollowersCount.objects.filter(follower=request.user.username)
    for users in user_following:
        user_following_list.append(users.user)
    
    for usernames in user_following_list:
        feed_lists=Post.objects.filter(user=usernames)
        feed.append(feed_lists)
    
    feed_list = list(chain(*feed))
    
    all_users=User.objects.all()
    user_following_all=[]

    for user in user_following:
        user_list=User.objects.get(username=user.user)
        user_following_all.append(user_list)

    new_suggestions_list=[x for x in list(all_users) if(x not in list(user_following_all))]
    current_user=User.objects.filter(username=request.user.username)
    final_suggestions_list=[ x for x in list(new_suggestions_list) if (x not in list(current_user))]
    random.shuffle(final_suggestions_list)

    username_profile=[]
    username_profile_list=[]

    for users in final_suggestions_list:
        username_profile.append(users.id)
    for ids in username_profile:
        profile_list=Profile.objects.filter(id_user=ids)
        username_profile_list.append(profile_list)
    
    suggestions_username_profile_list=list(chain(*username_profile_list))
    posts=Post.objects.all()
    return render(request ,'index.html', {'user_profile':user_profile, 'posts':feed_list, 'suggestions_username_profile_list':suggestions_username_profile_list[:4]})

@login_required(login_url='signin')
def settings1(request):
    try:
        user_profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        pass
    
    if request.method=="POST":
        if request.FILES.get('image')==None:
            image=user_profile.profileimg
            bio=request.POST['bio']
            location=request.POST['location']

            user_profile.profileimg=image
            user_profile.bio=bio
            user_profile.location=location
            user_profile.save()
        if request.FILES.get('image') != None:
            image=request.FILES.get('image')
            bio=request.POST['bio']
            location=request.POST['location']

            user_profile.profileimg=image
            user_profile.bio=bio
            user_profile.location=location
            user_profile.save()
        
        return redirect('settings')


    return render(request, 'setting.html',{'user_profile': user_profile})

def signup(request):

    if request.method =='POST':
        username=request.POST['username']
        email=request.POST['email']
        password=request.POST['password']
        password2=request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request,'Email Taken')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request,'Username is already Taken')
                return redirect('signup')
            else:
                user=User.objects.create_user(username=username,email=email,password=password)
                user.save()
            
            user_login = auth.authenticate(username=username,password=password)
            auth.login(request,user_login)
            
            user_model =User.objects.get(username=username)
            new_profile=Profile.objects.create(user=user_model,id_user=user_model.id) 
            new_profile.save()
            subject = "WELCOME to ConnectSphere"

            message = "HELLO"+ user.username + "!! \n" +"WELCOME to ConnectSphere!! \n"+"WE HAVE ALSO SENT A CONFIRMATION EMAIL, PLEASE CONFIRM EMAIL ADERESS"

            from_email = settings.EMAIL_HOST_USER

            to_list=[user.email]

            send_mail(subject,message,from_email,to_list,fail_silently=True,)

            # Email Address Confirmation Email

            current_site = get_current_site(request)

            email_subject = "confrim your email"

            message2= render_to_string('email_confirmation.html',{
                'name':user.username,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':generate_token.make_token(user),

            })

            email= EmailMessage (
                email_subject,
                message2,
                settings.EMAIL_HOST_USER,
                [user.email],
            )
            
            email.fail_silently = True
            email.send()
            return redirect('signup')
            
        else:
            messages.info(request,'Password Not Matching')
            return redirect('signup')

    else:
        return render(request ,'signup.html')

def activate(request,uid64,token):
    try:
        uid = force_str(urlsafe_base64_decode(uid64))
        myuser = User.objects.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        myuser =None 
    if myuser is not None and generate_token.check_token(myuser,token):
        myuser.is_active=True
        myuser.save()
        login(request,myuser)
        return redirect('index')
    else:
        return render(request,'activation_failed.html')

def signin(request):
    if request.method=="POST":
        username = request.POST['username']
        password = request.POST['password']

        user=auth.authenticate(username=username,password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request,'Credentials Invalid')
            return redirect('signin')

    else:
        return render(request, 'signin.html')
    
@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')

@login_required(login_url='signin')
def upload(request):
    if request.method =='POST':
        user =request.user.username
        image=request.FILES.get('image_upload')
        caption = request.POST['caption']

        new_post=Post.objects.create(user=user,image=image,caption=caption)
        new_post.save()

        return redirect("/")
    else:
        return redirect('/')
    return HttpResponse('<h1>Up</h1>')
@login_required(login_url='signin')
def like_post(request):
    username=request.user.username
    post_id=request.GET.get('post_id')

    post=Post.objects.get(id=post_id)
    like_filter =LikePost.objects.filter(post_id=post_id,username=username).first()

    if like_filter == None:
        new_like=LikePost.objects.create(post_id=post_id,username=username)
        new_like.save()

        post.no_of_likes=post.no_of_likes+1
        post.save()
        return redirect('/')
    else:
        like_filter.delete()
        post.no_of_likes=post.no_of_likes-1
        post.save()
        return redirect('/')
    

@login_required(login_url='signin')  
def profile(request,pk):
    user_object = User.objects.get(username=pk)
    try:
        user_profile=Profile.objects.get(user=user_object)
    except Profile.DoesNotExist:
        pass
    user_posts=Post.objects.filter(user=pk)
    user_post_length=len(user_posts)

    follower=request.user.username
    user=pk

    if FollowersCount.objects.filter(follower=follower,user=user).first():
        button_text='Unfollow'
    else:
        button_text='Follow'

    user_followers=len(FollowersCount.objects.filter(user=pk))
    user_followeing=len(FollowersCount.objects.filter(follower=pk))

    context={
        'user_object':user_object,
        'user_profile':user_profile,
        'user_posts':user_posts,
        'user_post_length':user_post_length,
        'button_text':button_text,
        'user_followers':user_followers,
        'user_followeing':user_followeing,
    }
    return render(request ,'profile.html', context)


@login_required(login_url='signin')  
def follow(request):
    if request.method =='POST':
        follower=request.POST['follower']
        user=request.POST['user']

        if FollowersCount.objects.filter(follower=follower,user=user).first():
            delete_follower = FollowersCount.objects.get(follower=follower,user=user)
            delete_follower.delete()
            return redirect('/profile/'+user)
        else:
            new_follower = FollowersCount.objects.create(follower=follower,user=user)
            new_follower.save()
            return redirect('/profile/'+user)

       
    else:
        return redirect('/')
@login_required(login_url='signin')  
def search(request):
    user_object = User.objects.get(username=request.user.username)
    try:
        user_profile=Profile.objects.get(user=user_object)
    except Profile.DoesNotExist:
        pass
    if request.method=='POST':
        username=request.POST['username']
        username_object=User.objects.filter(username__icontains=username)

        username_profile=[]
        username_profile_list=[]

        for users in username_object:
            username_profile.append(users.id)
        
        for ids in username_profile:
            profile_lists=Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_lists)
        
        username_profile_list=list(chain(*username_profile_list))


    return render(request,'search.html',{'user_profile':user_profile, 'username_profile_list':username_profile_list})

