# -*-: coding utf-8 -*-
""" Handler for various states of the system. """

from leds_service import LedsService
import time 

class State:
    none, welcome, goodbye, hotword_toggle_on, hotword_detected, asr_start_listening, asr_text_captured, error, idle, session_queued, session_started, session_ended, nlu_intent_parsed, say = range(14)

    def list(self):
        return [s for s in dir(self) if not s.startswith('__') and not s == 'list']
    
    def get_id(self, state_name=None):
        if state_name is not None:
            return self.__dict__[state_name]

class StateHandler:
    """ Handler for various states of the system. """

    def __init__(self, thread_handler, logger = None):
        self.leds_service = LedsService(thread_handler, logger)
        self.state = None

    def set_state(self, state):
        if state == State.goodbye:
            self.leds_service.start_animation(LedsService.State.none)
        elif state == State.welcome:
            self.leds_service.start_animation(LedsService.State.waking_up)
            time.sleep(2.2)
            self.leds_service.start_animation(LedsService.State.standby)
        elif state == State.hotword_toggle_on:
            self.leds_service.start_animation(LedsService.State.standby)
        elif state == State.hotword_detected:
            self.leds_service.start_animation(LedsService.State.listening)
        elif state == State.nlu_intent_parsed:
            self.leds_service.start_animation(LedsService.State.intentParsed)
        elif state == State.say:
            self.leds_service.start_animation(LedsService.State.speak)
        elif state == State.error:
            self.leds_service.start_animation(LedsService.State.error)
        elif state == State.session_queued:
            pass
        elif state == State.session_started:
            pass
        elif state == State.session_ended:
            pass
        self.state = state
