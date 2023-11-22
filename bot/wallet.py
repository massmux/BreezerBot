
from commons import *

import bip39
import os
from address_checker import AddressChecker
import breez_sdk
from models import InvoiceData, EventData
import time
from breez_sdk import LnUrlCallbackStatus, LnUrlPayResult, PaymentTypeFilter, ListPaymentsRequest
from datetime import datetime


class SDKListener(breez_sdk.EventListener):
    def __init__(self):
        self.status={}

    def on_event(self, event):
        # todo: add all events to a rediskey. schedule will message the main events
        if isinstance(event, breez_sdk.BreezEvent.INVOICE_PAID):
            # BreezEvent.INVOICE_PAID(details=InvoicePaidDetails(payment_hash=7df58bbaef596428f4806738b5a5c5471107a02ccd519c0230f17045d2b37a6e,
            # bolt11=lnbc220n1pj4ujnXXXX))
            print(event)
            print(f"[event]: INVOICE_PAID"
                  f"\n[event]: PAYMENT_HASH: {event.details.payment_hash}"
                  f"\n[event]: INVOICE\n{event.details.bolt11}")
            a = InvoiceData()
            result = a.get_invoice(event.details.bolt11)
            user = result['user']
            if result:
                hdel_redis("invoices", event.details.bolt11)
                result['payment_hash'] = event.details.payment_hash
                b = EventData()
                b.set_event('invoice.paid', user, result)
        elif isinstance(event, breez_sdk.BreezEvent.PAYMENT_SUCCEED):
            # event:
            # BreezEvent.PAYMENT_SUCCEED(details=Payment(id=b552652f8f90b7c9e84b9d6966858dad42eb54193c2940e20fb8ac5f9c13921d,
            # payment_type=PaymentType.SENT, payment_time=1700593498, amount_msat=12000, fee_msat=2692, status=PaymentStatus.COMPLETE,
            # description=memo2 (@SatsMobiBot),
            # details=PaymentDetails.LN(data=LnPaymentDetails(payment_hash=b552652f8f90b7c9e84b9d6966858dad42eb54193c2940e20fb8ac5f9c13921d,
            # label=, destination_pubkey=021a7a31f03a9b49807eb18ef03046e264871a1d03cd4cb80d37265499d1b726b9,
            # payment_preimage=0a5b103353abd904907adc722977cd911f86dd345b30bffbc447650d3f9daa4a, keysend=False,
            # bolt11=lnbc120n1pj4eleXXX, lnurl_success_action=None, lnurl_metadata=None, ln_address=None, lnurl_withdraw_endpoint=None, swap_info=None))))
            print(f"[event]: PAYMENT_SUCCEED"
                  f"\n[event]: PAYMENT_ID: {event.details.id}"
                  f"\n[event]: INVOICE\n{event.details.details.data.bolt11}")
            a = InvoiceData()
            result = a.get_invoice(event.details.details.data.bolt11)
            user = result['user']
            if result:
                hdel_redis("invoices", event.details.details.data.bolt11)
                result['invoice'] = event.details.details.data.bolt11
                result['invoice'] = event.details.details.data.bolt11
                result['payment_hash'] = event.details.details.data.payment_hash
                result['amount'] = event.details.amount_msat/1000
                result['memo'] = event.details.description
                b = EventData()
                b.set_event('payment.succeed', user, result)
        elif isinstance(event, breez_sdk.BreezEvent.PAYMENT_FAILED):
            print(f"event details {event.details}")


class Wallet(AddressChecker):
    def __init__(self):
        super().__init__()
        AddressChecker.__init__(self)
        self.sdk_services = None
        self.userid = ""


    def get_sdk(self,breez_sdk_api_key: str,
                working_dir: str,
                invite_code: str,
                mnemonic: str,
                ) -> breez_sdk.BlockingBreezServices:
        # Create working dir
        full_working_dir = os.path.join(os.getcwd(), working_dir)
        #mkdir(full_working_dir)
        # Configure and connect
        seed = breez_sdk.mnemonic_to_seed(mnemonic)
        config = breez_sdk.default_config(breez_sdk.EnvironmentType.PRODUCTION, breez_sdk_api_key,
                                          breez_sdk.NodeConfig.GREENLIGHT(breez_sdk.GreenlightNodeConfig(None, invite_code)))
        config.working_dir = full_working_dir
        sdk_services = breez_sdk.connect(config, seed, SDKListener())
        # Get node info
        node_info = sdk_services.node_info()
        print(node_info)
        return sdk_services

    def open(self,userid):
        # open the wallet for userid
        self.userid = userid
        secret = get_secrets(userid)
        mnemonic = secret['phrase']
        invite_code = secret['invite_code']
        api_key = settings['breez']['api_key']
        seed = bip39.phrase_to_seed(mnemonic)
        self.sdk_services = self.get_sdk(api_key,
                        os.getcwd() + "/workdir/" + str(userid),
                        invite_code,
                        mnemonic,
                        )

    def disconnect(self):
        self.sdk_services.disconnect()


    def get_info(self):
        try:
            node_info = self.sdk_services.node_info()
            lsp_id = self.sdk_services.lsp_id()
            lsp_info = self.sdk_services.fetch_lsp_info(lsp_id)
            print(f"[get_info]\n{node_info}")
            return node_info
        except Exception as error:
            print(f"in get_info {type(error).__name__} was raised: {error}")


    def get_invoice(self, arg):
        memo = ''
        amount = arg.split(' ')[0]
        if not amount.isdigit() or int(amount) < 0:
            print('Amount must be a non-negative integer')
            return
        if len(arg.split(' ')) > 1:
            memo = ' '.join(arg.split(' ')[1:])
        print(f'Getting invoice for amount: {amount}')
        print(f"[get_invoice]: {amount}")
        if memo:
            print(f"[get_invoice]: {memo}")
        try:
            request = breez_sdk.ReceivePaymentRequest(amount_msat=int(amount)*1000, description=memo, preimage=None,
                                                      opening_fee_params=None)
            invoice= self.sdk_services.receive_payment(req=request)
            print(f"[get_invoice]: INVOICE\n{invoice.ln_invoice.bolt11}")
            return invoice.ln_invoice.bolt11
        except Exception as error:
            # Handle error
            print(f"in get_invoice {type(error).__name__} was raised: {error}")

    def transactions(self,howmany):
        # Payment(id=9b8da9e9dd58451faeb6e784bb935f97d1233a1235e9d6d217e20eeefe36b3e9, payment_type=PaymentType.SENT,
        # payment_time=1693313642, amount_msat=500000, fee_msat=2002, status=PaymentStatus.COMPLETE,
        # description=ritorno, details=PaymentDetails.LN(data=LnPaymentDetails(payment_hash=9b8da9e9dd58451faeb6e784bb935f97d1233a1235e9d6d217e20eeefe36b3e9,
        # label=, destination_pubkey=021a7a31f03a9XXXX,
        # payment_preimage=57c85dc5b3e375242XXXX, keysend=False,
        # bolt11=lnbc5u1pjwm6jXXXX, lnurl_success_action=None, lnurl_metadata=None, ln_address=None, lnurl_withdraw_endpoint=None)))
        now = int(time.time())
        payments = self.sdk_services.list_payments(ListPaymentsRequest(PaymentTypeFilter.ALL, 0, now))
        res,cont = [],0
        # todo: order the list with the newest as first
        for i in payments:
            print(f"type: {i.payment_type} amount: {i.amount_msat}")
            cur_datetime = datetime.fromtimestamp(i.payment_time)
            res.append({'payment_type' : f"{i.payment_type}",
                        'amount' : i.amount_msat/1000,
                        'fee' : i.fee_msat/1000,
                        'payment_timestamp' : i.payment_time,
                        'payment_time' : cur_datetime.strftime("%m/%d/%Y, %H:%M:%S"),
                        'description' : i.description,
                        })
            cont = cont + 1
            if cont == howmany:
                break
        return res


    def pay_invoice(self, args):
        # result SendPaymentResponse(payment=Payment(id=b614008989b6a87caaa786abb06dd813729f0372db7c38823ef6bc4b10210906,
        # payment_type=PaymentType.SENT, payment_time=1700592065, amount_msat=23000, fee_msat=3629, status=PaymentStatus.COMPLETE,
        # description=test1,
        # details=PaymentDetails.LN(data=LnPaymentDetails(payment_hash=b614008989b6a87caaa786abb06dd813729f0372db7c38823ef6bc4b10210906,
        # label=, destination_pubkey=021a7a31f03a9b49807eb18ef03046e264871a1d03cd4cb80d37265499d1b726b9,
        # payment_preimage=17dd5f706b11d83be20a541a3765f850acd792007bef011e6c99f73083bca70d,
        # keysend=False, bolt11=lnbc230n1pj4eXXXX,
        # lnurl_success_action=None, lnurl_metadata=None, ln_address=None, lnurl_withdraw_endpoint=None, swap_info=None))))
        invoice = args.strip()
        try:
            req = breez_sdk.SendPaymentRequest(bolt11=invoice,amount_msat=None)
            res = self.sdk_services.send_payment(req=req)
            return res
        except Exception as error:
            # Handle error
            print(f"in pay_invoice {type(error).__name__} was raised: {error}")
            return False

