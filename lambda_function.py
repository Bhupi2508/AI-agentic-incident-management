def lambda_handler(event, context):
    path = event.get('rawPath', '/')

    if path == '/' or path == '/index':
        html_content = render_html('index.html')
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html'
            },
            'body': html_content
        }
    else:
        return {
            'statusCode': 404,
            'body': 'Page not found'
        }

def render_html(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()