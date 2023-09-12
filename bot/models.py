import qrcode
import random
from datetime import datetime


class Invoice:

    def __init__(self,invoice,qrdir):
        self.invoice = invoice
        self.qrdir = qrdir

    def get_timeid(self):
        timestamp = datetime.now()
        time_id = "{0}".format(timestamp.strftime('%Y%m%d%H%M%S'))
        return time_id


    def create_id(self):
        time_id = self.get_timeid()
        random_num = random.randint(100000000, 999999999)
        generated_id = f"{time_id}{random_num}"[:12]
        return generated_id


    def generate(self):
        voucher_qrcode = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        voucher_qrcode.add_data(self.invoice)
        voucher_qrcode.make(fit=True)
        voucher_qrcode_img = voucher_qrcode.make_image(fill_color="black", back_color="lightgrey")
        qrfile = self.qrdir + "/"+ self.create_id() + ".png"
        voucher_qrcode_img.save(qrfile)
        return qrfile
