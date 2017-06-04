import string
import qrcode

qr = qrcode.QRCode()

qr.add_data(string.letters*13)
qr.make()
print(qr.version)
