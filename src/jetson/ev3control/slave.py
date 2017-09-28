"""MQTT client that listens for commands from a master and turns them into Ev3 commands"""
from functools import partial

import paho.mqtt.client as mqtt
import ev3dev.ev3 as ev3
from ev3dev.ev3 import *
import IR.IR_control as remoteControl
from .messages import *
from Sensors.odometry import Odometry

MASTER_HOST = "localhost"


def dont_crash(func):
    """Stop-gap decorator for preventing the slave from crashing in cases of errors.

    TODO: replace exception printing with logging.
    """

    def robust(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e)
            return None

    return robust


def _payload_to_message(msg):
    return eval(msg.payload.decode())


@dont_crash
def print_property(objects, obj_name, attr_name):
    return getattr(objects[obj_name], attr_name, "Not set")


@dont_crash
def set_property(objects, obj_name, attr_name, val):
    setattr(objects[obj_name], attr_name, val)


@dont_crash
def run_method(objects, obj_name, method_name, args):
    return getattr(objects[obj_name], method_name)(**args)


def process_message(objects: dict, client, userdata, msg):
    """Callback for processing an MQTT message.

    Assumes the message payload can be evaluated to one of the message types
    defined in `messages` module.
    """
    #print("receiving message")
    message = _payload_to_message(msg)
    if isinstance(message, ShowAttrMessage):
        print(print_property(objects, *message))
    elif isinstance(message, SetAttrMessage):
        #print("Value before: ", print_property(objects, message.obj_name, message.attr_name))
        set_property(objects, *message)
        #print("Value after:", print_property(objects, message.obj_name, message.attr_name))
    elif isinstance(message, RunMethodMessage):
        #print('running method')
        run_method(objects, *message)
    elif isinstance(message, AddDeviceMessage):
        #print("adding object!")
        objects[message.obj_name] = eval(message.obj_init)
        #print("new objects", objects)
    else:
        print("not a valid message type!")


def run_slave(host=MASTER_HOST):
    """Convenience function for setting up an MQTT client and running its listening loop.

    :param host: can be an IP or hostname.
    """
    client = mqtt.Client()
    client.connect(host, 1883, keepalive=60)
    all_objects = {}
    client.on_message = partial(process_message, all_objects)
    client.subscribe("commands")
    print("Client is set up, gonna start listening now!")
    client.loop_forever()



