from pyftdi.i2c import I2cIOError, I2cNackError, I2cTimeoutError
import threading


class LUTScriptOSX:
    def __init__(self, commands):
        self.commands = commands

    def execute(self, slave, script_log_label, script_progress_bar, script_preview_text_input, i2c_device):
        run = RunOSX(self.commands, slave, script_log_label, script_progress_bar, script_preview_text_input,
                     i2c_device)
        run.start()


class LUTScriptWIN32:
    def __init__(self, commands):
        self.commands = commands

    def execute(self, slave, script_log_label, script_progress_bar, script_preview_text_input, dll):
        run = RunWIN32(self.commands, slave, script_log_label, script_progress_bar, script_preview_text_input,
                       dll)
        run.start()


class RunOSX(threading.Thread):
    def __init__(self, commands, slave, script_log_label, script_progress_bar, script_preview_text_input, i2c_device):
        super(RunOSX, self).__init__()
        self.commands = commands
        self.slave = slave
        self.i2c_device = i2c_device
        self.script_log_label = script_log_label
        self.script_progress_bar = script_progress_bar
        self.script_preview_text_input = script_preview_text_input

    def run(self):
        progress_segment = self.script_progress_bar.max / len(self.commands)
        self.script_preview_text_input.text = ''

        for command in self.commands:
            try:
                address = int(command[1], 16)

                write_value = command[3]
                if write_value.replace("0x", '').__len__() == 1:
                    write_value = '0' + write_value.replace("0x", '')

                data = bytearray.fromhex(write_value.replace('0x', ''))
                self.slave.write_to(address, data)
                if int(hex(self.slave.read_from(address, 1)[0]), 16) == data[0]:
                    self.script_log_label.text = (command[3] + " written to bit(s) " + command[2] + " in " +
                                                  command[1])
                else:
                    self.script_log_label.text = ("Failed to write " + command[3] + " to bit(s) " + command[2] +
                                                  " in " + command[1])

            except AttributeError:
                self.script_log_label.text = "No Slave Device"
            except I2cNackError:
                self.script_log_label.text = str(I2cNackError)
            except I2cIOError:
                self.script_log_label.text = str(I2cIOError)
            except I2cTimeoutError:
                self.script_log_label.text = str(I2cTimeoutError)
            self.script_progress_bar.value += progress_segment

            self.script_preview_text_input.text += self.script_log_label.text + '\n'

        self.script_log_label.text = "End Write"
        self.script_progress_bar.value = 0
        self.i2c_device.terminate()


class RunWIN32(threading.Thread):
    def __init__(self, commands, slave, script_log_label, script_progress_bar, script_preview_text_input, dll):
        super(RunWIN32, self).__init__()
        self.commands = commands
        self.slave = slave
        self.dll = dll
        self.script_log_label = script_log_label
        self.script_progress_bar = script_progress_bar
        self.script_preview_text_input = script_preview_text_input

    def run(self):
        progress_segment = self.script_progress_bar.max / len(self.commands)
        self.script_preview_text_input.text = ''

        for command in self.commands:
            address = int(command[1], 16)

            write_value = command[3]
            if write_value.replace("0x", '').__len__() == 1:
                write_value = '0' + write_value.replace("0x", '')

            int_addr_msb = address >> 8
            int_addr_lsb = address & 0xFF
            int_data = int(write_value, 16)
            self.dll.i2c_write(self.slave, int_addr_msb, int_addr_lsb, int_data)

            self.script_progress_bar.value += progress_segment

            self.script_preview_text_input.text += self.script_log_label.text + '\n'

        self.script_log_label.text = "End Write"
        self.script_progress_bar.value = 0
