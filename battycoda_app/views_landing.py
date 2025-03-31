"""
Landing page view for BattyCoda application.
"""

from django.shortcuts import render

def landing_page(request):
    """Display a landing page with information about BattyCoda"""
    return render(request, "landing.html")