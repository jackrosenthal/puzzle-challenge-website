# -*- coding: utf-8 -*-
"""Competitions controller module"""

import datetime
from tg import expose, redirect, validate, flash, url, request, response, require, abort
from tg import predicates
from puzzlesweb.lib.helpers import log

from puzzlesweb.lib.base import BaseController
from puzzlesweb.model import DBSession, Puzzle, User, Competition, Answer, Submission
from puzzlesweb.model.puzzlecomp import AnswerGrade
from collections import namedtuple

class CompetitonsController(BaseController):

    @expose('puzzlesweb.templates.competitionslist')
    def index(self):
        competitions = DBSession.query(Competition)\
                            .filter(Competition.close_time < datetime.datetime.now())\
                            .order_by(Competition.open_time.desc())\
                            .all()
        return dict(page='competitions', competitions=competitions, title='Previous Competitions')

    @expose('puzzlesweb.templates.competitionslist')
    @require(predicates.has_permission('admin'))
    def preview(self):
        competitions = DBSession.query(Competition)\
                            .filter(Competition.close_time > datetime.datetime.now())\
                            .order_by(Competition.open_time.desc())\
                            .all()

        if len(competitions) == 1:
            # There's only one thing to click on here, lets save the user a click
            redirect(url('/competitions/leaderboard/{}'.format(competitions[0].id)))

        return dict(page='preview', competitions=competitions, title='Preview Leaderboard')

    @expose('puzzlesweb.templates.leaderboard')
    def leaderboard(self, competition_id):
        competition = DBSession.query(Competition)\
                            .filter(Competition.id == competition_id)\
                            .one()
        
        # This might change if we are an admin and it's a preview
        page = 'competitions'

        # Can view unreleased leaderboards only if admin
        if competition.close_time >= datetime.datetime.now():
            if predicates.has_permission('admin'):
                flash('This competition has not ended yet, so this is just a preview only visible to admin.', 'warning')
                page = 'preview'
            else:
                abort(403)

        # Have we not finished grading yet? OK for admin to view, everyone else gets a message.
        if any(p.count_need_grading() for p in competition.puzzles):
            if predicates.has_permission('admin'):
                if page != 'preview':
                    flash('Not all answers have been graded, so this is just a preview only visible to admin.', 'warning')
                page = 'preview'
            else:
                flash('Grading is in progress. Hang tight!', 'info')
                redirect(url('/competitions'))

        # Build the leaderboard!
        # User -> dict of (puzzle -> final and correct submission times for that user)
        subs = {}

        q = (DBSession
                .query(User, Puzzle.id, Answer.grade, Submission.time)
                .filter(Puzzle.competition_id == competition_id)
                .filter(Answer.puzzle_id == Puzzle.id)
                .filter(Submission.answer_id == Answer.id)
                .filter(Submission.user_id == User.user_id)
                .order_by(Submission.time.asc()))

        for u, puzzle_id, grade, time in q:
            if u not in subs.keys():
                subs[u] = {}
            if grade == AnswerGrade.correct:
                # Keep the time
                subs[u][puzzle_id] = time
            elif puzzle_id in subs[u].keys():
                # Delete the correct answer
                del subs[u][puzzle_id]
            # delete the user's entry if they are down to zero now
            if not subs[u]:
                del subs[u]

        # sum of minutes for each user
        minutes = {}
        for u, prows in subs.items():
            minutes[u] = sum(int((itm - competition.open_time).total_seconds() // 60) for itm in prows.values())

        # build the table rows
        LeaderTableRow = namedtuple('LeaderTableRow', 'user, rank, puzzletimes, solved, minutes')
        last_user = None
        rows = []
        for u, prows in sorted(subs.items(), key=lambda kv: (-len(kv[1]), minutes[kv[0]])):
            # don't adjust rank on peleton finish
            if not last_user or minutes[last_user] + 5 < minutes[u] or len(subs[u]) < len(subs[last_user]):
                rank = len(rows) + 1
            rows.append(
                LeaderTableRow(
                    user=u,
                    rank=rank,
                    puzzletimes=tuple(
                        int((subs[u][puzz.id] - competition.open_time).total_seconds() // 60)
                        if puzz.id in subs[u].keys() else ''
                        for puzz in competition.puzzles),
                    solved=len(prows),
                    minutes=minutes[u]
                )
            )
            last_user = u
        
        return dict(page=page, competition=competition, rows=rows, full_width=True)
