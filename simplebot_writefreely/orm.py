from contextlib import contextmanager
from threading import Lock

from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship, sessionmaker


class Base:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


Base = declarative_base(cls=Base)
_Session = sessionmaker()
_lock = Lock()


class Account(Base):
    addr = Column(String(500), primary_key=True)
    host = Column(String(1000), nullable=False)
    token = Column(String(1000), nullable=False)

    blogs = relationship(
        "Blog", backref="account", cascade="all, delete, delete-orphan"
    )


class Blog(Base):
    chat_id = Column(Integer, primary_key=True)
    alias = Column(String(1000), nullable=False)
    account_addr = Column(String(500), ForeignKey("account.addr"), nullable=False)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    with _lock:
        session = _Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()


def init(path: str, debug: bool = False) -> None:
    """Initialize engine."""
    engine = create_engine(path, echo=debug)
    Base.metadata.create_all(engine)
    _Session.configure(bind=engine)
