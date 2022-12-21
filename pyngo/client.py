from pathlib import Path
from typing import Optional

import usb
import usb.backend.libusb1
import usb.util

from ._errors import *


def _get_backend() -> str:
    '''Attempt to find a libusb 1.0 library to use as pyusb's backend, exit if one isn't found.'''

    search_paths = (
        Path('/usr/local/lib'),
        Path('/usr/lib'),
        Path('/opt/homebrew/lib'),
        Path('/opt/procursus/lib'),
    )

    for path in search_paths:
        for file_ in path.rglob('*libusb-1.0*'):
            if not file_.is_file():
                continue

            if file_.suffix not in ('.so', '.dylib'):
                continue

            return usb.backend.libusb1.get_backend(find_library=lambda _: file_)

    raise usb.core.NoBackendError('No backend available')


class Client:
    def __init__(self, device: usb.core.Device) -> None:
        if not isinstance(device, usb.core.Device):
            raise TypeError('Device must be an instance of usb.core.Device')

        if device.idVendor != 0x5AC:
            raise ValueError('Device must be an Apple device')

        if (
            device.product != 'pongoOS USB Device'
            or device.manufacturer != 'checkra1n team'
        ):
            raise ValueError('Device must be booted into pongoOS')

        self._device = device

        if self._device.is_kernel_driver_active(0):
            self._device.detach_kernel_driver(0)

        self._device.set_configuration()
        usb.util.claim_interface(self._device, 0)

    def __del__(self) -> None:
        usb.util.release_interface(self._device, 0)
        self._device.attach_kernel_driver(0)

    def _ctrl_transfer(self, *args):
        return self._device.ctrl_transfer(*args)

    def _bulk_upload(self, data: bytes):
        return self._device.write(2, data)

    @classmethod
    def init(cls):
        for device in usb.core.find(
            find_all=True,
            idVendor=0x05AC,
            idProduct=0x4141,
            manufacturer='checkra1n team',
            product='pongoOS USB Device',
            backend=_get_backend(),
        ):
            return cls(device)

        raise DeviceNotFoundError('No pongoOS USB device found')

    def send_command(self, command: str) -> Optional[str]:
        if not isinstance(command, str):
            raise TypeError('Command must be a string')

        if len(command) > 512:
            raise ValueError('Command must be less than 512 characters long')

        self._ctrl_transfer(0x21, 4, 1, 0, 0)
        self._ctrl_transfer(
            0x21,
            3,
            0,
            0,
            command + '\n',
        )

        self._ctrl_transfer(0xA1, 2, 0, 0, 1)
        output = ''.join([chr(x) for x in self._ctrl_transfer(0xA1, 1, 0, 0, 4096)])

        while True:
            self._ctrl_transfer(0xA1, 2, 0, 0, 1)
            line = ''.join([chr(x) for x in self._ctrl_transfer(0xA1, 1, 0, 0, 4096)])
            if len(line) == 0:
                break

            output += line

        self._ctrl_transfer(0x21, 4, 0xFFFF, 0, 0)
        return output or None

    def send_data(self, data: bytes) -> None:
        if not isinstance(data, bytes):
            raise TypeError('Data must be a bytes object')

        # this line crashes pongoOS
        self._ctrl_transfer(0x21, 1, 0, 0, 4)
        self._device.write(2, data)
        self._ctrl_transfer(0x21, 4, 0xFFFF, 0, 0)
