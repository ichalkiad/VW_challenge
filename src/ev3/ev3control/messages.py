"""Defines the types of messages."""
from collections import namedtuple

ShowAttrMessage = namedtuple("ShowAttrMessage", "obj_name attr_name")

SetAttrMessage = namedtuple("SetAttrMessage", "obj_name attr_name value")

RunMethodMessage = namedtuple("RunMethodMessage", "obj_name method_name args")

AddDeviceMessage = namedtuple("AddDeviceMessage", "obj_name obj_init")
