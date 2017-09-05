# -*- coding: utf-8 -*-
import enum
import tg
import datetime
from sqlalchemy import *
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, Unicode, DateTime, LargeBinary, Enum
from depot.fields.sqlalchemy import UploadedFileField
from sqlalchemy.orm import relationship, backref

from puzzlesweb.model import DeclarativeBase, metadata, DBSession
import puzzlesweb.model.auth

class AnswerGrade(enum.Enum):
    unknown = 0
    correct = 1
    incorrect = 2

    def __repr__(self):
        return self.name

class Puzzle(DeclarativeBase):
    __tablename__ = 'puzzles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(Integer, nullable=False)
    name = Column(Unicode(255), nullable=False)
    file = Column(UploadedFileField)

    # Plain text solution to be shown after the competition ends
    solution = Column(Unicode, nullable=True)

    author_id = Column(Integer, ForeignKey("tg_user.user_id"), nullable=True)
    author = relationship("puzzlesweb.model.auth.User", back_populates="puzzles")

    competition_id = Column(Integer, ForeignKey('competitions.id'), nullable=False)
    competition = relationship("Competition", back_populates="puzzles")

    answers = relationship("Answer", back_populates="puzzle")

    def __repr__(self):
        return self.name

    @property
    def download_url(self):
        return tg.url('/puzzles/download/{}'.format(self.id))

    @property
    def submit_url(self):
        return tg.url('/puzzles/submit/{}'.format(self.id))

    @property
    def solution_url(self):
        return self.solution and tg.url('/puzzles/solution/{}'.format(self.id))

    def count_need_grading(self):
        return DBSession.query(Answer)\
                .filter(Answer.puzzle_id == self.id)\
                .filter(Answer.grade == AnswerGrade.unknown)\
                .count()

class Competition(DeclarativeBase):
    __tablename__ = 'competitions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(255), nullable=False)
    prize = Column(Unicode, nullable=True)
    open_time = Column(DateTime, nullable=False)
    close_time = Column(DateTime, nullable=False)

    puzzles = relationship("Puzzle", order_by=Puzzle.number, back_populates="competition")

    @property
    def active(self):
        return self.open_time <= datetime.datetime.now() < self.close_time

    @property
    def closed(self):
        return datetime.datetime.now() >= self.close_time

class Submission(DeclarativeBase):
    __tablename__ = 'submissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, nullable=False)

    user_id = Column(Integer, ForeignKey("tg_user.user_id"), nullable=False)
    user = relationship("puzzlesweb.model.auth.User", back_populates="submissions")

    answer_id = Column(Integer, ForeignKey("answers.id"), nullable=False)
    answer = relationship("Answer", back_populates="submissions")

    @property
    def minutes(self):
        return int((self.time - self.answer.puzzle.competition.open_time).total_seconds() // 60)

class Answer(DeclarativeBase):
    __tablename__ = 'answers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Unicode)
    grade = Column(Enum(AnswerGrade), nullable=False, default=AnswerGrade.unknown)

    puzzle_id = Column(Integer, ForeignKey("puzzles.id"), nullable=False)
    puzzle = relationship("Puzzle", back_populates="answers")

    submissions = relationship("Submission", back_populates="answer", order_by=Submission.time.desc())

    def __repr__(self):
        return "Answer(text='{}', puzzle={}, grade={})".format(self.text, repr(self.puzzle), repr(self.grade))

__all__ = ['Competition', 'Puzzle', 'Answer', 'AnswerGrade', 'Submission']
