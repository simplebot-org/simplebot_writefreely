"""hooks, commands and filters definition."""

import os

import simplebot
import writefreely as wf
from deltachat import Chat, Contact, Message
from pkg_resources import DistributionNotFound, get_distribution
from simplebot.bot import DeltaBot, Replies
from sqlalchemy.exc import NoResultFound

from .orm import Account, Blog, init, session_scope

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "0.0.0.dev0-unknown"


@simplebot.hookimpl
def deltabot_init(bot: DeltaBot) -> None:
    prefix = bot.get("command_prefix", scope=__name__) or ""

    name = f"/{prefix}login"
    desc = "Login to your WriteFreely instance.\nExamples:\n"
    desc += f"{name} https://write.as YourUser YourPassword\n{name} https://write.as YourToken"
    bot.commands.register(func=login, name=name, help=desc)

    name = f"/{prefix}logout"
    desc = "Logout from your WriteFreely instance."
    bot.commands.register(func=logout, name=name, help=desc)


@simplebot.hookimpl
def deltabot_start(bot: DeltaBot) -> None:
    path = os.path.join(os.path.dirname(bot.account.db_path), __name__)
    if not os.path.exists(path):
        os.makedirs(path)
    path = os.path.join(path, "sqlite.db")
    init(f"sqlite:///{path}")


@simplebot.hookimpl
def deltabot_member_removed(bot: DeltaBot, chat: Chat, contact: Contact) -> None:
    if bot.self_contact == contact or len(chat.get_contacts()) <= 1:
        with session_scope() as session:
            blog = session.query(Blog).filter_by(chat_id=chat.id).first()  # noqa
            if blog:
                session.delete(blog)  # noqa


@simplebot.filter
def filter_messages(message: Message, replies: Replies) -> None:
    """All messages sent in a WriteFreely blog group will be published to the respective blog."""
    with session_scope() as session:
        blog = session.query(Blog).filter_by(chat_id=message.chat.id).first()  # noqa
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
        acc = session.query(Account).filter_by(addr=sender.addr).first()  # noqa
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
        group = bot.create_group(f"📝 {blog['title'] or blog['alias']}", [sender])
        acc.blogs.append(Blog(chat_id=group.id, alias=blog["alias"]))
        replies.add(
            text="All messages sent here will be published to blog:\n"
            f"Alias: {blog['alias']}\nDescription: {blog['description']}",
            chat=group,
        )
    with session_scope() as session:
        session.add(acc)  # noqa
    replies.add(text="✔️Logged in")


def logout(bot: DeltaBot, message: Message, replies: Replies) -> None:
    addr = message.get_sender_contact().addr
    try:
        with session_scope() as session:
            acc = session.query(Account).filter_by(addr=addr).one()  # noqa
            host, token = acc.host, acc.token
            chats = [blog.chat_id for blog in acc.blogs]
            session.delete(acc)  # noqa
        wf.client(host=host, token=token).logout()
        for chat_id in chats:
            try:
                bot.get_chat(chat_id).remove_contact(bot.self_contact)
            except ValueError as ex:
                bot.logger.exception(ex)
        replies.add(text="✔️Logged out")
    except NoResultFound:
        replies.add(text="❌ You are not logged in.")
