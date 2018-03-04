# -*-: coding utf-8 -*-
""" Handler for various states of the system. """

from leds_service import LedsService

class State:
    none, welcome, goodbye, hotword_toggle_on, hotword_detected, asr_start_listening, asr_text_captured, error, idle, session_queued, session_started, session_ended, nlu_intent_parsed, say = range(14)

class StateHandler:
    """ Handler for various states of the system. """

    def __init__(self, thread_handler):
        self.leds_service = LedsService(thread_handler)
        self.state = None

    def set_state(self, state):
        if state == State.goodbye:
            self.leds_service.start_animation(LedsService.State.none)
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
