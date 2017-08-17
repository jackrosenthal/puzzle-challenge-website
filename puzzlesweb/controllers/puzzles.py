# -*- coding: utf-8 -*-
"""Puzzles controller module"""

import datetime
from tg import expose, redirect, validate, flash, url, request, response, require, abort
from tg import predicates
from depot.manager import DepotManager

from puzzlesweb.lib.base import BaseController
from puzzlesweb.model import DBSession, Puzzle, User, Competition, Answer, Submission

class PuzzlesController(BaseController):

    @expose('puzzlesweb.templates.psearch')
    def by_author(self, author_id):
        author = DBSession.query(User).filter(User.user_id == author_id).one()
        return self.psearch(Puzzle.author_id == author_id, 'All Puzzles by {}'.format(author))

    @expose('puzzlesweb.templates.psearch')
    def by_competition(self, competition_id):
        competition = DBSession.query(Competition).filter(Competition.id == competition_id).one()
        return self.psearch(Puzzle.competition_id == competition_id, 'All Puzzles from {}'.format(competition.name))

    @expose('puzzlesweb.templates.psearch')
    def by_id(self, puzzle_id):
        return self.psearch(Puzzle.id == puzzle_id, 'Puzzle Listing')

    def psearch(self, pfilter, title):
        puzzles = DBSession.query(Puzzle)\
                .join(Puzzle.competition)\
                .order_by(Competition.open_time.desc(), Puzzle.number)\
                .filter(pfilter)
        
        # Admins can view puzzles which have not opened yet
        if not predicates.has_permission('admin'):
            puzzles = puzzles.filter(Competition.open_time <= datetime.datetime.now())\

        puzzles = puzzles.all()

        return dict(page='puzzles', puzzles=puzzles, title=title)

    @expose()
    def download(self, puzzle_id):
        puzzle = DBSession.query(Puzzle)\
                .filter(Puzzle.id == puzzle_id)\
                .one()

        # Requesting a puzzle that has not opened yet? This requires admin permission.
        if (puzzle.competition.open_time > datetime.datetime.now()
            and not predicates.has_permission('admin')):
            abort(403)

        redirect(DepotManager.url_for(puzzle.file.path))

    @expose('puzzlesweb.templates.solution')
    def solution(self, puzzle_id):
        puzzle = DBSession.query(Puzzle)\
                .filter(Puzzle.id == puzzle_id)\
                .one()

        if not puzzle.solution:
            abort(404)

        # Requesting a puzzle that has not closed yet? This requires admin permission.
        if not puzzle.competition.closed and not predicates.has_permission('admin'):
            abort(403)

        return dict(page='solution', puzzle=puzzle)

    @expose('puzzlesweb.templates.submit')
    @require(predicates.not_anonymous())
    def submit(self, puzzle_id, answer=None):
        user = User.by_user_name(request.identity['repoze.who.userid'])

        puzzle = DBSession.query(Puzzle)\
                .filter(Puzzle.id == puzzle_id)\
                .one()

        old = DBSession.query(Submission)\
                .join(Submission.answer)\
                .join(Answer.puzzle)\
                .filter(User.user_id == user.user_id)\
                .filter(Answer.puzzle_id == puzzle.id)\
                .order_by(Submission.time.desc())\
                .first()

        # Can only submit on active competitions
        if not puzzle.competition.active:
            abort(403)

        # Display form if not submitting
        if not answer:
            return dict(puzzle=puzzle, old=old)

        # Process answer submission
        answer = answer.strip()
        dbans = DBSession.query(Answer)\
                .filter(Answer.text == answer)\
                .filter(Answer.puzzle_id == puzzle_id)\
                .one_or_none()

        if not dbans:
            # New answer... add it!
            dbans = Answer(text=answer, puzzle_id=puzzle_id)
            DBSession.add(dbans)

        sub = Submission(answer=dbans, user=user, time=datetime.datetime.now())
        DBSession.add(sub)

        flash('Your answer for "{}" has been recorded!'.format(puzzle.name), 'ok')
        redirect(url('/'))

