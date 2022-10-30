"""

Application to Control Relay board using MQTT.

"""
import logging

import os
import eventlet
import json
from flask import Flask, render_template, request, redirect, url_for
from flask_mqtt import Mqtt
from flask_socketio import SocketIO, emit
from flask_bootstrap import Bootstrap
from flask_table import Table, Col, html, LinkCol
from flask_wtf.csrf import CSRFProtect
import json

eventlet.monkey_patch()
SECRET_KEY = os.urandom(32)

csrf = CSRFProtect()
app = Flask(__name__)
app.config['SECRET'] = 'my secret key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = '127.0.0.1'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_CLIENT_ID'] = 'flask_mqtt'
app.config['MQTT_CLEAN_SESSION'] = True
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False
app.config['MQTT_LAST_WILL_TOPIC'] = 'home/lastwill'
app.config['MQTT_LAST_WILL_MESSAGE'] = 'bye'
app.config['MQTT_LAST_WILL_QOS'] = 2
app.config['SECRET_KEY'] = SECRET_KEY #'secret!'

# Parameters for SSL enabled
# app.config['MQTT_BROKER_PORT'] = 8883
# app.config['MQTT_TLS_ENABLED'] = True
# app.config['MQTT_TLS_INSECURE'] = True
# app.config['MQTT_TLS_CA_CERTS'] = 'ca.crt'

csrf.init_app(app)
mqtt = Mqtt(app)
socketio = SocketIO(app)
bootstrap = Bootstrap(app)


relayconfig = {'value_ch0':False, 'value_ch1':False, 'value_ch2':False, 'value_ch3':False, 
                'value_ch4':False, 'value_ch5':False, 'value_ch6':False, 'value_ch7':False}

class RelayConfigItem(object):
    def __init__(self, uid, channels, relay0, relay1, relay2, relay3, relay4, relay5, relay6, relay7):
        self.id = uid
        self.channels = channels
        self.relay0 = relay0
        self.relay1 = relay1
        self.relay2 = relay2
        self.relay3 = relay3
        self.relay4 = relay4
        self.relay5 = relay5
        self.relay6 = relay6
        self.relay7 = relay7


class TableRelayConfig(Table):
    id = Col('Id', column_html_attrs={'class': 'id'},)
    channels = Col('Channels', column_html_attrs={'class': 'channels'},)
    relay0 = Col('Relay0', column_html_attrs={'class': 'relay0'},)
    relay1 = Col('Relay1', column_html_attrs={'class': 'relay1'},)
    relay2 = Col('Relay2', column_html_attrs={'class': 'relay2'},)
    relay3 = Col('Relay3', column_html_attrs={'class': 'relay3'},)
    relay4 = Col('Relay4', column_html_attrs={'class': 'relay4'},)
    relay5 = Col('Relay5', column_html_attrs={'class': 'relay5'},)
    relay6 = Col('Relay6', column_html_attrs={'class': 'relay6'},)
    relay7 = Col('Relay7', column_html_attrs={'class': 'relay7'},)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/relay', methods=['GET', 'POST'])
def relay():
    try:
        if request.method == 'POST':
            data = request.get_json()
            print("relay url POST got data: ", repr(data))
            channel = 'value_ch'+data['relaychan']
            if data['relayvalue'] == "Open":
                relayconfig[channel] = True
            elif data['relayvalue'] == "Close":
                relayconfig[channel] = False
            data = {}
            data['topic'] = 'relay'
            data['message'] = json.dumps(relayconfig)
            data['qos'] = 0
            mqtt.publish(data['topic'], data['message'], data['qos'])
            return '', 200
        else:
            items = []
            relay_channel_list = []
            for item in range(len(relayconfig)):
                relay_channel_list.append(item)
            is_table = True
            relayconf = RelayConfigItem(uid = 1,
                            channels=8, 
                            relay0 = 'Open' if relayconfig['value_ch0'] else 'Close',
                            relay1 = 'Open' if relayconfig['value_ch1'] else 'Close',
                            relay2 = 'Open' if relayconfig['value_ch2'] else 'Close',
                            relay3 = 'Open' if relayconfig['value_ch3'] else 'Close',
                            relay4 = 'Open' if relayconfig['value_ch4'] else 'Close',
                            relay5 = 'Open' if relayconfig['value_ch5'] else 'Close',
                            relay6 = 'Open' if relayconfig['value_ch6'] else 'Close',
                            relay7 = 'Open' if relayconfig['value_ch7'] else 'Close',
                            )
            items.append(relayconf)
            table = TableRelayConfig(items=items, table_id='relayconfig_id', classes=["table"]).__html__()
            return render_template('relay.html', table=table, is_table=is_table, channels=relay_channel_list)
    except:
        # raise
        return '', 404

@socketio.on('publish')
def handle_publish(json_str):
    data = json.loads(json_str)
    mqtt.publish(data['topic'], data['message'], data['qos'])


@socketio.on('subscribe')
def handle_subscribe(json_str):
    # print('json_str', repr(json_str))
    data = json.loads(json_str)
    mqtt.subscribe(data['topic'], data['qos'])


@socketio.on('unsubscribe_all')
def handle_unsubscribe_all():
    mqtt.unsubscribe_all()


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc == 0:
       print('Connected successfully')
       mqtt.subscribe('test')
    else:
       print('Bad connection. Code:', rc)


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode(),
        qos=message.qos,
    )
    print('received mqtt message', repr(data))
    socketio.emit('mqtt_message', data=data)


@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    # print(level, buf)
    pass


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=7000, use_reloader=False, debug=True)
