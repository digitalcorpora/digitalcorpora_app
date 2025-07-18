#!/usr/bin/env python3
"""
Lambda handler for the DigitalCorpora Flask application.
This file serves as the entry point for AWS Lambda.
"""

import json
import os
import sys
from urllib.parse import urlparse

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from flask import request as flask_request
from digitalcorpora_app.main import app

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

    # Set up Flask request context
    with app.test_request_context(
        path=path,
        method=http_method,
        query_string=query_string,
        headers=headers,
        data=body
    ):
        try:
            # Call the Flask application
            response = app.full_dispatch_request()

            # Build API Gateway response
            api_response = {
                'statusCode': response.status_code,
                'headers': dict(response.headers),
                'body': response.get_data(as_text=True),
                'isBase64Encoded': False
            }

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