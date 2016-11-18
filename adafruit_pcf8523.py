""" MicroPython library to support PCF8523 Real Time Clock (RTC).

This library supports the use of the PCF8523-based RTC in MicroPython. It
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

* Adafruit `Feather HUZZAH ESP8266 <https://www.adafruit.com/products/2821>`_ (Product ID: 2821)
* Adafruit `Feather M0 Adalogger <https://www.adafruit.com/products/2796>`_  (Product ID: 2796)
* Adafruit `Arduino Zero <https://www.adafruit.com/products/2843>`_ (Product ID: 2843)
* Pycom LoPy
* Adafruit `PCF8523 RTC breakout <https://www.adafruit.com/products/3295>`_ (Product ID: 3295)

**Software and Dependencies:**

* MicroPython firmware for the ESP8266, which can be obtained from

https://micropython.org/download/#esp8266

* MicroPython firmware for the M0-based boards, which can be obtained from:

https://github.com/adafruit/micropython/releases

* ucollections library
* utime library

**Notes:**

#. Milliseconds are not supported by this RTC.
#. The data sheet for the PCF8523 can be obtained from

http://cache.nxp.com/documents/data_sheet/PCF8523.pdf

"""

##############################################################################
# Credits and Acknowledgements:
#        Original code written by Radomir Dopieralski. See LICENSE file.
#
##############################################################################


##############################################################################
# Imports
##############################################################################

try:
	import os
except ImportError:
	import uos as os

osName = os.uname()[0]
bootMicro = False
if 'samd21' == osName:
	bootMicro = True
if 'esp8266' == osName:
	bootMicro = True
if 'LoPy' == osName:
	bootMicro = True
if 'WiPy' == osName:
	bootMicro = True
if 'pyboard' == osName:
	bootMicro = True

if bootMicro:
	import ucollections
	import utime
else:
	import collections as ucollections
	import time as utime


##############################################################################
# Globals and constants
##############################################################################

# DateTimeTuple is the same for all RTCs.
DateTimeTuple = ucollections.namedtuple("DateTimeTuple", ["year", "month",
    "day", "weekday", "hour", "minute", "second", "millisecond"])
# Note that AlarmTuple may need to be modified for each RTC.
AlarmTuple = ucollections.namedtuple("AlarmTuple", ["weekday", "day",
    "hour", "minute"])


##############################################################################
# Functions
##############################################################################

def datetime_tuple(year, month, day, weekday=0, hour=0, minute=0,
                    second=0, millisecond=0):
    """Return individual values converted into a data structure (a tuple).

    **Arguments:**

    * year - The year (four digits, required, no default).
    * month - The month (two digits, required, no default).
    * day - The day (two digits, required, no default).
    * weekday - The day of the week (one digit, optional, default zero).
    * hour - The hour (two digits, 24-hour format, optional, default zero).
    * minute - The minute (two digits, optional, default zero).
    * second - The second (two digits, optional, default zero).
    * millisecond - Milliseconds (not supported, default zero).

    """
    return DateTimeTuple(year, month, day, weekday, hour, minute,second,
        millisecond)


def alarm_tuple(weekday, day, hour, minute):
    """Return data structure for writing PCF8523 alarm registers.

    **Arguments:**

    * weekday - The weekday for the alarm (Sunday = 0, required, no default)
    * day - The day of the month for the alarm (required, no default)
    * hour - The hour of the alarm (required, no default)
    * minute - The minute for the alarm (required, no default)

    """
    return AlarmTuple(weekday, day, hour, minute)


def _bcd2bin(value):
    """Convert binary coded decimal to Binary

    **Arguments:**

    * value - the BCD value to convert to binary (required, no default)

    """
    return value - 6 * (value >> 4)


def _bin2bcd(value):
    """Convert a binary value to binary coded decimal.

    **Arguments:**

    * value - the binary value to convert to BCD. (required, no default)

    """
    return value + 6 * (value // 10)


def tuple2seconds(datetime):
    """Convert a datetime tuple to seconds since the epoch.

    **Arguments:**

    * datetime - a datetime tuple containing the date and time to convert.
      (required, no default)

    """
    return utime.mktime((datetime.year, datetime.month, datetime.day,
        datetime.hour, datetime.minute, datetime.second, datetime.weekday, 0))


def seconds2tuple(seconds):
    """Convert seconds since the epoch into a datetime structure.

    **Arguments:**

    * seconds - the value to convert. (required, no default)

    """
    year, month, day, hour, minute, second, weekday, _yday = utime.localtime()
    return DateTimeTuple(year, month, day, weekday, hour, minute, second, 0)


##############################################################################
# Classes and methods
##############################################################################

class _BaseRTC:
    """ Provide RTC functionality common across all Adafruit RTC products.

    This is the parent class inherited by the chip-specific subclasses.

    **Methods:**

    * __init__ - constructor (must be passed I2C interface object)
    * _register - read and write registers
    * _flag - return or set flag bits in registers

    """
    def __init__(self, i2c, address=0x68):
        """Base RTC class constructor.

        **Arguments:**

        * i2c - an existing I2C interface object (required, no default)
        * address - the hex i2c address for the DS3231 chip (default 0x68).

        """
        self.i2c = i2c                # An existing I2C interface object
        self.address = address        # The I2C address for the device

    def _register(self, register, buffer=None):
        """Base RTC class register method to set or read a register value.

        **Arguments:**

        * register - Hex address of the register to be manipulated. (required)
        * buffer - Data to be written to the register location, or None
          if the register is to be read.

        """
        if buffer is None:
            # Read the register byte and return it.
            return self.i2c.readfrom_mem(self.address, register, 1)[0]
        # Write the buffer contents into the register location.
        self.i2c.writeto_mem(self.address, register, buffer)

    def _flag(self, register, mask, value=None):
        """Set or return a bitwise flag setting.

        **Arguments:**

        * register - Hex address of the register to be used. (required)
        * mask - Binary bitmask to extract or write specific bits. (required)
        * value - Data to write into the flag register. If None, the method
        * returns the flag(s). If set, it is written to the register (using the
          mask parameter). (optional, default None)

        """
        data = self._register(register)
        if value is None:
            # Return True or False depending on the bit selected
            return bool(data & mask)
        if value:
            # Set the bit by oring the data with the mask
            data |= mask
        else:
            # Clear the bit
            data &= ~mask
        self._register(register, bytearray((data,)))


class PCF8523(_BaseRTC):
    """Subclass to support PCF8523 RTC operation. Inherits _BaseRTC.

    **Methods:**

    * __init__ - Overloaded base class constructor.
    * init - PCF8523-specific constructor.
    * datetime - return or set the RTC clock
    * alarm_time - return or set the time-of-day alarm
    * reset - Sets the control register to reset the RTC.
    * lost_power - Returns True if the board has lost power, False otherwise.
    * stop - Stops the RTC from transmitting data on I2C and freezes registers.
    * battery_low - Returns True if the CR1220 battery needs replacing, False
      otherwise.
    * alarm - Returns True or False indicating whether the alarm has triggered.
      Passing the value "False" will reset the interrupt and clear the flag.

    """
    _CONTROL1_REGISTER = 0x00
    _CONTROL2_REGISTER = 0x01
    _CONTROL3_REGISTER = 0x02
    _DATETIME_REGISTER = 0x03
    _ALARM_REGISTER = 0x0a
    _SQUARE_WAVE_REGISTER = 0x0f

    def __init__(self, *args, **kwargs):
        """Overloaded _BaseRTC constructor for PCF8523-specific arguments."""
        super().__init__(*args, **kwargs)
        self.init()

    def init(self):
        """Initializes register to enable battery management.

        **Arguments:**

        * none

        """
        # Enable battery switchover and low-battery detection.
        self._flag(self._CONTROL3_REGISTER, 0b11100000, False)
        # Enable BSIE - battery switchover interrupt enable
        self._flag(self._CONTROL3_REGISTER, 0b00000010, True)

    def datetime(self, datetime=None):
        """Read or set the RTC clock.

        **Arguments:**

        * datetime - a datetime structure to write to the RTC, i.e., sets the
          clock.

        """
        buffer = bytearray(7)
        if datetime is None:
            # Read and return the date and time.
            self.i2c.readfrom_mem_into(self.address, self._DATETIME_REGISTER,
                                       buffer)
            return datetime_tuple(
                year=_bcd2bin(buffer[6]) + 2000,
                month=_bcd2bin(buffer[5]),
                weekday=_bcd2bin(buffer[4]),
                day=_bcd2bin(buffer[3] & 0x3F),
                hour=_bcd2bin(buffer[2]),
                minute=_bcd2bin(buffer[1]),
                second=_bcd2bin(buffer[0] & 0x7F),
            )
        # Set the time.
        datetime = datetime_tuple(*datetime)    # convert argument to struct
        buffer[0] = _bin2bcd(datetime.second & 0x7F)   # format conversions
        buffer[1] = _bin2bcd(datetime.minute)
        buffer[2] = _bin2bcd(datetime.hour)
        buffer[3] = _bin2bcd(datetime.day & 0x3F)
        buffer[4] = _bin2bcd(datetime.weekday)
        buffer[5] = _bin2bcd(datetime.month)
        buffer[6] = _bin2bcd(datetime.year - 2000)
        self._register(self._DATETIME_REGISTER, buffer) # Write the register

    def alarm_time(self, alarmTime=None):
        """Set or return the time-of-day alarm on-chip.

        **Arguments:**

        * alarmTime - If None (the default), the method will return the current
          alarm setting in AlarmTime tuple format. Otherwise, it will set the
          alarm for the given time. If all values of the given time are None,
          however, this method will disable the alarm.

        """
        buffer = bytearray(4)
        if alarmTime is None:
            # Read the alarm register.
            self.i2c.readfrom_mem_into(self.address, self._ALARM_REGISTER,
                                      buffer)
            # Note: on the PCF8523, bit 8 is set to zero to enable the alarm
            # and 1 to disable it, so for this chip we have to check bit 8
            # to know if the alarm is enabled. If the alarm for a particular
            # time field is disabled, this method returns None for that field.
            return alarm_tuple(
                weekday=_bcd2bin(
                    buffer[3] & 0x7f) if not (buffer[3] & 0x80) else None,
                day=_bcd2bin(buffer[2] & 0x7f) if not (buffer[2] & 0x80) else None,
                hour=_bcd2bin(buffer[1] & 0x7f) if not (buffer[1] & 0x80) else None,
                minute=_bcd2bin(
                    buffer[0] & 0x7f) if not (buffer[0] & 0x80) else None,
            )
        # Write the alarm time to the alarm register.
        alarmTime = alarm_tuple(*alarmTime)  #  Convert to data structure
        # Set register values and defaults. Note that setting the alarm
        # clock values also enables the alarm!
        # Also note that for the PCF8523 bit 8 set to zero _enables_ the alarm
        # and the default is 1 (disabled). Setting all parameters to None will
        # disable the alarm by setting bit 8 to 1.
        buffer[0] = (_bin2bcd(alarmTime.minute)
                     if alarmTime.minute is not None else 0x80)
        buffer[1] = (_bin2bcd(alarmTime.hour)
                     if alarmTime.hour is not None else 0x80)
        buffer[2] = (_bin2bcd(alarmTime.day)
                     if alarmTime.day is not None else 0x80)
        buffer[3] = (_bin2bcd(alarmTime.weekday)
                     if alarmTime.weekday is not None else 0x80)
        # Set the alarm
        self._register(self._ALARM_REGISTER, buffer)
	# Set the interrupt pin enable
	self._flag(self._CONTROL1_REGISTER, 0b00000010, True)

    def reset(self):
        """Sets the flag to reset the RTC.

        **Arguments:**

        * none

        """
        self._flag(self._CONTROL1_REGISTER, 0x58, True)
        self.init()

    def lost_power(self, value=None):
        """Set or return flag for power loss detection.

        **Arguments:**

        * value - True or False to set the register, None to return current value.
          (optional, default None)

        """
        return self._flag(self._CONTROL3_REGISTER, 0b00001000, value)

    def stop(self, value=None):
        """Stop the RTC from transmitting data on I2C.

        **Arguments:**

        * value - True or False to set the register, None to return current value.
          (optional, default None)

        """
        return self._flag(self._CONTROL1_REGISTER, 0b00010000, value)

    def battery_low(self):
        """Return True if battery needs replacement.

        **Arguements:**

        * none

        """
        return self._flag(self._CONTROL3_REGISTER, 0b00000100)

    def alarm(self, value=None):
        """Return current alarm state, or clear alarm interrupt.

        **Arguments:**

        * value - 0 to unset registerand clear interrupt, None to return
          True or False depending on whether the alarm has been triggered.
          (optional, default None)

        """
        return self._flag(self._CONTROL2_REGISTER, 0b00001000, value)
