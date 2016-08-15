import atexit
from datetime import datetime
import time

import RPi.GPIO as GPIO


PULSES_PER_LITRE = 3900
FORCE_SENSOR_RC_MAX_CHARGE_TIME_MS = 25
MIN_MS_BETWEEN_FORCE_SENSOR_CHECKS = 10


class Sensors(object):
    def __init__(self, flow_sensor_channel, force_sensor_channel):
        self._flow_sensor_channel = flow_sensor_channel
        self._force_sensor_channel = force_sensor_channel

        self._time_of_last_force_sensor_check = None
        self._num_pulses = 0

        GPIO.setmode(GPIO.BCM)

        GPIO.setup(flow_sensor_channel, GPIO.IN)
        GPIO.setup(force_sensor_channel, GPIO.OUT, initial=GPIO.LOW)

        atexit.register(self._exit_handler)

        # Listen for flow sensor interrupts
        GPIO.add_event_detect(
            self._flow_sensor_channel,
            GPIO.RISING,
            callback=self._handle_flow_sensor_interrupt
        )

    def _exit_handler(self):
        GPIO.cleanup()

    def _handle_flow_sensor_interrupt(self, channel):
        self._num_pulses += 1

    def get_litres_acc(self):
        """Return the amount of water that has flowed through the sensor since
        the last reset in litres."""
        return self._num_pulses / 3900

    def reset_litres_acc(self):
        """Reset the amount of water that has flowed through the sensor to
        zero."""
        self._num_pulses = 0

    def get_force_sensor_state(self):
        """Return force sensor state as a boolean."""
        if self._time_of_last_force_sensor_check:
            time_since_last_ms = int(
                (datetime.now() -
                    self._time_of_last_force_sensor_check).microseconds / 1000
            )
            if (time_since_last_ms < MIN_MS_BETWEEN_FORCE_SENSOR_CHECKS):
                time.sleep((
                    MIN_MS_BETWEEN_FORCE_SENSOR_CHECKS - time_since_last_ms
                ) / 1000)

        GPIO.setup(self._force_sensor_channel, GPIO.IN)
        time.sleep(FORCE_SENSOR_RC_MAX_CHARGE_TIME_MS / 1000)
        sensor_state = GPIO.input(self._force_sensor_channel)
        GPIO.setup(self._force_sensor_channel, GPIO.OUT, initial=GPIO.LOW)

        self._time_of_last_force_sensor_check = datetime.now()

        return bool(sensor_state)
