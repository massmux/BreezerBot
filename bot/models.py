import qrcode
import random
from datetime import datetime
from db import r
import simplejson as json


class InvoiceQR:

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



class InvoiceData:

    def set_invoice(self,invoice,payload):
        #payload = {'user': '','bolt11': '', 'amount': '','memo': '','payment_hash': ''}
        ret = r.hset('invoices', invoice, json.dumps(payload))
        if ret:
            return ret
        else:
            return False

    def get_invoice(self,invoice):
        a = r.hget('invoices', invoice).decode('utf-8')
        if a:
            return json.loads(a)
        else:
            return False


class EventData:

    def set_event(self,event,userid,payload):
        #payload = {'user': '','bolt11': '','amount': '','memo': '','payment_hash': ''}
        ret = r.hset(event, userid, json.dumps(payload))
        if ret:
            return ret
        else:
            return False

    def get_event(self,event,userid):
        a = r.hget(event, userid).decode('utf-8')
        if a:
            return json.loads(a)
        else:
            return False
