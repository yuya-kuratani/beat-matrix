import spidev

class MCP3208Reader:
    def __init__(self, bus=0, dev1=0, dev2=1, vref=3.3):
        self.vref = vref
        self.spi = [spidev.SpiDev(), spidev.SpiDev()]
        self.spi[0].open(bus, dev1)
        self.spi[1].open(bus, dev2)
        for s in self.spi:
            s.max_speed_hz = 1_000_000
            s.mode = 0

    def read_adc(self, adc_id, ch):
        cmd = [0x06 | (ch >> 2), (ch & 0x03) << 6, 0x00]
        resp = self.spi[adc_id].xfer2(cmd)
        return ((resp[1] & 0x0F) << 8) | resp[2]

    def adc_to_voltage(self, adc):
        return adc * self.vref / 4095

    def read_all_16(self):
        values = []
        for i in range(16):
            adc_id = 0 if i < 8 else 1
            ch = i % 8
            adc = self.read_adc(adc_id, ch)
            values.append(self.adc_to_voltage(adc))
        return values
