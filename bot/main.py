#!/usr/bin/env python

import schedule
from wallet import *
from models import InvoiceQR, InvoiceData, EventData, TlgUser
from texts import *

#https://github.com/tmrwapp/breez-sdk-cli-wallet/


@bot.command("version")
def version_command(handler):
    chat = bbot.Chat(bot, handler.chat)
    chat.send("BreezerBot version 0.0.3 build 20231010")


@bot.command("help")
def help_command(handler):
    chat = bbot.Chat(bot, handler.chat)
    chat.send(f"🖖Breezer Bot, Welcome"
              f"\n\nPythonic non custodial Breez SDK implementation."
              f"\n\nCommands summary"
              f"\n/invoice <AMOUNT> <DESCRIPTION> 👉 Issue an invoice"
              f"\n/pay <BOLT11> 👉 Pay an invoice"
              f"\n/info 👉 Get status and balance"
              f"\n/transactions 👉 Get Transactions"
              f"\n/version 👉 Get current version"
              f"\n/help 👉 This message",syntax="markdown")



@bot.command("start")
def start_command(handler):
    chat = bbot.Chat(bot, handler.chat)
    chat.send(f"🖖Breezer Bot, Welcome", syntax="markdown")
    chatuser = get_secrets(chat.id)
    if not chatuser:
        chat.send(f"❌*User not Active*"
                  f"\n\nUser: {chat.id}"
                  f"\nStatus: Not Active"
                  f"\n\nPlease request activation for your user to be able working with this Wallet Bot.", syntax="markdown")


@bot.command("pay")
def pay_command(handler):
    # result Payment(id=ecda441eedbb3ea43e1a36b138e102a676463b3aef2c5e5355ff704a6c9121fe, payment_type=PaymentType.SENT,
    # payment_time=1696309010, amount_msat=12000, fee_msat=2034, status=PaymentStatus.COMPLETE, description=test 0656,
    # details=PaymentDetails.LN(data=LnPaymentDetails(payment_hash=ecda441eedbb3ea43e1a36b138e102a676463b3aef2c5e5355ff704a6c9121fe,
    # label=, destination_pubkey=021a7a31f0XXXX,
    # payment_preimage=00af43338fb2XXXX, keysend=False,
    # bolt11=lnbc100n1pj3hy5epp5q8ydgtx, lnurl_success_action=None, lnurl_metadata=None, ln_address=None, lnurl_withdraw_endpoint=None)))

    # resultdetails PaymentDetails.LN(data=LnPaymentDetails(payment_hash=a75cfe33226f2bf76697c600bc0d0a6afeb145cddb173d0c26040b5cb413fe30,
    # label=, destination_pubkey=021a7a31f03a9XXX,
    # payment_preimage=25494ff83d8e51b36c8XXXX, keysend=False,
    # bolt11=lnbc100n1pj3hy5epp5q8ydgtx, lnurl_success_action=None, lnurl_metadata=None, ln_address=None, lnurl_withdraw_endpoint=None))

    chat, message, args, btns = bbot.Chat(bot, handler.chat), bbot.Message(bot, handler), bbot.Args(handler).GetArgs(), bbot.Buttons()
    invoice = args[0]
    # caching the invoice for payment notification #qui
    hset_redis("invoices", invoice, chat.id)
    a = InvoiceData()
    a.set_invoice(invoice,{'user':chat.id,'bolt11':invoice,'amount':0,'memo':'','payment_hash':''})
    please_wait = chat.send(f"*Payment in progress*. This may take several seconds, ❗*please wait..*❗",syntax='markdown')
    try:
        cli = Wallet()
        cli.open(chat.id)
        result = cli.pay_invoice(invoice)
        print(f"result {result}")
        print(f"resultdetails {result.details}")
        please_wait.delete()
        a.set_invoice(invoice, {'user': chat.id, 'bolt11': invoice, 'amount': result.amount_msat / 1000,'memo': result.description, 'payment_hash': result.details.data.payment_hash})
        chat.send(f"✔️*Invoice payment*"
                  f"\n\nResult: Succeed"
                  f"\n\nAmount: {result.amount_msat / 1000} Sats"
                  f"\nFees: {result.fee_msat / 1000} Sats "
                  f"\nDescription: {result.description}"
                  f"\nStatus: {result.status}"
                  f"\nPayment hash: `{result.details.data.payment_hash}` ", syntax="markdown")
    except Exception as err:
        print(f"{type(err).__name__} was raised: {err}")
        chat.send(GENERIC_ERROR)


@bot.command("invoice")
def invoice_command(handler):
    chat, message, args, btns = bbot.Chat(bot, handler.chat), bbot.Message(bot, handler), bbot.Args(handler).GetArgs(), bbot.Buttons()
    amount = args[0]
    memo = ''
    if len(args) > 1:
        memo = ' '.join(args[1:])
    try:
        please_wait = chat.send(f"*Invoice generation in progress*. This may take several seconds, ❗*please wait..*❗",
                                syntax='markdown')
        cli = Wallet()
        cli.open(chat.id)
        invoice = cli.get_invoice(f"{amount} {memo}")
        caption =f"⚡️*Lightning Invoice*" \
             f"\n\nUser: {chat.id}" \
             f"\nAmount: {amount} Sats" \
             f"\nMemo: {memo}" \
             f"\n\n`{invoice}`"
        a = InvoiceData()
        a.set_invoice(invoice,{'user' : chat.id, 'bolt11' : invoice,'amount' : amount,'memo' : memo,'payment_hash' : ''})
        qrdir = os.getcwd() + "/qrdir"
        qr = InvoiceQR(invoice,qrdir)
        qrfile = qr.generate()
        please_wait.delete()
        chat.send_photo(f"{qrfile}", caption=caption, syntax='markdown')
    except Exception as err:
        print(f"{type(err).__name__} was raised: {err}")
        chat.send(GENERIC_ERROR)


@bot.command("info")
def info_command(handler):
    chat, message, args, btns = bbot.Chat(bot, handler.chat), bbot.Message(bot, handler), bbot.Args(handler).GetArgs(), bbot.Buttons()
    # NodeState(id=02c6aaf466946ce43fcf56ecf69XXXX, block_height=806614, channels_balance_msat=2858990,
    # onchain_balance_msat=0, utxos=[], max_payable_msat=2858990, max_receivable_msat=3997141010, max_single_payment_amount_msat=4294967000,
    # max_chan_reserve_msats=0, connected_peers=['02c811e575be2df47d8b48dab3d3f1c9b0f6e16d0d40b5ed78253308fc2bd7170d'], inbound_liquidity_msats=90923010)
    try:
        cli = Wallet()
        cli.open(chat.id)
        nodeinfo = cli.get_info()
        chat.send(f"💰*Wallet Info*"
              f"\n\nChannels balance: {nodeinfo.channels_balance_msat/1000} Sats"
              f"\nMax payable: {nodeinfo.max_payable_msat/1000} Sats"
              f"\nMax receivable: {nodeinfo.max_receivable_msat/1000} Sats"
              f"\nOn-chain balance: {nodeinfo.onchain_balance_msat/1000} Sats"
              f"\nChannels balance: {nodeinfo.channels_balance_msat / 1000} Sats"
              )
    except Exception as err:
        print(f"{type(err).__name__} was raised: {err}")
        chat.send(GENERIC_ERROR)

@bot.command("transactions")
def transactions_command(handler):
    chat, message, args, btns = bbot.Chat(bot, handler.chat), bbot.Message(bot, handler), bbot.Args(handler).GetArgs(), bbot.Buttons()
    howmany=20
    try:
        cli = Wallet()
        cli.open(chat.id)
        transactions = cli.transactions(howmany)
        msgbody=""
        for i in transactions:
            if i['payment_type']=='PaymentType.SENT':
                msgbody=msgbody + f"\n🔴 {i['payment_time']} -{i['amount']} Sats (fee: {i['fee']}) {i['description']}"
            elif i['payment_type']=='PaymentType.RECEIVED':
                msgbody = msgbody + f"\n🟢 {i['payment_time']} +{i['amount']} Sats (fee: {i['fee']}) {i['description']}"
        chat.send(f"💰*Last {howmany} Transactions*"
              f"\n"
              f"{msgbody}"
              )
    except Exception as err:
        print(f"{type(err).__name__} was raised: {err}")
        chat.send(GENERIC_ERROR)


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
                                         f"\n\nAmount: {result['amount']} Sats"
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


# events processor
schedule.every(30).seconds.do(events_processor, bot)


if __name__ == "__main__":
    threading.Thread(target=bot.infinity_polling, name='bot_infinity_polling', daemon=True).start()
    while (1):
        schedule.run_pending()
        ev = SDKListener()
        if ev.status.get('success'):
            print (f"status {ev.status}")


