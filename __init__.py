from flask import Blueprint, json, request, render_template
from pymongo import MongoClient
from datetime import datetime

webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['webhook']
collection = db['requests']

@webhook.route('/receiver', methods=["POST"])
def receiver():
    payload = request.json
    event_type = request.headers.get('X-GitHub-Event')
    data = {
        'request_id': payload['id'],
        'author': payload['sender']['login'],
        'action': event_type,
        'from_branch': payload['pull_request']['head']['ref'] if event_type == 'pull_request' else '',
        'to_branch': payload['pull_request']['base']['ref'] if event_type == 'pull_request' else payload['ref'].split('/')[-1],
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    collection.insert_one(data)
    return {}, 200

@webhook.route('/ui', methods=["GET"])
def ui():
    requests = list(collection.find().sort('timestamp', -1).limit(10))
    formatted_requests = []
    for req in requests:
        if req['action'] == 'push':
            message = f"{req['author']} pushed to {req['to_branch']} on {req['timestamp']}"
        elif req['action'] == 'pull_request':
            message = f"{req['author']} submitted a pull request from {req['from_branch']} to {req['to_branch']} on {req['timestamp']}"
        elif req['action'] == 'merge':
            message = f"{req['author']} merged branch {req['from_branch']} to {req['to_branch']} on {req['timestamp']}"
        formatted_requests.append(message)
    return render_template('index.html', requests=formatted_requests)