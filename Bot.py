import websocket
import time
import sys
import asyncio
import json
from pprint import pprint
import random
import threading
import argparse

TICKRATE = 1.0 / 10
WANTED_USERNAME = "ExamplePY" + str(random.randint(0, 10000))

try:
    import thread
except ImportError:
    import _thread as thread

# Command actually sent
basicCommand = {  # I like just having to copy the dict where needed
    "Type": "",
    "Command": ""
}

# MoveToPoint
moveToPoint = {
    "x": 0,
    "z": 0  # Note how this is Z and not Y
}

# MoveAngle
cmd_value = {
    "value": 0
}


class Bot:
    def __init__(self):
        self.state = "pregame"
        self.ws: websocket.WebSocketApp = None

        self.status = None  # The tick by tick status update
        self.map = None  #The map status given at the start of the map

    def connect(self):
        self.ws = websocket.WebSocketApp("ws://localhost:8888/server",
                                         on_message=on_message,
                                         on_error=on_error,
                                         on_close=on_close)

    def on_message(self, ws, message):
        print("CLASS on_message: ", ws, message)
        self.evaluate(message)

    def on_error(self, ws, error):
        print("CLASS on_error: ", ws, error)

    def on_close(self, ws):
        print("CLASS on_close: WS Closed", ws)
        exit(1)

    def evaluate(self, message):
        command = json.loads(message)

        if command["Type"] == "username":
            self.set_username()

        if command["Type"] == "fullMap":
            cmd = json.loads(command["Command"])
            self.map = cmd

        if command["Type"] == "playerStatus":
            cmd = json.loads(command["Command"])
            self.status = cmd

    def set_username(self):
        command = basicCommand.copy()
        command["Type"] = "Username"
        command["Command"] = WANTED_USERNAME
        self.send_command(command)

    def send_command(self, basic_command: dict):
        string = json.dumps(basic_command)
        print(string)
        self.ws.send(string)

    # noinspection PyTypeChecker
    def moveToPoint(self, x, z):
        cmd = basicCommand.copy()
        moveToPoint_cmd = moveToPoint.copy()
        moveToPoint_cmd["x"] = x
        moveToPoint_cmd["z"] = z

        cmd["Type"] = "moveToPoint"
        cmd["Command"] = json.dumps(moveToPoint_cmd.copy())
        string = json.dumps(cmd)
        self.ws.send(string)

    def thrust(self, time_sec):
        cmd = basicCommand.copy()
        thrust_cmd = cmd_value.copy()
        thrust_cmd["value"] = time_sec

        cmd["Type"] = "thrust"
        cmd["Command"] = json.dumps(thrust_cmd)
        string = json.dumps(cmd)
        self.ws.send(string)

    def moveToAngle(self, angle):
        cmd = basicCommand.copy()
        moveToAngle_cmd = cmd_value.copy()
        moveToAngle_cmd["value"] = angle

        cmd["Type"] = "turnAngle"
        cmd["Command"] = json.dumps(moveToAngle_cmd)
        string = json.dumps(cmd)
        self.ws.send(string)

    def moveToAngleRelative(self, angle):
        cmd = basicCommand.copy()
        moveToAngle_cmd = cmd_value.copy()
        moveToAngle_cmd["value"] = angle

        cmd["Type"] = "turnAngleRelative"
        cmd["Command"] = json.dumps(moveToAngle_cmd)
        string = json.dumps(cmd)
        self.ws.send(string)

    # MODE: Just gun it for the middle of the points. Yolo
    def dumb_game_control_loop_point_move(self):
        print("dumb_game_control_loop_point_move")
        while True:
            time.sleep(TICKRATE)
            if self.status is None or self.map is None:
                continue
            checkpoint_pos = self.status["checkpoint_next_pos"]
            x = checkpoint_pos["x"]
            z = checkpoint_pos["z"]
            self.moveToPoint(x, z)

    # MODE: Just ugn it for the middle of the point, but manually
    # so that you guys can look at the trig involved
    def dumb_game_control_loop_manual_move(self):
        print("dumb_game_control_loop_manual_move")
        while True:
            time.sleep(TICKRATE)
            if self.status is None or self.map is None:
                continue

            status = self.status
            map = self.map

    def test_angle(self):
        print("test_angle")
        angle = 0
        while True:
            time.sleep(TICKRATE)
            if self.status is None or self.map is None:
                continue

            angle = (angle + 45) % 360
            self.moveToAngle(angle)
            time.sleep(2)

    def test_angle_adv(self):
        print("test_angle_adv")
        angle = 0
        while True:
            time.sleep(TICKRATE)
            if self.status is None or self.map is None:
                continue

            self.moveToAngle(0)
            time.sleep(3)
            self.moveToAngleRelative(angle)
            angle = angle + 45
            time.sleep(3)

    def test_thrust(self):
        print("test_thrust")
        while True:
            time.sleep(TICKRATE)
            if self.status is None or self.map is None:
                continue

            timeBurst = 0.5  # 0.2 sec
            self.thrust(timeBurst)
            time.sleep(2)

    def test_drive(self):
        print("test_drive")
        while True:
            time.sleep(TICKRATE)
            if self.status is None or self.map is None:
                continue

            timeBurst = 0.5  # 0.2 sec
            self.thrust(timeBurst)
            time.sleep(2)
            self.moveToAngleRelative(90)
            time.sleep(2)

def on_message(ws, message):
    bot.on_message(ws, message)


def on_error(ws, error):
    print(error)
    bot.on_error(ws, error)


def on_close(ws):
    print("WS Closed")
    bot.on_close(ws)


if __name__ == '__main__':
    websocket.enableTrace(True)
    bot = Bot()
    bot.connect()

    mode_mapping = {
        "dumb_point": bot.dumb_game_control_loop_point_move,
        "dumb_manual": bot.dumb_game_control_loop_manual_move,
        "test_angle": bot.test_angle,
        "test_thrust": bot.test_thrust,
        "test_angle_adv": bot.test_angle_adv,
        "test_drive": bot.test_drive,
    }

    parser = argparse.ArgumentParser(description='Lets get down to fun town.')
    parser.add_argument('--mode', dest='modus', default="dumb_point")
    args = parser.parse_args()
    print(args.modus)

    gameloop = mode_mapping.get(args.modus)
    if gameloop is None:
        exit(1)

    control_loop = threading.Thread(target=gameloop)
    control_loop.start()
    bot.ws.run_forever()
    exit(1)
