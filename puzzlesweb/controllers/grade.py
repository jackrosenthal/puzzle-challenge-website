# -*- coding: utf-8 -*-
"""Grading interface controller module"""

import datetime
from tg import expose, redirect, validate, flash, url, request, response, require
from tg import predicates
from depot.manager import DepotManager

from puzzlesweb.lib.base import BaseController
from puzzlesweb.model import DBSession, Puzzle, User, Competition, Answer, Submission
from puzzlesweb.model.puzzlecomp import AnswerGrade

class GradeAnswersController(BaseController):
    allow_only = predicates.has_permission('grader')

    @expose('puzzlesweb.templates.gradepuzzle')
    def puzzle(self, puzzle_id):

        puzzle = DBSession.query(Puzzle)\
                .filter(Puzzle.id == puzzle_id)\
                .one()

        answers = DBSession.query(Answer)\
                .filter(Answer.puzzle_id == puzzle_id)

        unknown = answers.filter(Answer.grade == AnswerGrade.unknown)
        correct = answers.filter(Answer.grade == AnswerGrade.correct)
        incorrect = answers.filter(Answer.grade == AnswerGrade.incorrect)

        return dict(puzzle=puzzle, unknown=unknown, correct=correct, incorrect=incorrect)

    @expose()
    def mark(self, answer_id, what):
        answer = DBSession.query(Answer).filter(Answer.id == answer_id).one()
        answer.grade = AnswerGrade[what]
        redirect(url('/grade/puzzle/{}'.format(answer.puzzle_id)))

    @expose('puzzlesweb.templates.gradehome')
    def index(self):
        competitions = DBSession.query(Competition).order_by(Competition.open_time.desc())

        return dict(competitions=competitions)

