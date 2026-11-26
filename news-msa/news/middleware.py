from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

class OptionsMiddleware(MiddlewareMixin):
    """
    OPTIONS 요청을 처리하여 CORS preflight 요청에 대한 응답을 제공합니다.
    """
    
    def process_request(self, request):
        if request.method == 'OPTIONS':
            response = HttpResponse()
            response["Access-Control-Allow-Origin"] = "https://d18wspy7xouagh.cloudfront.net"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Max-Age"] = "86400"
            return response
        return None
