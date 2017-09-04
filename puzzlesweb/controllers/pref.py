# -*- coding: utf-8 -*-
"""User preferences controller module"""

import datetime
import unicodedata
from tg import expose, redirect, flash, url, request, response, require
from tg import predicates

from puzzlesweb.lib.base import BaseController
from puzzlesweb.model import DBSession, User
from puzzlesweb.model.auth import PrivacySetting

class PreferencesController(BaseController):
    allow_only = predicates.not_anonymous()

    @expose('puzzlesweb.templates.pref')
    def index(self, display_name=None, privacy=None):
        user = request.identity['user']

        def set_display_name(display_name):
            display_name = unicodedata.normalize('NFC', display_name).strip()
            if len(display_name) < 3:
                flash('Your selected display name is too short.', 'error')
                return
            if len(display_name) > 45:
                flash('Your selected display name is too long. Please limit your name to 45 characters.', 'error')
                return

            sep_used = 0
            for c in display_name:
                if c in ('"', "'", '.'):
                    continue
                cc = unicodedata.category(c)
                if cc[0] in ('L', 'M'):
                    continue
                if cc in ('Pd', 'Nl', 'Pi', 'Pf'):
                    continue
                if cc == 'Zs':
                    sep_used += 1
                    continue
                flash(
                    """The character "{}" is not allowed to be automatically
                       set in a display name. If this is in your real name,
                       please contact a website admin to set this manually.
                    """.format(unicodedata.name(c)), 'error'
                )
                return

            if not sep_used:
                flash("""Please use both your first and last name. If you have
                         only one name, please contact a website admin to set
                         this manually.""", 'error')
                return

            user.display_name = display_name

        if display_name is not None:
            set_display_name(display_name)

        if privacy in ('always', 'auth', 'admin'):
            user.privacy = PrivacySetting[privacy]

        return dict(page='pref')
