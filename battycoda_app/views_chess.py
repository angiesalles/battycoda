"""Chess proxy view for BattyCoda application."""

import requests
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt


@login_required
@csrf_exempt
def chess_proxy_view(request, path=''):
    """
    Proxy requests to a local chess server running on port 9000.
    Only available to authenticated users.
    """
    # Build the target URL
    target_url = f"http://localhost:9000/{path}"
    
    # Forward query parameters
    if request.GET:
        query_string = request.GET.urlencode()
        target_url += f"?{query_string}"
    
    try:
        # Prepare headers (remove some Django-specific headers)
        headers = {}
        for key, value in request.META.items():
            if key.startswith('HTTP_'):
                # Convert HTTP_HEADER_NAME to Header-Name
                header_name = key[5:].replace('_', '-').title()
                # Skip some headers that might cause issues
                if header_name not in ['Host', 'Connection', 'Content-Length']:
                    headers[header_name] = value
        
        # Make the request to the chess server
        if request.method == 'GET':
            response = requests.get(target_url, headers=headers, stream=True, timeout=30)
        elif request.method == 'POST':
            response = requests.post(
                target_url, 
                data=request.body, 
                headers=headers, 
                stream=True, 
                timeout=30
            )
        elif request.method == 'PUT':
            response = requests.put(
                target_url, 
                data=request.body, 
                headers=headers, 
                stream=True, 
                timeout=30
            )
        elif request.method == 'DELETE':
            response = requests.delete(target_url, headers=headers, timeout=30)
        else:
            # For other methods, just pass through
            response = requests.request(
                request.method,
                target_url, 
                data=request.body, 
                headers=headers, 
                stream=True, 
                timeout=30
            )
        
        # For streaming responses (like WebSocket upgrades or large files)
        if 'text/html' in response.headers.get('content-type', '') or \
           'application/javascript' in response.headers.get('content-type', '') or \
           'text/css' in response.headers.get('content-type', ''):
            # For HTML, JS, CSS - return the content directly
            django_response = HttpResponse(
                response.content,
                status=response.status_code,
                content_type=response.headers.get('content-type', 'text/html')
            )
        else:
            # For other content types, stream the response
            django_response = StreamingHttpResponse(
                response.iter_content(chunk_size=8192),
                status=response.status_code,
                content_type=response.headers.get('content-type', 'application/octet-stream')
            )
        
        # Copy relevant headers from the chess server response
        for key, value in response.headers.items():
            if key.lower() not in ['connection', 'transfer-encoding', 'content-encoding']:
                django_response[key] = value
        
        return django_response
        
    except requests.exceptions.ConnectionError:
        return HttpResponse(
            "<h1>Chess Server Unavailable</h1>"
            "<p>The chess server on port 9000 is not running or not accessible.</p>"
            f"<p><a href='{reverse('battycoda_app:index')}'>← Back to BattyCoda</a></p>",
            status=503,
            content_type='text/html'
        )
    except requests.exceptions.Timeout:
        return HttpResponse(
            "<h1>Chess Server Timeout</h1>"
            "<p>The chess server took too long to respond.</p>"
            f"<p><a href='{reverse('battycoda_app:index')}'>← Back to BattyCoda</a></p>",
            status=504,
            content_type='text/html'
        )
    except Exception as e:
        return HttpResponse(
            f"<h1>Chess Proxy Error</h1>"
            f"<p>Error connecting to chess server: {str(e)}</p>"
            f"<p><a href='{reverse('battycoda_app:index')}'>← Back to BattyCoda</a></p>",
            status=500,
            content_type='text/html'
        )


@login_required
def chess_home_view(request):
    """
    Redirect to the chess proxy root.
    """
    return redirect('battycoda_app:chess_proxy', path='')