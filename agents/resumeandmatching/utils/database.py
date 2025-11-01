from typing import Optional
from sqlalchemy import create_engine, String, Float, Text, Column
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy import UniqueConstraint

Base = declarative_base()


class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    resume_path = Column(Text, nullable=False)
    score = Column(Float, nullable=False)
    job_id = Column(String, nullable=True)


class JobDescription(Base):
    __tablename__ = "job_descriptions"
    id = Column(String, primary_key=True)  # use Mongo _id string
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    embedding = Column(Text, nullable=True)  # store as JSON string if desired


def get_engine(sqlalchemy_url: str):
    return create_engine(sqlalchemy_url, echo=False, future=True)


def get_session_factory(sqlalchemy_url: str):
    engine = get_engine(sqlalchemy_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False, class_=Session)


def upsert_candidate(session: Session, *, email: str, resume_path: str, score: float, job_id: Optional[str]) -> Candidate:
    obj = session.query(Candidate).filter_by(email=email).one_or_none()
    if obj is None:
        obj = Candidate(id=email, email=email, resume_path=resume_path, score=score, job_id=job_id)
        session.add(obj)
    else:
        obj.resume_path = resume_path
        obj.score = score
        obj.job_id = job_id
    session.commit()
    return obj


def upsert_job_description(session: Session, *, id: str, title: Optional[str], description: Optional[str], embedding: Optional[str]) -> JobDescription:
    obj = session.query(JobDescription).filter_by(id=id).one_or_none()
    if obj is None:
        obj = JobDescription(id=id, title=title, description=description, embedding=embedding)
        session.add(obj)
    else:
        obj.title = title
        obj.description = description
        obj.embedding = embedding
    session.commit()
    return obj


