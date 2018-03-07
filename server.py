# -*-: coding utf-8 -*-
""" Snips core server. """

import json
import time
import re
import logging
import sys
import argparse

from socket import error as socket_error

import paho.mqtt.client as mqtt

from thread_handler import ThreadHandler
from state_handler import StateHandler, State

MQTT_TOPIC_NLU = "hermes/nlu/"
MQTT_TOPIC_HOTWORD = "hermes/hotword/"
MQTT_TOPIC_ASR = "hermes/asr/"
MQTT_TOPIC_INTENT = "hermes/intent/"
MQTT_TOPIC_TTS = "hermes/tts/"

MQTT_TOPIC_HOTWORD_DETECTED_RE = re.compile("^hermes\/hotword(\/[a-zA-Z0-9]+)*\/detected$")


class Server():
    """ Snips core server. """
    DIALOGUE_EVENT_STARTED, DIALOGUE_EVENT_ENDED, DIALOGUE_EVENT_QUEUED = range(3)

    def __init__(self,
                 mqtt_hostname,
                 mqtt_port,
                 logger=None):
        """ Initialisation.

        :param config: a YAML configuration.
        :param assistant: the client assistant class, holding the
                          intent handler and intents registry.
        """
        self.logger = logger
        self.thread_handler = ThreadHandler()
        self.state_handler = StateHandler(self.thread_handler, logger)

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.mqtt_hostname = mqtt_hostname
        self.mqtt_port = mqtt_port

        self.first_hotword_detected = False

    def start(self):
        """ Start the MQTT client. """
        self.thread_handler.run(target=self.start_blocking)
        self.thread_handler.start_run_loop(self.logger)

    def start_blocking(self, run_event):
        """ Start the MQTT client, as a blocking method.

        :param run_event: a run event object provided by the thread handler.
        """

        self.log_info("Connecting to {} on port {}".format(self.mqtt_hostname, str(self.mqtt_port)))

        retry = 0
        while True and run_event.is_set():
            try:
                self.log_info("Trying to connect to {}".format(self.mqtt_hostname))
                self.client.connect(self.mqtt_hostname, self.mqtt_port, 60)
                break
            except (socket_error, Exception) as e:
                self.log_info("MQTT error {}".format(e))
                time.sleep(5 + int(retry / 5))
                retry = retry + 1

        topics = [
            (MQTT_TOPIC_INTENT + '#', 0),
            (MQTT_TOPIC_HOTWORD + '#', 0),
            (MQTT_TOPIC_ASR + '#', 0),
            (MQTT_TOPIC_TTS + '#', 0),
            (MQTT_TOPIC_NLU + '#', 0)
        ]
        self.log_info("Subscribing to topics {}".format(topics))
        self.client.subscribe(topics)

        self.state_handler.set_state(State.hotword_toggle_on)

        while run_event.is_set():
            try:
                self.client.loop()
            except AttributeError as e:
                self.log_info("Error in mqtt run loop {}".format(e))
                time.sleep(1)

    # pylint: disable=unused-argument,no-self-use
    def on_connect(self, client, userdata, flags, result_code):
        """ Callback when the MQTT client is connected.

        :param client: the client being connected.
        :param userdata: unused.
        :param flags: unused.
        :param result_code: result code.
        """
        self.log_info("Connected with result code {}".format(result_code))
        self.state_handler.set_state(State.welcome)

    # pylint: disable=unused-argument
    def on_disconnect(self, client, userdata, result_code):
        """ Callback when the MQTT client is disconnected. In this case,
            the server waits five seconds before trying to reconnected.

        :param client: the client being disconnected.
        :param userdata: unused.
        :param result_code: result code.
        """
        self.log_info("Disconnected with result code " + str(result_code))
        self.state_handler.set_state(State.goodbye)
        time.sleep(5)
        self.thread_handler.run(target=self.start_blocking)

    # pylint: disable=unused-argument
    def on_message(self, client, userdata, msg):
        """ Callback when the MQTT client received a new message.

        :param client: the MQTT client.
        :param userdata: unused.
        :param msg: the MQTT message.
        """
        if msg is None:
            return

        self.log_info("New message on topic {}".format(msg.topic))
        self.log_debug("Payload {}".format(msg.payload))

        if msg.payload is None or len(msg.payload) == 0:
            pass

        """
        if msg.payload:
            payload = json.loads(msg.payload.decode('utf-8'))
            site_id = payload.get('siteId')
            session_id = payload.get('sessionId')
        """

        if msg.topic is not None and msg.topic == MQTT_TOPIC_NLU + "intentParsed":
            self.state_handler.set_state(State.nlu_intent_parsed)
        elif msg.topic is not None and msg.topic == MQTT_TOPIC_HOTWORD + "toggleOn":
            self.state_handler.set_state(State.hotword_toggle_on)
        elif MQTT_TOPIC_HOTWORD_DETECTED_RE.match(msg.topic):
            if not self.first_hotword_detected:
                self.client.publish(
                    "hermes/feedback/sound/toggleOff", payload=None, qos=0, retain=False)
                self.first_hotword_detected = True
            self.state_handler.set_state(State.hotword_detected)
        elif msg.topic is not None and msg.topic == MQTT_TOPIC_NLU + "intentNotRecognized":
            self.state_handler.set_state(State.error)
        elif msg.topic is not None and msg.topic.startswith(MQTT_TOPIC_TTS):
            self.state_handler.set_state(State.say)

        self.log_debug("Switching state handler to {}".format(self.state_handler.state))

    def log_info(self, message):
        if self.logger is not None:
            self.logger.info(message)

    def log_debug(self, message):
        if self.logger is not None:
            self.logger.debug(message)

    def log_error(self, message):
        if self.logger is not None:
            self.logger.error(message)

def main_start():
    # define logging parameters
    logger = logging.getLogger(__name__)
    print (logger)
    handler = logging.StreamHandler()
    log_format = '\033[2m%(asctime)s\033[0m [%(levelname)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(log_format, date_format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # start the handler
    led_handler = Server("localhost", 1883, logger = logger)
    led_handler.start()


def main_try(state_to_try=None):
    if state_to_try is None:
        parser.print_usage()
        return
    else:
        print("Sorry, not yet implemented !")

def main_list():
    
    for state in State().list():
        print (state)

if __name__ == '__main__':

    # Defin arguments and usage
    parser = argparse.ArgumentParser(description="LED handler for ReSpeaker used with Snips")
    parser.add_argument('action', type=str, choices=['start', 'list', 'try'], help="Action to launch in the LED handler")
    parser.add_argument('--state', help="The state you wish to try")
    args = parser.parse_args(sys.argv[1:])

    if (args.action == 'list'):
        main_list()
    elif (args.action == 'start'):
        main_start()
    elif (args.action == 'try'):
        main_try(args.state)

