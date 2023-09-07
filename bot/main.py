#!/usr/bin/env python

from commons import *
import bip39
from address_checker import AddressChecker
import breez_sdk
from secrets_loader import load_secrets
import schedule

#https://github.com/tmrwapp/breez-sdk-cli-wallet/



class SDKListener(breez_sdk.EventListener):
    def __init__(self):
        self.status={}

    def on_event(self, event):
        if isinstance(event, breez_sdk.BreezEvent.INVOICE_PAID):
            # InvoicePaidDetails(payment_hash=83a5cb998d5cd5ffece15b71f386aadc364e115f95a2d8fd112e5c28a43933bd,
            # bolt11=lnbc10n1pj0nuyjsp52sjnzegXXXX )
            print(event.details.payment_hash)
            print(f"[event]: INVOICE_PAID")
            print(f"[event]: PAYMENT_HASH: {event.details.payment_hash}")
            print(f"[event]: INVOICE\n{event.details.bolt11}")
            user = hget_redis("invoices", event.details.bolt11)
            if user:
                hdel_redis("invoices", event.details.bolt11)
                hset_redis("invoice.paid", user, event.details.bolt11)
        elif isinstance(event, breez_sdk.BreezEvent.PAYMENT_SUCCEED):
            print(event.details)
        elif isinstance(event, breez_sdk.BreezEvent.PAYMENT_FAILED):
            print(event.details)
        elif isinstance(event, breez_sdk.BreezEvent.PAYMENT_SUCCEED):
            print(event.details)


class Wallet(AddressChecker):
    def __init__(self):
        super().__init__()
        AddressChecker.__init__(self)

        # Load secrets from file
        secrets = load_secrets('secrets.txt')

        # Create the default config
        mnemonic = secrets['phrase']
        invite_code = secrets['invite_code']
        api_key = secrets['api_key']
        seed = bip39.phrase_to_seed(mnemonic)

        config = breez_sdk.default_config(breez_sdk.EnvironmentType.PRODUCTION, api_key,
            breez_sdk.NodeConfig.GREENLIGHT(breez_sdk.GreenlightNodeConfig(None, invite_code)))

        # Customize the config object according to your needs
        config.working_dir = os.getcwd()+"/workdir"

        # Connect to the Breez SDK make it ready for use
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


    def do_get_invoice(self, arg):
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

    def do_pay_invoice(self, args):
        invoice = args.strip()
        try:
            self.sdk_services.send_payment(invoice, None)
        except Exception as error:
            # Handle error
            print('error paying invoice: ', error)



@bot.command("pay")
def pay_command(handler):
    chat, message, args, btns = bbot.Chat(bot, handler.chat), bbot.Message(bot, handler), bbot.Args(handler).GetArgs(), bbot.Buttons()
    invoice = args[0]
    result = cli.do_pay_invoice(invoice)


@bot.command("invoice")
def invoice_command(handler):
    chat, message, args, btns = bbot.Chat(bot, handler.chat), bbot.Message(bot, handler), bbot.Args(handler).GetArgs(), bbot.Buttons()
    amount = args[0]
    memo = ''
    if len(args) > 1:
        memo = ' '.join(args[1:])
    invoice = cli.do_get_invoice(f"{amount} {memo}")
    chat.send(f"✔️*Lightning Invoice*"
                    f"\n\nUser: {chat.id}"
                    f"\nAmount: {amount} Sats"
                    f"\nMemo: {memo}"
                    f"\n\n`{invoice}`", syntax="markdown" )
    # caching the invoice for payment notification
    hset_redis("invoices", invoice,chat.id)


@bot.command("info")
def info_command(handler):
    chat, message, args, btns = bbot.Chat(bot, handler.chat), bbot.Message(bot, handler), bbot.Args(handler).GetArgs(), bbot.Buttons()
    # NodeState(id=02c6aaf466946ce43fcf56ecf6949127108c8b368c4af5c1ebe2d632c9eb5d4aa2, block_height=806614, channels_balance_msat=2858990,
    # onchain_balance_msat=0, utxos=[], max_payable_msat=2858990, max_receivable_msat=3997141010, max_single_payment_amount_msat=4294967000,
    # max_chan_reserve_msats=0, connected_peers=['02c811e575be2df47d8b48dab3d3f1c9b0f6e16d0d40b5ed78253308fc2bd7170d'], inbound_liquidity_msats=90923010)
    nodeinfo = cli.get_info()
    chat.send(f"✔️*Wallet Info*"
              f"\n\nChannels balance: {nodeinfo.channels_balance_msat/1000} Sats"
              f"\nMax payable: {nodeinfo.max_payable_msat/1000} Sats"
              f"\nMax receivable: {nodeinfo.max_receivable_msat/1000} Sats"
              f"\nOn-chain balance: {nodeinfo.onchain_balance_msat/1000} Sats"
              )


def events_processor(bot):
    # get events list and make notifications to the user
    invoices_paid = hkeys_redis("invoice.paid")
    for i in invoices_paid:
        print(f"Processing invoice.paid {i}")
        invoice = hget_redis('invoice.paid', i)
        bot.chat(i.decode('utf-8')).send(f"✔️*Invoice paid*"
                                         f"\n\n{invoice}", syntax="markdown")
        hdel_redis("invoice.paid", i)


schedule.every(30).seconds.do(events_processor, bot)


if __name__ == "__main__":
    threading.Thread(target=bot.infinity_polling, name='bot_infinity_polling', daemon=True).start()
    cli = Wallet()
    while (1):
        schedule.run_pending()
        #ev = breez_sdk.EventListener()
        ev = SDKListener()
        if ev.status.get('success'):
            print (f"status {ev.status}")


