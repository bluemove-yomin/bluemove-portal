from django.shortcuts import render, redirect


####
#### views
####
def main(request):
    return render(request, "home/main.html")
