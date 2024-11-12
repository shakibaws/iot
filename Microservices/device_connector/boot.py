import machine
if machine.reset_cause() == machine.DEEPSLEEP_RESET:
    print('woke from a deep sleep')
    # set the frequency to 80 Mhz | MIN
    machine.freq(80000000)
else:
    print('power on or hard reset')
    # set the frequency to 240 Mhz | MAX
    machine.freq(240000000)

# configure input RTC pin with pull-up on boot
pin = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_UP)
