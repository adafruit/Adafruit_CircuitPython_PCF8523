# SPDX-FileCopyrightText: 2016 Philip R. Moyer for Adafruit Industries
# SPDX-FileCopyrightText: 2016 Radomir Dopieralski for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pcf8523` - PCF8523 Real Time Clock module
====================================================

This library supports the use of the PCF8523-based RTC in CircuitPython. It
contains a base RTC class used by all Adafruit RTC libraries. This base
class is inherited by the chip-specific subclasses.

Functions are included for reading and writing registers and manipulating
datetime objects.

Author(s): Philip R. Moyer and Radomir Dopieralski for Adafruit Industries.
Date: November 2016
Affiliation: Adafruit Industries

Implementation Notes
--------------------

**Hardware:**

* Adafruit `Adalogger FeatherWing - RTC + SD Add-on <https://www.adafruit.com/products/2922>`_
  (Product ID: 2922)
* Adafruit `PCF8523 RTC breakout <https://www.adafruit.com/products/3295>`_ (Product ID: 3295)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

**Notes:**

#. Milliseconds are not supported by this RTC.
#. The alarm does not support seconds. It will always fire on full minutes.
#. Datasheet: http://cache.nxp.com/documents/data_sheet/PCF8523.pdf

"""

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PCF8523.git"

from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register import i2c_bit
from adafruit_register import i2c_bits
from adafruit_register import i2c_bcd_alarm
from adafruit_register import i2c_bcd_datetime
from micropython import const

try:
    import typing  # pylint: disable=unused-import
    from busio import I2C
    from time import struct_time
except ImportError:
    pass

STANDARD_BATTERY_SWITCHOVER_AND_DETECTION = 0b000
BATTERY_SWITCHOVER_OFF = 0b111


class PCF8523:
    """Interface to the PCF8523 RTC.

    :param ~busio.I2C i2c_bus: The I2C bus the device is connected to

    **Quickstart: Importing and using the device**

        Here is an example of using the :class:`PCF8523` class.
        First you will need to import the libraries to use the sensor

        .. code-block:: python

            import time
            import board
            import adafruit_pcf8523

        Once this is done you can define your `board.I2C` object and define your sensor object

        .. code-block:: python

            i2c = board.I2C()  # uses board.SCL and board.SDA
            rtc = adafruit_pcf8523.PCF8523(i2c)

        Now you can give the current time to the device.

        .. code-block:: python

            t = time.struct_time((2017, 10, 29, 15, 14, 15, 0, -1, -1))
            rtc.datetime = t

        You can access the current time accessing the :attr:`datetime` attribute.

        .. code-block:: python

            current_time = rtc.datetime

    """

    lost_power = i2c_bit.RWBit(0x03, 7)
    """True if the device has lost power since the time was set."""

    power_management = i2c_bits.RWBits(3, 0x02, 5)
    """Power management state that dictates battery switchover, power sources
    and low battery detection. Defaults to BATTERY_SWITCHOVER_OFF (0b111)."""

    # The False means that day comes before weekday in the registers. The 0 is
    # that the first day of the week is value 0 and not 1.
    datetime_register = i2c_bcd_datetime.BCDDateTimeRegister(0x03, False, 0)
    """Current date and time."""

    clockout_frequency = i2c_bits.RWBits(3, 0x0F, 3)
    """Clock output frequencies generated. Default is 32.768kHz.
    Possible values are as shown (selection value - frequency).
    000 - 32.768khz
    001 - 16.384khz
    010 - 8.192kHz
    011 - 4.096kHz
    100 - 1.024kHz
    101 - 0.032kHz (32Hz)
    110 - 0.001kHz (1Hz)
    111 - Disabled
    """

    CLOCKOUT_FREQ_32KHZ = const(0b000)
    """Clock frequency of 32 KHz"""
    CLOCKOUT_FREQ_16KHZ = const(0b001)
    """Clock frequency of 16 KHz"""
    CLOCKOUT_FREQ_8KHZ = const(0b010)
    """Clock frequency of  8 KHz"""
    CLOCKOUT_FREQ_4KHZ = const(0b011)
    """Clock frequency of  4 KHz"""
    CLOCKOUT_FREQ_1KHZ = const(0b100)
    """Clock frequency of  4 KHz"""
    CLOCKOUT_FREQ_32HZ = const(0b101)
    """Clock frequency of 32 Hz"""
    CLOCKOUT_FREQ_1HZ = const(0b110)
    """Clock frequency of 1 Hz"""
    CLOCKOUT_FREQ_DISABLED = const(0b111)
    """Clock output disabled"""

    # The False means that day and weekday share a register. The 0 is that the
    # first day of the week is value 0 and not 1.
    alarm = i2c_bcd_alarm.BCDAlarmTimeRegister(
        0x0A, has_seconds=False, weekday_shared=False, weekday_start=0
    )
    """Alarm time for the first alarm. Note that the value of the seconds-fields
    is ignored, i.e. alarms only fire at full minutes. For short-term
    alarms, use a timer instead."""

    alarm_interrupt = i2c_bit.RWBit(0x00, 1)
    """True if the interrupt pin will output when alarm is alarming."""

    alarm_status = i2c_bit.RWBit(0x01, 3)
    """True if alarm is alarming. Set to False to reset."""

    timerA_enabled = i2c_bits.RWBits(2, 0x0F, 1)
    """Configures timerA. Possible values:
    00 - disabled
    01 - enabled as countdown timer
    10 - enabled as watchdog timer
    11 - disabled
    """

    timerA_frequency = i2c_bits.RWBits(3, 0x10, 0)
    """TimerA clock frequency. Default is 1/3600Hz.
    Possible values are as shown (selection value - frequency).
    000 - 4.096kHz
    001 - 64Hz
    010 -  1Hz
    011 -  1/60Hz
    111 -  1/3600Hz
    """

    TIMER_FREQ_4KHZ = const(0b000)
    """Timer frequency of 4 KHz"""
    TIMER_FREQ_64HZ = const(0b001)
    """Timer frequency of 64 Hz"""
    TIMER_FREQ_1HZ = const(0b010)
    """Timer frequency of 1 Hz"""
    TIMER_FREQ_1_60HZ = const(0b011)
    """Timer frequency of 1/60 Hz"""
    TIMER_FREQ_1_3600HZ = const(0b111)
    """Timer frequency of 1/3600 Hz"""

    timerA_value = i2c_bits.RWBits(8, 0x11, 0)
    """ TimerA value (0-255). The default is undefined.
    The total countdown duration is calcuated by
    timerA_value/timerA_frequency. For a higher precision, use higher values
    and frequencies, e.g. for a one minute timer you could use
    value=1, frequency=1/60Hz or value=60, frequency=1Hz. The
    latter will give better results. See the PCF85x3 User's Manual
    for details."""

    timerA_interrupt = i2c_bit.RWBit(0x01, 1)
    """True if the interrupt pin will assert when timerA has elapsed.
    Defaults to False."""

    timerA_watchdog = i2c_bit.RWBit(0x01, 2)
    """True if the interrupt pin will output when timerA generates a
    watchdog-alarm. Defaults to False."""

    timerA_status = i2c_bit.RWBit(0x01, 6)
    """True if timerA has elapsed. Set to False to reset."""

    timerA_pulsed = i2c_bit.RWBit(0x0F, 7)
    """True if timerA asserts INT as a pulse. The default
    value False asserts INT permanently."""

    timerB_enabled = i2c_bit.RWBit(0x0F, 0)
    """True if the timerB is enabled. Default is False."""

    timerB_frequency = i2c_bits.RWBits(3, 0x12, 0)
    """TimerB clock frequency. Default is 1/3600Hz.
    Possible values are as shown (selection value - frequency).
    000 - 4.096kHz
    001 - 64Hz
    010 -  1Hz
    011 -  1/60Hz
    111 -  1/3600Hz
    """

    timerB_value = i2c_bits.RWBits(8, 0x13, 0)
    """ TimerB value (0-255). The default is undefined.
    The total countdown duration is calcuated by
    timerB_value/timerB_frequency. For a higher precision, use higher values
    and frequencies, e.g. for a one minute timer you could use
    value=1, frequency=1/60Hz or value=60, frequency=1Hz. The
    latter will give better results. See the PCF85x3 User's Manual
    for details."""

    timerB_interrupt = i2c_bit.RWBit(0x01, 0)
    """True if the interrupt pin will assert when timerB has elapsed.
    Defaults to False."""

    timerB_status = i2c_bit.RWBit(0x01, 5)
    """True if timerB has elapsed. Set to False to reset."""

    timerB_pulsed = i2c_bit.RWBit(0x0F, 6)
    """True if timerB asserts INT as a pulse. The default
    value False asserts INT permanently."""

    battery_low = i2c_bit.ROBit(0x02, 2)
    """True if the battery is low and should be replaced."""

    high_capacitance = i2c_bit.RWBit(0x00, 7)
    """True for high oscillator capacitance (12.5pF), otherwise lower (7pF)"""

    calibration_schedule_per_minute = i2c_bit.RWBit(0x0E, 7)
    """False to apply the calibration offset every 2 hours (1 LSB = 4.340ppm);
    True to offset every minute (1 LSB = 4.069ppm).  The default, False,
    consumes less power.  See datasheet figures 28-31 for details."""

    calibration = i2c_bits.RWBits(  # pylint: disable=unexpected-keyword-arg
        7, 0xE, 0, signed=True
    )
    """Calibration offset to apply, from -64 to +63.  See the PCF8523 datasheet
    figure 18 for the offset calibration calculation workflow."""

    def __init__(self, i2c_bus: I2C):
        self.i2c_device = I2CDevice(i2c_bus, 0x68)

    @property
    def datetime(self) -> struct_time:
        """Gets the current date and time or sets the current date and time then starts the
        clock."""
        return self.datetime_register

    @datetime.setter
    def datetime(self, value: struct_time):
        # Automatically sets lost_power to false.
        self.power_management = STANDARD_BATTERY_SWITCHOVER_AND_DETECTION
        self.datetime_register = value
