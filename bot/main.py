#!/usr/bin/env python

import schedule
from wallet import *
from models import Invoice

#https://github.com/tmrwapp/breez-sdk-cli-wallet/


@bot.command("start")
def start_command(handler):
    chat = bbot.Chat(bot, handler.chat)
    chat.send(f"🖖Breez(er) Bot, Welcome"
              f"\n\nPythonic non custodial breez sdk implementation."
              f"\n\nCommands summary"
              f"\n/invoice <AMOUNT> <DESCRIPTION> 👉 Issue an invoice"
              f"\n/pay <BOLT11> 👉 Pay an invoice"
              f"\n/info Get status and balance"
              f"\n/start This message",syntax="markdown")
    nodeinfo = cli.get_info()
    if nodeinfo.channels_balance_msat==0:
        chat.send(f"🤚Please note:"
              f"\n\nYour balance in channels is actually: {nodeinfo.channels_balance_msat/1000} Sats"
              f"\n\nA minimum amount of at least 3000 Sats is necessary to start. Just issue a Lightning invoice and get it paid from an external source.",syntax="markdown")


@bot.command("pay")
def pay_command(handler):
    # result Payment(id=45400f9d18edddc93fa6506878bfea1e23956f20d1408536c6bdfb073e443be2, payment_type=PaymentType.SENT, payment_time=1694239982,
    # amount_msat=1000, fee_msat=1004, pending=False, description=f,
    # details=PaymentDetails.LN(data=LnPaymentDetails(payment_hash=45400f9d18edddc93fa6506878bfea1e23956f20d1408536c6bdfb073e443be2, label=,
    # destination_pubkey=021a7a31f03a9b49807eb18ef03046e264871a1d03cd4cb80d37265499d1b726b9,
    # payment_preimage=9a89e8c0f2c3ea20c7fe8d3a885cb84a084d3872b384cbd94ca1f6e71fb11ca4, keysend=False,
    # bolt11=lnbc10n1pj0cr8qpp5gXXXX, lnurl_success_action=None, lnurl_metadata=None, ln_address=None)))
    chat, message, args, btns = bbot.Chat(bot, handler.chat), bbot.Message(bot, handler), bbot.Args(handler).GetArgs(), bbot.Buttons()
    invoice = args[0]
    # caching the invoice for payment notification #qui
    hset_redis("invoices", invoice, chat.id)
    a = InvoiceData()
    a.set_invoice(invoice,{'user':chat.id,'bolt11':invoice,'amount':0,'memo':'','payment_hash':''})
    please_wait = chat.send(f"*Payment in progress*. This may take several seconds, ❗*please wait..*❗",syntax='markdown')
    result = cli.pay_invoice(invoice)
    print(f"result {result}")
    please_wait.delete()
    a.set_invoice(invoice,{'user':chat.id,'bolt11':invoice,'amount':result.amount_msat/1000,'memo':result.description,'payment_hash':result.details.data.payment_hash})
    chat.send(f"✔️*Invoice payment*"
              f"\n\nStatus: Succeed"
              f"\n\nAmount: {result.amount_msat/1000} Sats"
              f"\nFees: {result.fee_msat/1000} Sats "
              f"\nDescription: {result.description}"
              f"\nPending: {result.pending}"
              f"\nPayment hash: `{result.details.data.payment_hash}` ", syntax="markdown")



@bot.command("invoice")
def invoice_command(handler):
    chat, message, args, btns = bbot.Chat(bot, handler.chat), bbot.Message(bot, handler), bbot.Args(handler).GetArgs(), bbot.Buttons()
    amount = args[0]
    memo = ''
    if len(args) > 1:
        memo = ' '.join(args[1:])
    invoice = cli.get_invoice(f"{amount} {memo}")
    #chat.send(f"⚡️*Lightning Invoice*"
    #                f"\n\nUser: {chat.id}"
    #                f"\nAmount: {amount} Sats"
    #                f"\nMemo: {memo}"
    #                f"\n\n`{invoice}`", syntax="markdown" )
    caption =f"⚡️*Lightning Invoice*" \
             f"\n\nUser: {chat.id}" \
             f"\nAmount: {amount} Sats" \
             f"\nMemo: {memo}" \
             f"\n\n`{invoice}`"
    a = InvoiceData()
    a.set_invoice(invoice,{'user':chat.id,'bolt11':invoice,'amount':amount,'memo':memo,'payment_hash':''})
    qrdir=os.getcwd() + "/qrdir"
    qr=Invoice(invoice,qrdir)
    qrfile=qr.generate()
    chat.send_photo(f"{qrfile}", caption=caption, syntax='markdown')




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
              f"\nChannels balance: {nodeinfo.channels_balance_msat / 1000} Sats"
              )



def events_processor(bot):
    # get events list and make notifications to the user
    invoices_paid = hkeys_redis("invoice.paid")
    for i in invoices_paid:
        print(f"Processing invoice.paid {i}")
        b = EventData()
        result = b.get_event('invoice.paid',i)
        print(f"result {result}")
        invoice = result['bolt11']
        bot.chat(i.decode('utf-8')).send(f"🎉*Payment Received*"
                                         f"\n\nAmount: {result['amount']}"
                                         f"\nMemo: {result['memo']}"
                                         f"\nPayment hash: {result['payment_hash']}", syntax="markdown")
        hdel_redis("invoice.paid", i)

    payment_succeed = hkeys_redis("payment.succeed")
    for i in payment_succeed:
        # result {'user': 200260523, 'bolt11': 'lnbc10n1pjsqXXXX', 'amount': 0, 'memo': '',
        # 'payment_hash': '75e137a0682bd159a678f558a8d5f02c3bc4b258f1ff3e9d9199a12606326a3b',
        # 'invoice': 'lnbc10n1pjsqtejpp5w2gzfa0d2hyj5lsh34r6jafx02pmgdnct80nn2xhp0kvqpkfu5d7'}
        print(f"Processing payment.succeed {i}")
        b = EventData()
        result = b.get_event('payment.succeed',i)
        print(f"result {result}")
        bot.chat(i.decode('utf-8')).send(f"💳*Payment Sent*"
                                         f"\n\nAmount: {result['amount']} Sats"
                                         f"\nMemo: {result['memo']}"
                                         f"\nPayment hash: `{result['payment_hash']}`", syntax="markdown")
        hdel_redis("payment.succeed", i)


schedule.every(30).seconds.do(events_processor, bot)


if __name__ == "__main__":
    threading.Thread(target=bot.infinity_polling, name='bot_infinity_polling', daemon=True).start()
    cli = Wallet()
    while (1):
        schedule.run_pending()
        ev = SDKListener()
        if ev.status.get('success'):
            print (f"status {ev.status}")


