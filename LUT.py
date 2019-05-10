from kivy.uix.screenmanager import Screen
from kivy.factory import Factory
from LUT_Script import LUTScript
from pyftdi.i2c import I2cController, I2cIOError
from usb.core import USBError
from pyftdi.usbtools import UsbToolsError
import re


class Lut(Screen):
    addresses = range(64)
    script_values = list()
    slave_device = None
    i2c_device = None
    os = None

    def set_os(self, os):
        self.os = os

    def activate_osx(self):
        try:
            self.i2c_device = I2cController()
            self.i2c_device.configure('ftdi://ftdi:232h/1')
            self.slave_device = self.i2c_device.get_port(int("60", 16))
            self.slave_device.configure_register(bigendian=True, width=2)
        except USBError:
            usb_error = Factory.ErrorPopup()
            usb_error.text = str(USBError)
            usb_error.open()
        except UsbToolsError:
            usb_tool_error = Factory.ErrorPopup()
            usb_tool_error.text = str(UsbToolsError)
            usb_tool_error.open()
        except I2cIOError:
            i2c_io_error = Factory.ErrorPopup()
            i2c_io_error.text = str(I2cIOError)
            i2c_io_error.open()

    def activate_win(self):
        import ctypes
        dll = ctypes.windll.LoadLibrary('/Users/eric/Desktop/i2c_dll.dll')
        dll.i2c_init()

    @staticmethod
    def validate_address(text):
        valid = re.compile(r"^[a-fA-F0-9]{2,4}$")
        if not valid.match(text.replace("0x", "")):
            return False
        else:
            return True

    @staticmethod
    def calc_lut(addresses, bin_weight_eye_adj_param1, bin_weight_eye_adj_param2, a_pre, b_main, c_post, scale_factor):

        y_values = list()
        minimized_values = list()
        normalized_values = list()
        final_lut_ints = list()
        final_lut_bins = list()

        count = 4
        b_fix = False
        for address in addresses:
            bin_string = format(address, '06b')

            a = ((bin_weight_eye_adj_param2 * int(bin_string[0])) + (
                        bin_weight_eye_adj_param1 * int(bin_string[1]))) * a_pre

            if ((address == 12 or address == 28 or address == 44 or address == 60) or b_fix is True) and address != 0:
                b_fix = True
                b = ((2 * int(bin_string[2])) + (1 * int(bin_string[3]))) * b_main
                count -= 1
                if count == 0:
                    b_fix = False
                    count = 4
            else:
                b = ((bin_weight_eye_adj_param2 * int(bin_string[2])) + (
                            bin_weight_eye_adj_param1 * int(bin_string[3]))) * b_main

            if (address + 1) % 4 == 0:
                c = ((2 * int(bin_string[4])) + (1 * int(bin_string[5]))) * c_post
            else:
                c = ((bin_weight_eye_adj_param2 * int(bin_string[4])) + (
                            bin_weight_eye_adj_param1 * int(bin_string[5]))) * c_post

            sum_factor = a + b + c

            y_values.append(sum_factor)

        for y_value in y_values:
            minimized_values.append(y_value - min(y_values))

        for minimized_value in minimized_values:
            normalized_values.append((minimized_value / max(minimized_values)) * 63)

        for normalized_value in normalized_values:
            final_lut_ints.append(((normalized_value - 31.5) * scale_factor) + 31.5)

        for final_lut_int in final_lut_ints:
            final_lut_bins.append(format(int(final_lut_int), '06b'))

        return final_lut_bins

    def get_lut(self):
        try:
            bin_weight_eye_adj_param1 = float(self.pam1.text)
            bin_weight_eye_adj_param2 = float(self.pam2.text)
            a_pre = float(self.a.text)
            b_main = float(self.b.text)
            c_post = float(self.c.text)
            scale_factor = float(self.scale.text)

            # get lut valuse
            lut = self.calc_lut(self.addresses, bin_weight_eye_adj_param1, bin_weight_eye_adj_param2, a_pre, b_main,
                                c_post, scale_factor)

            # transpose to get 64 bit values
            lut_transposed = [''.join(s) for s in zip(*lut)]

            self.lut_text.text = ''

            lut_value_list = list()

            for row in reversed(lut_transposed):
                row = ' '.join(row[i:i+8] for i in range(0, len(row), 8))
                self.lut_text.text += (row + '\n\n')

                row = row.split(' ')
                for value in row:
                    value = ''.join(reversed(value))
                    value = "{0:#0{1}x}".format((int(value, 2)), 4)
                    lut_value_list.append(value)

            self.script_values = lut_value_list

        except ValueError:
            input_error_popup = Factory.ErrorPopup()
            input_error_popup.text = 'Error: invalid input values'
            input_error_popup.open()
        except ZeroDivisionError:
            input_error_popup = Factory.ErrorPopup()
            input_error_popup.text = 'Error: invalid input values'
            input_error_popup.open()

    def write(self, start_address, values):
        if len(values) != 0:
            if self.validate_address(start_address):
                commands = list()
                address = start_address

                for i in range(len(values)):
                    address = int(address, 16)
                    address = "{0:#0{1}x}".format(address, 6)
                    command_sequence = ['write', address, '[7:0]', values[i]]
                    commands.append(command_sequence)
                    address = int(address, 16) + 1
                    address = "{0:#0{1}x}".format(address, 6)

                if self.os == 'osx':
                    self.activate_osx()
                    if self.slave_device is not None:
                        lut_script = LUTScript(commands)
                        lut_script.execute(self.slave_device, self.lut_script_log_label, self.lut_script_progress_bar,
                                           self.lut_text, self.i2c_device)
                if self.os == 'win32':
                    print("Win Write")

            else:
                blank_addr_error = Factory.ErrorPopup()
                blank_addr_error.text = "Error: no address added or invalid address"
                blank_addr_error.open()
        else:
            no_lut_error = Factory.ErrorPopup()
            no_lut_error.text = "Error: LUT not calculated"
            no_lut_error.open()
