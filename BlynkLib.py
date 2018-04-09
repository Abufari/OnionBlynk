#!/usr/bin/env python3

# The MIT License (MIT)
#
# Copyright (c) 2015 Volodymyr Shymanskyy
# Copyright (c) 2015 Daniel Campora
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import logging
import socket
import struct
import sys
import time

try:
    import machine

    idle_func = machine.idle
except ImportError:
    const = lambda x: x
    idle_func = lambda: 0
    setattr(sys.modules['time'], 'sleep_ms', lambda ms: time.sleep(ms // 1000))
    setattr(sys.modules['time'], 'ticks_ms', lambda: int(time.time() * 1000))
    setattr(sys.modules['time'], 'ticks_diff', lambda s, e: e - s)

HDR_LEN = const(5)
HDR_FMT = "!BHH"

MAX_MSG_PER_SEC = const(20)

# App Commands
MSG_Response = const(0)
MSG_Register = const(1)
MSG_Login = const(2)
MSG_Hardware_Connected = const(4)
MSG_Get_Token = const(5)
MSG_Ping = const(6)

# Hardware Commands
MSG_Tweet = const(12)
MSG_Email = const(13)
MSG_Push_Notification = const(14)
MSG_Bridge = const(15)
MSG_Hardware_Sync = const(16)
MSG_Blynk_Internal = const(17)
MSG_Set_Widget_Property = const(19)
MSG_Hardware = const(20)

# App Commands
MSG_App_Sync = const(25)
MSG_Create_Widget = const(33)
MSG_Update_Widget = const(34)
MSG_Delete_Widget = const(35)
MSG_App_Connected = const(50)

Response_OK = const(200)

HEARTBEAT_PERIOD = const(10)
NON_BLK_SOCK = const(0)
MIN_SOCK_TO = const(1)  # 1 second
MAX_SOCK_TIMEOUT = const(5)  # 5 seconds, must be < HEARTBEAT_PERIOD
RECONNECT_DELAY = const(1)  # seconds
TASK_PERIOD_RES = const(50)  # 50 ms
IDLE_TIME_MS = const(5)  # 5 ms

RE_TX_DELAY = const(2)
MAX_TX_RETRIES = const(3)

MAX_VIRTUAL_PINS = const(32)

DISCONNECTED = const(0)
CONNECTING = const(1)
AUTHENTICATING = const(2)
AUTHENTICATED = const(3)

EAGAIN = const(11)


def sleep_from_until(start, delay):
    while time.ticks_diff(start, time.ticks_ms()) < delay:
        idle_func()
    return start + delay


class VrPin:
    def __init__(self, read=None, write=None):
        self.read = read
        self.write = write


class Terminal:
    def __init__(self, blynk, pin):
        self._blynk = blynk
        self._pin = pin

    def write(self, data):
        self._blynk.virtual_write(self._pin, data)

    def read(self, size):
        return ''

    def virtual_read(self):
        pass

    def virtual_write(self, value):
        try:
            out = eval(value)
            if out is not None:
                print(repr(out))
        except:
            try:
                exec(value)
            except Exception as e:
                print('Exception:\n  ' + repr(e))


class Blynk:

    def __init__(self, token, server='blynk-cloud.com', port=None,
                 connect=True, ssl=False):
        self._tx_count = 0
        self._last_hb_id = 0
        self._hb_time = 0
        self._vr_pins = {}
        self._do_connect = False
        self._on_connect = None
        self._task = None
        self._task_period = 0
        self._token = token
        if isinstance(self._token, str):
            self._token = token.encode('ascii')
        self._server = server
        if port is None:
            if ssl:
                port = 8441
            else:
                port = 8442
        self._port = port
        self._do_connect = connect
        self._ssl = ssl
        self.state = DISCONNECTED

        # run relevant variabables
        self._start_time = time.ticks_ms()
        self._task_millis = self._start_time
        self._hw_pins = {}
        self._rx_data = b''
        self._msg_id = 1
        self._timeout = None
        self._last_server_alive_checked = 0

        self.hdr = struct.Struct(HDR_FMT)
        self.logger = logging.getLogger('__main__.' + __name__)

    def run(self):
        self._start_time = time.ticks_ms()
        self._task_millis = self._start_time
        self._hw_pins = {}
        self._rx_data = b''
        self._msg_id = 1
        self._timeout = None
        self._tx_count = 0
        self._last_server_alive_checked = 0
        self.state = DISCONNECTED

        while True:
            self._block_until_connected_to_blynk()

            self._communicate_with_blynk_and_run_task()

            if not self._do_connect:
                self._close()
                print('Blynk disconnection requested by the user')

    def _block_until_connected_to_blynk(self):
        while self.state != AUTHENTICATED:
            self._run_task()
            if self._do_connect:
                try:
                    self._connect_via_ssl_or_tcp()
                except:
                    self._close('connection with the Blynk servers failed')
                    continue

                self.state = AUTHENTICATING
                hdr = self.hdr.pack(MSG_Login, self._new_msg_id(),
                                    len(self._token))
                self.logger.info('Blynk connection successful, '
                                 'authenticating...')
                self._send(hdr + self._token, True)
                data = self._receive(HDR_LEN, timeout=MAX_SOCK_TIMEOUT)
                if not data:
                    self._close('Blynk authentication timed out')
                    continue

                msg_type, msg_id, status = self.hdr.unpack(data)
                if status != Response_OK or msg_id == 0:
                    self._close('Blynk authentication failed')
                    continue

                self.state = AUTHENTICATED
                self._send(
                    self._format_msg(MSG_Blynk_Internal, 'ver', '0.0.1+py',
                                     'h-beat', HEARTBEAT_PERIOD, 'dev',
                                     sys.platform))
                self.logger.info('Access granted, happy Blynking!')
                self._hb_time = int(time.time())
                if self._on_connect:
                    self._on_connect()
            else:
                self._start_time = sleep_from_until(self._start_time,
                                                    TASK_PERIOD_RES)

    def _communicate_with_blynk_and_run_task(self):
        while self._do_connect:
            data = None
            try:
                data = self._receive(HDR_LEN, NON_BLK_SOCK)
            except:
                pass
            if data:
                msg_type, msg_id, msg_len = struct.unpack(HDR_FMT, data)
                if msg_id == 0:
                    self._close('invalid msg id %d' % msg_id)
                    break
                if msg_type == MSG_Response:
                    if msg_id == self._last_hb_id:
                        self.logger.debug('setting last_hb_id to 0')
                        self._last_hb_id = 0
                    else:
                        self.logger.debug(
                            'last_hb_id ({}) != msg_id ({}), '
                            'but msg_type == '
                            'MSG_Response'.format(
                                self._last_hb_id, msg_id
                                ))
                elif msg_type == MSG_Ping:
                    # Send Pong
                    self.logger.debug('sending Pong in communicate_with_blynk')
                    self._send(
                        self.hdr.pack(MSG_Response, msg_id,
                                      Response_OK), True)
                elif msg_type == MSG_Hardware or msg_type == MSG_Bridge:
                    data = self._receive(msg_len, MIN_SOCK_TO)
                    if data:
                        self._handle_hw(data)
                else:
                    self._close('unknown message type %d' % msg_type)
                    break
            else:
                self._start_time = sleep_from_until(self._start_time,
                                                    IDLE_TIME_MS)
            if not self._server_alive():
                self._close('Blynk server is offline')
                break
            self._run_task()

    def _format_msg(self, msg_type, *args):
        """convert params to string and join using \0"""
        data = ('\0'.join(map(str, args))).encode('ascii')
        # prepend HW command header
        return self.hdr.pack(msg_type, self._new_msg_id(),
                             len(data)) + data

    def _handle_hw(self, data):
        params = list(map(lambda x: x.decode('ascii'), data.split(b'\0')))
        cmd = params.pop(0)
        if cmd == 'info':
            pass
        elif cmd == 'pm':
            # direct pin operations
            pass
        elif cmd == 'vw':
            pin = int(params.pop(0))
            if pin in self._vr_pins and self._vr_pins[pin].write:
                for param in params:
                    self._vr_pins[pin].write(param)
            else:
                print("Warning: Virtual write to unregistered pin %d" % pin)
        elif cmd == 'vr':
            pin = int(params.pop(0))
            if pin in self._vr_pins and self._vr_pins[pin].read:
                self._vr_pins[pin].read()
            else:
                print("Warning: Virtual read from unregistered pin %d" % pin)
        else:
            raise ValueError("Unknown message cmd: %s" % cmd)

    def _new_msg_id(self):
        self._msg_id += 1
        if self._msg_id > 0xFFFF:
            self._msg_id = 1
        return self._msg_id

    def _settimeout(self, timeout):
        if timeout != self._timeout:
            self._timeout = timeout
            self.conn.settimeout(timeout)

    def _receive(self, length, timeout=0):
        self._settimeout(timeout)
        try:
            self._rx_data += self.conn.recv(length)
        except socket.timeout:
            return b''
        except socket.error as e:
            if e.args[0] == EAGAIN:
                return b''
            else:
                raise
        if len(self._rx_data) >= length:
            data = self._rx_data[:length]
            self._rx_data = self._rx_data[length:]
            return data
        else:
            return b''

    def _send(self, data, send_anyway=False):
        if self._tx_count < MAX_MSG_PER_SEC or send_anyway:
            retries = 0
            while retries <= MAX_TX_RETRIES:
                try:
                    self.conn.send(data)
                    self._tx_count += 1
                    break
                except socket.error as er:
                    if er.args[0] != EAGAIN:
                        raise
                    else:
                        time.sleep_ms(RE_TX_DELAY)
                        retries += 1

    def _close(self, emsg=None):
        self.conn.close()
        self.state = DISCONNECTED
        self._last_hb_id = 0
        time.sleep(RECONNECT_DELAY)
        if emsg:
            print('Error: %s, connection closed' % emsg)
            self.logger.error('{}, connection closed'.format(emsg))

    def _server_alive(self):
        now_server_alive_check = int(time.time())
        if self._last_server_alive_checked != now_server_alive_check:
            self._last_server_alive_checked = now_server_alive_check
            self._tx_count = 0
            # last_hb_id is 0 after receiving Pong
            if self._last_hb_id != 0 and \
                    now_server_alive_check - self._hb_time >= MAX_SOCK_TIMEOUT:
                self.logger.error(
                    'now_server_alive_check - hb_time > max_sock_timeout:\n'
                    '{} - {} > {}'.format(now_server_alive_check,
                                          self._hb_time,
                                          MAX_SOCK_TIMEOUT))
                return False
            if (now_server_alive_check - self._hb_time >= HEARTBEAT_PERIOD and
                    self.state == AUTHENTICATED):
                self._hb_time = now_server_alive_check
                self._last_hb_id = self._new_msg_id()
                self._send(self.hdr.pack(MSG_Ping, self._last_hb_id, 0),
                           send_anyway=True)
                self.logger.debug('Sending ping in _server_alive')
        return True

    def _run_task(self):
        if self._task:
            c_millis = time.ticks_ms()
            if c_millis - self._task_millis >= self._task_period:
                self._task_millis += self._task_period
                self._task()

    def repl(self, pin):
        repl = Terminal(self, pin)
        self.add_virtual_pin(pin, repl.virtual_read, repl.virtual_write)
        return repl

    def notify(self, msg):
        if self.state == AUTHENTICATED:
            self._send(self._format_msg(MSG_Push_Notification, msg))

    def tweet(self, msg):
        if self.state == AUTHENTICATED:
            self._send(self._format_msg(MSG_Tweet, msg))

    def email(self, to, subject, body):
        if self.state == AUTHENTICATED:
            self._send(self._format_msg(MSG_Email, to, subject, body))

    def setProperty(self, pin, pin_property, args):
        if self.state == AUTHENTICATED:
            self._send(self._format_msg(MSG_Set_Widget_Property, pin,
                                        pin_property, args))

    def virtual_write(self, pin, val):
        if self.state == AUTHENTICATED:
            self._send(self._format_msg(MSG_Hardware, 'vw', pin, val))

    def sync_all(self):
        if self.state == AUTHENTICATED:
            self._send(self._format_msg(MSG_Hardware_Sync))

    def sync_virtual(self, pin):
        if self.state == AUTHENTICATED:
            self._send(self._format_msg(MSG_Hardware_Sync, 'vr', pin))

    def add_virtual_pin(self, pin, read=None, write=None):
        if isinstance(pin, int) and pin in range(0, MAX_VIRTUAL_PINS):
            self._vr_pins[pin] = VrPin(read, write)
        else:
            raise ValueError('the pin must be an integer between 0 and %d' % (
                    MAX_VIRTUAL_PINS - 1))

    def VIRTUAL_READ(blynk, pin):
        class Decorator:
            def __init__(self, func):
                self.func = func
                blynk._vr_pins[pin] = VrPin(func, None)
                # print(blynk, func, pin)

            def __call__(self):
                return self.func()

        return Decorator

    def VIRTUAL_WRITE(blynk, pin):
        class Decorator:
            def __init__(self, func):
                self.func = func
                blynk._vr_pins[pin] = VrPin(None, func)

            def __call__(self):
                return self.func()

        return Decorator

    def on_connect(self, func):
        self._on_connect = func

    def set_user_task(self, task, ms_period):
        if ms_period % TASK_PERIOD_RES != 0:
            raise ValueError(
                'the user task period must be a multiple of %d ms' % TASK_PERIOD_RES)
        self._task = task
        self._task_period = ms_period

    def connect(self):
        self._do_connect = True

    def disconnect(self):
        self._do_connect = False
        self.logger.debug('setting _do_connect = False in disconnect()')

    def _connect_via_ssl_or_tcp(self):
        self.state = CONNECTING
        if self._ssl:
            import ssl
            self.logger.info('SSL: Connecting to %s:%d' % (
                self._server, self._port))
            ss = socket.socket(socket.AF_INET,
                               socket.SOCK_STREAM,
                               socket.IPPROTO_SEC)
            self.conn = ssl.wrap_socket(ss,
                                        cert_reqs=ssl.CERT_REQUIRED,
                                        ca_certs='/flash/cert/ca.pem')
        else:
            self.logger.info('TCP: Connecting to %s:%d' % (
                self._server, self._port))
            self.conn = socket.socket()
        self.conn.connect(
            socket.getaddrinfo(self._server, self._port)[0][4])
