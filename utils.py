from flask import make_response

def add_no_cache_headers(response):
    """
    Add headers to prevent caching of sensitive pages.
    
    Args:
        response: Flask response object or string
        
    Returns:
        Response with no-cache headers
    """
    if not isinstance(response, str):
        return response
    
    resp = make_response(response)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp
