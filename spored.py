from flask import Flask, render_template
from datetime import datetime
from flask.ext.socketio import SocketIO, emit
from pymongo import MongoClient
import os

app = Flask(__name__)
socketio = SocketIO(app)

db = MongoClient(os.getenv('MONGOLAB_URI')).get_default_database()
entries = db.entries
descriptions = db.descriptions

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('epg', namespace='/epg')
def epg(msg):
    print "msg: %s" % msg
    try:
        from_time = int(msg['from'])/1000
        to_time = int(msg['to'])/1000
        query = {'from_time': {'$gt': from_time,
                               '$lt': to_time},
                 'channel': msg['channel']}
        print "query: %s" % query
        for entry in entries.find(query):
            del entry['_id']
            del entry['timestamp']
            print "reply: %s" % entry
            emit('channel', entry)
    except Exception as e:
        emit('error', e.message)

if __name__ == '__main__':
    socketio.run(app)
