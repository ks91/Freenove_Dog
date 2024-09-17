# -*- coding: utf-8 -*-
"""
Licensed under CC BY-NC-SA 3.0

Derived from Freenove by Kenji Saito (ks91), 2024.

A version of Main.py that takes input from REST API instead of
GUI events. It is assumed that the robot has been calibrated using
the original Main.py client software.
"""

from flask import Flask, request, jsonify, g, send_file
from Client import *
import threading
import time


DEFAULT_MOVE_SPEED = '8'

FILENAME_IMAGE = 'image.jpg'

PORT_INSTRUCTIONS = 5001
PORT_VIDEO = 8001


class ClientService:
    def __init__(self):
        self.client = Client()
        self.client.move_speed = DEFAULT_MOVE_SPEED
        
        try:
            with open('IP.txt', 'r') as file:
                self.ip_address = file.readline().strip()

        except FileNotFoundError:
            self.ip_address = '127.0.0.1'
            
        self.video_thread = None
        self.video_timer_thread = None
        self.instruction_thread = None
        self.connected = False
        self.distance = '0cm'


    # Function to receive instructions from the server
    def receive_instruction(self):
        try:
            self.client.client_socket1.connect((self.ip_address, PORT_INSTRUCTIONS))
            self.client.tcp_flag = True
            print("Connection Successful!")
            
        except Exception as e:
            print("Failed to connect to server:", e)
            self.client.tcp_flag = False
            return

        while self.client.tcp_flag:
            try:
                alldata = self.client.receive_data()
                if alldata == '':
                    break
                else:
                    cmdArray = alldata.strip().split('\n')
                for oneCmd in cmdArray:
                    data = oneCmd.split("#")
                    if data[0] == cmd.CMD_SONIC:
                        # Handle sonic data
                        self.distance = data[1] + 'cm'
                    elif data[0] == cmd.CMD_POWER:
                        if data[1]:
                            self.power = round((float(data[1]) - 7.00) / 1.40 * 100)
                    elif data[0] == cmd.CMD_RELAX:
                        if data[1] == "0":
                            self.relax = False
                        else:
                            self.relax = True

            except Exception as e:
                print("Error receiving data:", e)
                client.tcp_flag = False
                break


    # Function to stand the robot
    def stand(self):
        command = cmd.CMD_ATTITUDE + '#0#0#0\n'
        self.client.send_data(command)
        time.sleep(0.1)
        command = cmd.CMD_HORIZON + '#0\n'
        self.client.send_data(command)
        time.sleep(0.1)
        command = cmd.CMD_HEIGHT + '#0\n'
        self.client.send_data(command)
        time.sleep(0.1)


    # Function to enable image input periodically
    def refresh_image(self):
        while self.connected:
            if self.client.video_flag == False:
                self.client.video_flag = True
            time.sleep(0.1)


def abort_by_bad_content_type(content_type):
    abort(400, description='Content-Type {0} is not expected'.format(
            content_type))


def abort_by_bad_json_format():
    abort(400, description='Bad JSON format')


def abort_by_missing_param(param):
    abort(400, description='{0} is missing'.format(param))


app = Flask(__name__)
service = ClientService()


@app.after_request
def after_request(response):
    return response


@app.before_request
def before_request():
    global service
    g.service = service


# Endpoint to connect/disconnect
@app.route('/connect', methods=['POST'])
def connect_robot():
    if not g.service.connected:
        g.service.client.turn_on_client(g.service.ip_address)
        g.service.connected = True

        # Start video and instruction threads
        g.service.video_thread = threading.Thread(
                target=g.service.client.receiving_video,
                args=(g.service.ip_address,))
        g.service.video_timer_thread = threading.Thread(
                target=g.service.refresh_image)
        g.service.instruction_thread = threading.Thread(
                target=g.service.receive_instruction)
        g.service.video_thread.start()
        g.service.video_timer_thread.start()
        g.service.instruction_thread.start()

        return jsonify({'status': 'Connected'}), 200


# Endpoint to disconnect
@app.route('/disconnect', methods=['POST'])
def disconnect_robot():
    if g.service.connected:
        try:
            g.service.client.client_socket1.close()
            g.service.client.tcp_flag = False

        except Exception as e:
            print("Error disconnecting:", e)

        g.service.connected = False
        g.service.client.turn_off_client()

        return jsonify({'status': 'Disconnected'}), 200


# Endpoint to move forward
@app.route('/move/forward', methods=['POST'])
def move_forward():
    speed = g.service.client.move_speed
    g.service.stand()
    command = cmd.CMD_MOVE_FORWARD + "#" + speed + '\n'
    g.service.client.send_data(command)
    return jsonify({'status': 'Moving forward', 'speed': int(speed)}), 200


# Endpoint to move backward
@app.route('/move/backward', methods=['POST'])
def move_backward():
    speed = g.service.client.move_speed
    g.service.stand()
    command = cmd.CMD_MOVE_BACKWARD + "#" + speed + '\n'
    g.service.client.send_data(command)
    return jsonify({'status': 'Moving backward', 'speed': int(speed)}), 200


# Endpoint to move left
@app.route('/move/left', methods=['POST'])
def move_left():
    speed = g.service.client.move_speed
    g.service.stand()
    command = cmd.CMD_MOVE_LEFT + "#" + speed + '\n'
    g.service.client.send_data(command)
    return jsonify({'status': 'Moving left', 'speed': int(speed)}), 200


# Endpoint to move right
@app.route('/move/right', methods=['POST'])
def move_right():
    speed = g.service.client.move_speed
    g.service.stand()
    command = cmd.CMD_MOVE_RIGHT + "#" + speed + '\n'
    g.service.client.send_data(command)
    return jsonify({'status': 'Moving right', 'speed': int(speed)}), 200


# Endpoint to turn left
@app.route('/turn/left', methods=['POST'])
def turn_left():
    speed = g.service.client.move_speed
    g.service.stand()
    command = cmd.CMD_TURN_LEFT + "#" + speed + '\n'
    g.service.client.send_data(command)
    return jsonify({'status': 'Turning left', 'speed': int(speed)}), 200


# Endpoint to turn right
@app.route('/turn/right', methods=['POST'])
def turn_right():
    speed = g.service.client.move_speed
    g.service.stand()
    command = cmd.CMD_TURN_RIGHT + "#" + speed + '\n'
    g.service.client.send_data(command)
    return jsonify({'status': 'Turning right', 'speed': int(speed)}), 200


# Endpoint to stop
@app.route('/move/stop', methods=['POST'])
def move_stop():
    speed = g.service.client.move_speed
    command = cmd.CMD_MOVE_STOP + "#" + speed + '\n'
    g.service.client.send_data(command)
    return jsonify({'status': 'Stopped', 'speed': int(speed)}), 200


# Endpoint to adjust speed (2 <= speed <= 10; 8 by default)
@app.route('/speed', methods=['POST'])
@app.route('/speed/<string:value>', methods=['POST'])
def adjust_speed(value=None):
    if value is None:
        value = DEFAULT_MOVE_SPEED
    g.service.client.move_speed = value
    return jsonify({'status': 'Speed set', 'speed': int(value)}), 200


# Endpoint to get the speed
@app.route('/speed', methods=['GET'])
def get_speed():
    return jsonify({'speed': int(g.service.client.move_speed)}), 200


# Endpoint for relax
@app.route('/relax', methods=['POST'])
def relax():
    command = cmd.CMD_RELAX + '\n'
    g.service.client.send_data(command)
    return jsonify({'status': 'Relaxed'}), 200


# Endpoint for stand
@app.route('/stand', methods=['POST'])
def stand_up():
    g.service.stand()
    return jsonify({'status': 'Standing'}), 200


# Endpoint for buzzer (state : '1' to turn on, '0' to turn off)
@app.route('/buzzer', methods=['POST'])
@app.route('/buzzer/<string:state>', methods=['POST'])
def buzzer(state=None):
    if state is None:
        state = '0'
    command = cmd.CMD_BUZZER + '#' + state + '\n'
    g.service.client.send_data(command)
    return jsonify({'status': 'Buzzer state changed', 'state': state}), 200


# Endpoint for balance (state : '1' to enable, '0' to disable)
@app.route('/balance', methods=['POST'])
@app.route('/balance/<string:state>', methods=['POST'])
def balance(state=None):
    if state is None:
        state = '0'
    command = cmd.CMD_BALANCE + '#' + state + '\n'
    g.service.client.send_data(command)
    return jsonify({'status': 'Balance state changed', 'state': state}), 200


# Endpoint for sonic
@app.route('/sonic', methods=['GET'])
def sonic():
    command = cmd.CMD_SONIC + '\n'
    g.service.client.send_data(command)
    time.sleep(0.1)
    distance = g.service.distance
    return jsonify({'status': 'Sonic data requested', 'distance': distance}), 200


# Endpoint for power
@app.route('/power', methods=['GET'])
def power():
    command = cmd.CMD_POWER + '\n'
    g.service.client.send_data(command)
    time.sleep(0.1)
    power = g.service.power
    relax = g.service.relax
    return jsonify({
        'status': 'Power data requested',
        'power': power,
        'need-to-relax': relax
    }), 200


# Endpoint to set height (-20 <= value <= 20; 0 by default)
@app.route('/height', methods=['POST'])
@app.route('/height/<string:value>', methods=['POST'])
def set_height(value=None):
    if value is None:
        value = '0'
    command = cmd.CMD_HEIGHT + '#' + value + '\n'
    g.service.client.send_data(command)
    return jsonify({'status': 'Height set', 'value': int(value)}), 200


# Endpoint to set horizon (-20 <= value <= 20; 0 by default)
@app.route('/horizon', methods=['POST'])
@app.route('/horizon/<string:value>', methods=['POST'])
def set_horizon(value=None):
    if value is None:
        value = '0'
    command = cmd.CMD_HORIZON + '#' + value + '\n'
    g.service.client.send_data(command)
    return jsonify({'status': 'Horizon set', 'value': int(value)}), 200


# Endpoint to set head angle (50 <= angle <= 180; 90 by default)
@app.route('/head', methods=['POST'])
@app.route('/head/<string:angle>', methods=['POST'])
def set_head(angle=None):
    if angle is None:
        angle = '90'
    command = cmd.CMD_HEAD + '#' + angle + '\n'
    g.service.client.send_data(command)
    return jsonify({'status': 'Head angle set', 'angle': int(angle)}), 200


# Endpoint to set attitude (-20 <= values <= 20; 0 by default)
@app.route('/attitude', methods=['POST'])
@app.route('/attitude/<string:roll>/<string:pitch>/<string:yaw>', methods=['POST'])
def set_attitude(roll=None, pitch=None, yaw=None):
    if roll is None:
        roll = '0'
        pitch = '0'
        yaw = '0'
    command = cmd.CMD_ATTITUDE + '#' + roll + '#' + pitch + '#' + yaw + '\n'
    g.service.client.send_data(command)
    return jsonify({
        'status': 'Attitude set',
        'roll': int(roll),
        'pitch': int(pitch),
        'yaw': int(yaw)
    }), 200


# Endpoint to set LED mode (0 : off, 1 to 5)
@app.route('/led/mode', methods=['POST'])
@app.route('/led/mode/<string:value>', methods=['POST'])
def set_led_mode(value=None):
    if value is None:
        value = '0'
    command = cmd.CMD_LED_MOD + '#' + value + '\n'
    g.service.client.send_data(command)
    return jsonify({'status': 'LED mode set', 'mode': int(value)}), 200


# Endpoint to set LED color
@app.route('/led/color', methods=['POST'])
@app.route('/led/color/<string:red>/<string:green>/<string:blue>', methods=['POST'])
def set_led_color(red=None, green=None, blue=None):
    if red is None:
        red = '255'
        green = '255'
        blue = '255'
    command = cmd.CMD_LED + '#' + '255' + '#' + red + '#' + green + '#' + blue + '\n'
    g.service.client.send_data(command)
    return jsonify({
        'status': 'LED color set',
        'r': int(red),
        'g': int(green),
        'b': int(blue)
    }), 200


# Endpoint to get image from camera
@app.route('/camera/image', methods=['GET'])
def get_image():
    cv2.imwrite(FILENAME_IMAGE, g.service.client.image)
    return send_file(FILENAME_IMAGE, mimetype='image/jpeg')


# Endpoint to set camera usage mode (either 'video' or 'ball'; 'video' by default)
@app.route('/camera/mode', methods=['POST'])
@app.route('/camera/mode/<string:value>', methods=['POST'])
def set_image_mode(value=None):
    if value is None or value == 'video':
        g.service.client.ball_flag = False

    elif value == 'ball':
        g.service.client.ball_flag = True

    return jsonify({'status': 'Camera mode set', 'mode': value})


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(409)
def error_handler(e):
    return jsonify({'error': {
        'code': e.code,
        'name': e.name,
        'description': e.description,
    }}), e.code

@app.errorhandler(ValueError)
@app.errorhandler(KeyError)
def error_handler(e):
    return jsonify({'error': {
        'code': 400,
        'name': 'Bad Request',
        'description': str(e),
    }}), 400


# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)


# end of Main2.py
