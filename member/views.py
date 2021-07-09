from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# models
from django.contrib.auth.models import User
from .models import Profile


####
#### views
####
@login_required
def myaccount(request):
    # str, lst
    last_name = request.POST.get("last_name")
    first_name = request.POST.get("first_name")
    phone = request.POST.get("phone")
    # boolean
    modified = None
    if request.method == "POST":
        user = User.objects.get(id=request.user.id)
        user.last_name = last_name
        user.first_name = first_name
        user.save()
        profile = Profile.objects.get(user=request.user)
        profile.phone = phone
        profile.save()
        modified = True
    return render(
        request,
        "member/myaccount.html",
        {
            # boolean
            "modified": modified
        },
    )
