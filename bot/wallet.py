
from commons import *

import bip39
import os
from address_checker import AddressChecker
import breez_sdk
from models import InvoiceData, EventData


class SDKListener(breez_sdk.EventListener):
    def __init__(self):
        self.status={}

    def on_event(self, event):
        # todo: add all events to a rediskey. schedule will message the main events
        if isinstance(event, breez_sdk.BreezEvent.INVOICE_PAID):
            # InvoicePaidDetails(payment_hash=83a5cb998d5cd5ffece15b71f386aadc364e115f95a2d8fd112e5c28a43933bd,
            # bolt11=lnbc10n1pj0nuyjsp52sjnzegXXXX )
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
            # Payment(id=eea8457798c6b9036904a607575d66516b3f9614f61f5da2acfb15c700930b43, payment_type=PaymentType.SENT, payment_time=1694193980,
            # amount_msat=1000, fee_msat=1004, pending=False, description=ricevi 3,
            # details=PaymentDetails.LN(data=LnPaymentDetails(payment_hash=eea8457798c6b9036904a607575d66516b3f9614f61f5da2acfb15c700930b43,
            # label=, destination_pubkey=021a7a31f03a9b49807eb18ef03046e264871a1d03cd4cb80d37265499d1b726b9,
            # payment_preimage=155fc30aca10af5e9646b1174ab236dac2fc130d7d531379a504dad0a027bbb6, keysend=False,
            # bolt11=lnbc10n1pj0kkfkpp5a65y2aucc6usx6gy5cr4whtx294nl9s57c04mg4vlv2uwqynpdpsdqdwf5kxetkdXX, lnurl_success_action=None, lnurl_metadata=None, ln_address=None)))
            print(f"event details {event.details}")
            print(f"[event]: PAYMENT_SUCCEED"
                  f"\n[event]: PAYMENT_ID: {event.details.id}"
                  f"\n[event]: INVOICE\n{event.details.details.data.bolt11}")
            a = InvoiceData()
            result = a.get_invoice(event.details.details.data.bolt11)
            user = result['user']
            if result:
                hdel_redis("invoices", event.details.details.data.bolt11)
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

        # Load settings
        mnemonic = settings['secrets']['phrase']
        invite_code = settings['secrets']['invite_code']
        api_key = settings['secrets']['api_key']
        seed = bip39.phrase_to_seed(mnemonic)

        config = breez_sdk.default_config(breez_sdk.EnvironmentType.PRODUCTION, api_key,
            breez_sdk.NodeConfig.GREENLIGHT(breez_sdk.GreenlightNodeConfig(None, invite_code)))

        config.working_dir = os.getcwd() + "/workdir"

        # Connect to the Breez SDK
        self.sdk_services = breez_sdk.connect(config, seed, SDKListener())


    def get_info(self):
        try:
            node_info = self.sdk_services.node_info()
            lsp_id = self.sdk_services.lsp_id()
            lsp_info = self.sdk_services.fetch_lsp_info(lsp_id)
            print(f"[get_info]\n{node_info}")
            return node_info
        except Exception as error:
            print('Error getting LSP info: ', error)


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
            request = breez_sdk.ReceivePaymentRequest(amount_sats=int(amount), description=memo, preimage=None,
                                                      opening_fee_params=None)
            invoice = self.sdk_services.receive_payment(req_data=request)
            print(f"[get_invoice]: INVOICE\n{invoice.ln_invoice.bolt11}")
            return invoice.ln_invoice.bolt11
        except Exception as error:
            # Handle error
            print('error getting invoice: ', error)


    def pay_invoice(self, args):
        invoice = args.strip()
        try:
            res=self.sdk_services.send_payment(invoice, None)
            return res
        except Exception as error:
            # Handle error
            print('error paying invoice: ', error)
            return False

