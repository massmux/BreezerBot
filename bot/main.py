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
            print(event.details.payment_hash)
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
            #self._print_node_info(node_info)
            #self._print_lsp_info(lsp_info)
            print(node_info)
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
        if memo:
            print(f'With memo: {memo}')
        try:
            request = breez_sdk.ReceivePaymentRequest(amount_sats=int(amount), description=memo, preimage=None,
                                                      opening_fee_params=None)
            invoice = self.sdk_services.receive_payment(req_data=request)
            print('Pay: ', invoice.ln_invoice.bolt11)
            return invoice.ln_invoice.bolt11
        except Exception as error:
            # Handle error
            print('error getting invoice: ', error)




@bot.command("invoice")
def invoice_command(handler):
    chat, message, args, btns = bbot.Chat(bot, handler.chat), bbot.Message(bot, handler), bbot.Args(handler).GetArgs(), bbot.Buttons()
    amount = args[0]
    memo = ''
    if len(args) > 1:
        memo = ' '.join(args[1:])
    invoice = cli.do_get_invoice(f"{amount} {memo}")
    print (invoice)
    chat.send(f"✔️*Lightning Invoice*"
                    f"\n\nUser: {chat.id}"
                    f"\nAmount: {amount} Sats"
                    f"\nMemo: {memo}"
                    f"\n\n`{invoice}`", syntax="markdown" )
    # caching the invoice for payment notification
    hset_redis("invoices", invoice,chat.id)



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


