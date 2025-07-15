#!/usr/bin/env python3
"""
Lambda handler for the DigitalCorpora application.
This file serves as the entry point for AWS Lambda.
"""

import json
import os
import sys
from urllib.parse import urlparse

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bottle
from bottle import request, response

# Import your application
from app_wsgi import app

def lambda_handler(event, context):
    """
    AWS Lambda handler function.

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """

    # Parse the API Gateway event
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    query_string = event.get('queryStringParameters', {}) or {}
    headers = event.get('headers', {}) or {}
    body = event.get('body', '')

    # Set up Bottle request
    request.environ = {
        'REQUEST_METHOD': http_method,
        'PATH_INFO': path,
        'QUERY_STRING': '&'.join([f"{k}={v}" for k, v in query_string.items()]),
        'HTTP_HOST': headers.get('Host', 'localhost'),
        'HTTP_USER_AGENT': headers.get('User-Agent', ''),
        'HTTP_ACCEPT': headers.get('Accept', '*/*'),
        'HTTP_ACCEPT_ENCODING': headers.get('Accept-Encoding', ''),
        'HTTP_ACCEPT_LANGUAGE': headers.get('Accept-Language', ''),
        'HTTP_CONNECTION': headers.get('Connection', 'close'),
        'HTTP_REFERER': headers.get('Referer', ''),
        'HTTP_X_FORWARDED_FOR': headers.get('X-Forwarded-For', ''),
        'HTTP_X_FORWARDED_PROTO': headers.get('X-Forwarded-Proto', 'https'),
        'HTTP_X_FORWARDED_PORT': headers.get('X-Forwarded-Port', '443'),
        'wsgi.input': type('obj', (object,), {
            'read': lambda: body.encode('utf-8') if isinstance(body, str) else body
        })(),
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': True,
    }

    # Set up response
    response.status = 200
    response.headers = {}

    try:
        # Call the Bottle application
        result = app(request.environ, lambda status, headers: None)

        # Get the response content
        if hasattr(result, '__iter__'):
            content = b''.join(result)
        else:
            content = str(result).encode('utf-8')

        # Build API Gateway response
        api_response = {
            'statusCode': response.status,
            'headers': {
                'Content-Type': response.headers.get('Content-Type', 'text/html'),
                'Cache-Control': response.headers.get('Cache-Control', 'no-cache'),
            },
            'body': content.decode('utf-8') if isinstance(content, bytes) else str(content),
            'isBase64Encoded': False
        }

        # Add any additional headers from Bottle response
        for key, value in response.headers.items():
            if key.lower() not in ['content-type', 'cache-control']:
                api_response['headers'][key] = value

        return api_response

    except Exception as e:
        # Handle errors
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'text/plain',
            },
            'body': f'Internal Server Error: {str(e)}',
            'isBase64Encoded': False
        }