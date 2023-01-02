"""
Support for controlling a Cambridge Audio CXA amplifier over a serial connection.

For more details about this platform, please refer to the documentation at
https://github.com/lievencoghe/cambridge_audio_cxa
"""

import logging
import urllib.request
import voluptuous as vol
from serial import Serial

from homeassistant.components.media_player import MediaPlayerEntity, PLATFORM_SCHEMA

from homeassistant.components.media_player.const import (
    SUPPORT_SELECT_SOURCE,
    SUPPORT_SELECT_SOUND_MODE,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_STEP,
)

from homeassistant.const import (
    CONF_DEVICE,
    CONF_NAME,
    CONF_SLAVE,
    CONF_TYPE,
    STATE_OFF,
    STATE_ON,
)

import homeassistant.helpers.config_validation as cv

import homeassistant.loader as loader

__version__ = "0.4"

_LOGGER = logging.getLogger(__name__)


SUPPORT_CXA = (
    SUPPORT_SELECT_SOURCE
    | SUPPORT_SELECT_SOUND_MODE
    | SUPPORT_TURN_OFF
    | SUPPORT_TURN_ON
    | SUPPORT_VOLUME_MUTE
)

SUPPORT_CXA_WITH_CXN = (
    SUPPORT_SELECT_SOURCE
    | SUPPORT_SELECT_SOUND_MODE
    | SUPPORT_TURN_OFF
    | SUPPORT_TURN_ON
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_VOLUME_STEP
)

DEFAULT_NAME = "Cambridge Audio CXA"
DEVICE_CLASS = "receiver"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE): cv.string,
        vol.Required(CONF_TYPE): cv.string,      
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_SLAVE): cv.string,
    }
)

NORMAL_INPUTS_CXA61 = {
    "A1" : "#03,04,00",
    "A2" : "#03,04,01",
    "A3" : "#03,04,02",
    "A4" : "#03,04,03",
    "D1" : "#03,04,04",
    "D2" : "#03,04,05",
    "D3" : "#03,04,06",
    "Bluetooth" : "#03,04,14",
    "USB" : "#03,04,16",
    "MP3" : "#03,04,10"
}

NORMAL_INPUTS_CXA81 = {
    "A1" : "#03,04,00",
    "A2" : "#03,04,01",
    "A3" : "#03,04,02",
    "A4" : "#03,04,03",
    "D1" : "#03,04,04",
    "D2" : "#03,04,05",
    "D3" : "#03,04,06",
    "Bluetooth" : "#03,04,14",
    "USB" : "#03,04,16",
    "XLR" : "#03,04,20"
}

NORMAL_INPUTS_AMP_REPLY_CXA61 = {
    "#04,01,00" : "A1",
    "#04,01,01" : "A2",
    "#04,01,02" : "A3",
    "#04,01,03" : "A4",
    "#04,01,04" : "D1",
    "#04,01,05" : "D2",
    "#04,01,06" : "D3",
    "#04,01,14" : "Bluetooth",
    "#04,01,16" : "USB",
    "#04,01,10" : "MP3"
}

NORMAL_INPUTS_AMP_REPLY_CXA81 = {
    "#04,01,00" : "A1",
    "#04,01,01" : "A2",
    "#04,01,02" : "A3",
    "#04,01,03" : "A4",
    "#04,01,04" : "D1",
    "#04,01,05" : "D2",
    "#04,01,06" : "D3",
    "#04,01,14" : "Bluetooth",
    "#04,01,16" : "USB",
    "#04,01,20" : "XLR"
}

SOUND_MODES = {
    "A" : "#1,25,0",
    "AB" : "#1,25,1",
    "B" : "#1,25,2"
}

AMP_CMD_GET_PWSTATE = "#01,01"
AMP_CMD_GET_CURRENT_SOURCE = "#03,01"
AMP_CMD_GET_MUTE_STATE = "#01,03"

AMP_CMD_SET_MUTE_ON = "#01,04,1"
AMP_CMD_SET_MUTE_OFF = "#01,04,0"
AMP_CMD_SET_PWR_ON = "#01,02,1"
AMP_CMD_SET_PWR_OFF = "#01,02,0"

AMP_REPLY_PWR_ON = "#02,01,1"
AMP_REPLY_PWR_STANDBY = "#02,01,0"
AMP_REPLY_MUTE_ON = "#02,03,1"
AMP_REPLY_MUTE_OFF = "#02,03,0"

def setup_platform(hass, config, add_devices, discovery_info=None):
    device = config.get(CONF_DEVICE)
    name = config.get(CONF_NAME)
    cxatype = config.get(CONF_TYPE)
    cxnhost = config.get(CONF_SLAVE)

    if device is None:
        _LOGGER.error("No serial port defined in configuration.yaml for Cambridge CXA")
        return

    if cxatype is None:
        _LOGGER.error("No CXA type found in configuration.yaml file. Possible values are CXA61, CXA81")
        return

    add_devices([CambridgeCXADevice(hass, device, name, cxatype, cxnhost)])


class CambridgeCXADevice(MediaPlayerEntity):
    def __init__(self, hass, device, name, cxatype, cxnhost):
        _LOGGER.info("Setting up Cambridge CXA")
        self._hass = hass
        self._device = device
        self._mediasource = "#04,01,00"
        self._speakersactive = ""
        self._muted = AMP_REPLY_MUTE_OFF
        self._name = name
        self._pwstate = ""
        self._cxatype = cxatype.upper()
        if self._cxatype == "CXA61":
            self._source_list = NORMAL_INPUTS_CXA61.copy()
            self._source_reply_list = NORMAL_INPUTS_AMP_REPLY_CXA61.copy()
        else:
            self._source_list = NORMAL_INPUTS_CXA81.copy()
            self._source_reply_list = NORMAL_INPUTS_AMP_REPLY_CXA81.copy()
        self._sound_mode_list = SOUND_MODES.copy()
        self._state = STATE_OFF
        self._cxnhost = cxnhost
        self._serial = Serial(device, baudrate=9600, timeout=0.5, bytesize=8, parity="N", stopbits=1)
        
    def update(self):
        self._pwstate = self._command_with_reply(AMP_CMD_GET_PWSTATE)
        self._mediasource = self._command_with_reply(AMP_CMD_GET_CURRENT_SOURCE)
        self._muted = self._command_with_reply(AMP_CMD_GET_MUTE_STATE)

    def _command(self, command):
        try:
            self._serial.flush()
            self._serial.write((command+"\r").encode("utf-8"))
            self._serial.flush()
        except:
            _LOGGER.error("Could not send command")
    
    def _command_with_reply(self, command):
        try:
            self._serial.write((command+"\r").encode("utf-8"))
            reply = self._serial.readline()
            return(reply.decode("utf-8")).replace("\r","")
        except:
            _LOGGER.error("Could not send command")
            return ""

    def url_command(self, command):
        urllib.request.urlopen("http://" + self._cxnhost + "/" + command).read()

    @property
    def is_volume_muted(self):
        if AMP_REPLY_MUTE_ON in self._muted:
            return True
        else:
            return False

    @property
    def name(self):
        return self._name

    @property
    def source(self):
        return self._source_reply_list[self._mediasource]

    @property
    def sound_mode_list(self):
        return sorted(list(self._sound_mode_list.keys()))

    @property
    def source_list(self):
        return sorted(list(self._source_list.keys()))

    @property
    def state(self):
        if AMP_REPLY_PWR_ON in self._pwstate:
            return STATE_ON
        else:
            return STATE_OFF

    @property
    def supported_features(self):
        if self._cxnhost:
            return SUPPORT_CXA_WITH_CXN
        return SUPPORT_CXA

    def mute_volume(self, mute):
        if mute:
            self._command(AMP_CMD_SET_MUTE_ON)
        else:
            self._command(AMP_CMD_SET_MUTE_OFF)

    def select_sound_mode(self, sound_mode):
        self._command(self._sound_mode_list[sound_mode])

    def select_source(self, source):
        self._command(self._source_list[source])

    def turn_on(self):
        self._command(AMP_CMD_SET_PWR_ON)

    def turn_off(self):
        self._command(AMP_CMD_SET_PWR_OFF)

    def volume_up(self):
        self.url_command("smoip/zone/state?pre_amp_mode=false")
        self.url_command("smoip/zone/state?volume_step_change=+1")
        self.url_command("smoip/zone/state?pre_amp_mode=true")

    def volume_down(self):
        self.url_command("smoip/zone/state?pre_amp_mode=false")
        self.url_command("smoip/zone/state?volume_step_change=-1")
        self.url_command("smoip/zone/state?pre_amp_mode=true")
