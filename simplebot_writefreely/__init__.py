import os

import simplebot
import writefreely as wf
from deltachat import Chat, Contact, Message
from simplebot import DeltaBot
from simplebot.bot import Replies
from sqlalchemy.exc import NoResultFound

from .orm import Account, Blog, init, session_scope

__version__ = "1.0.0"


@simplebot.hookimpl
def deltabot_init(bot: DeltaBot) -> None:
    prefix = bot.get("command_prefix", scope=__name__) or ""

    name = f"/{prefix}login"
    description = f"Login to your WriteFreely instance.\nExamples: {name} https://write.as YourUser YourPassword\n{name} https://write.as YourToken"
    bot.commands.register(func=login, name=name, help=help)

    name = f"/{prefix}logout"
    help = f"Logout from your WriteFreely instance.\nExample: {name}"
    bot.commands.register(func=logout, name=name, help=help)


@simplebot.hookimpl
def deltabot_start(bot: DeltaBot) -> None:
    path = os.path.join(os.path.dirname(bot.account.db_path), __name__)
    if not os.path.exists(path):
        os.makedirs(path)
    path = os.path.join(path, "sqlite.db")
    init(f"sqlite:///{path}")


@simplebot.hookimpl
def deltabot_member_removed(bot: DeltaBot, chat: Chat, contact: Contact) -> None:
    me = bot.self_contact
    if me == contact or len(chat.get_contacts()) <= 1:
        with session_scope() as session:
            blog = session.query(Blog).filter_by(chat_id=chat.id).first()
            if blog:
                session.delete(blog)


@simplebot.filter
def filter_messages(message: Message, replies: Replies) -> None:
    """Process messages sent to WriteFreely groups."""
    with session_scope() as session:
        blog = session.query(Blog).filter_by(chat_id=message.chat.id).first()
        if blog:
            host, token = blog.account.host, blog.account.token
            alias = blog.alias
        else:
            return

    if message.text.startswith("# "):
        args = message.text.split("\n", maxsplit=1)
        title = args.pop(0)[2:] if len(args) == 2 else None
        body = args.pop(0).strip()
    else:
        title, body = None, message.text

    client = wf.client(host=host, token=token)
    post = client.create_post(collection=alias, title=title, body=body)
    replies.add(text=post["collection"]["url"] + post["slug"], quote=message)


def login(bot: DeltaBot, payload: str, message: Message, replies: Replies) -> None:
    sender = message.get_sender_contact()
    with session_scope() as session:
        acc = session.query(Account).filter_by(addr=sender.addr).first()
        if acc:
            replies.add(text="❌ You are already logged in.")
            return

    args = payload.split(maxsplit=2)
    if len(args) == 3:
        client = wf.client(host=args[0], user=args[1], password=args[2])
    else:
        client = wf.client(host=args[0], token=args[1])

    acc = Account(addr=sender.addr, host=client.host, token=client.token)
    for blog in client.get_collections():
        g = bot.create_group("{} [WF]".format(blog["title"] or blog["alias"]), [sender])
        acc.blogs.append(Blog(chat_id=g.id, alias=blog["alias"]))
        replies.add(
            text="All messages sent here will be published to"
            " blog:\nAlias: {}\nDescription: {}".format(
                blog["alias"], blog["description"]
            ),
            chat=g,
        )
    with session_scope() as session:
        session.add(acc)
    replies.add(text="✔️Logged in")


def logout(message: Message, replies: Replies) -> None:
    addr = message.get_sender_contact().addr
    try:
        with session_scope() as session:
            acc = session.query(Account).filter_by(addr=addr).one()
            host, token = acc.host, acc.token
            session.delete(acc)
        wf.client(host=host, token=token).logout()
        replies.add(text="✔️Logged out")
    except NoResultFound:
        replies.add(text="❌ You are not logged in.")
