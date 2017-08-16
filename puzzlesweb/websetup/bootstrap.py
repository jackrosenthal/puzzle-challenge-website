# -*- coding: utf-8 -*-
"""Setup the puzzlesweb application"""
from __future__ import print_function, unicode_literals
import transaction
from puzzlesweb import model

def bootstrap(command, conf, vars):
    """Place any commands to setup puzzlesweb here"""

    # <websetup.bootstrap.before.auth
    from sqlalchemy.exc import IntegrityError
    try:
        jack = model.User(
                user_id=28263,
                user_name="jrosenth",
                display_name="Jack Rosenthal")
        model.DBSession.add(jack)

        tracy = model.User(
                user_id=4829,
                user_name="tcamp",
                display_name="Tracy Camp")
        model.DBSession.add(tracy)

        tom = model.User(
                user_id=364308,
                user_name="twilliams",
                display_name="Tom Williams")
        model.DBSession.add(tom)

        g = model.Group()
        g.group_name = 'admins'
        g.display_name = 'Admins'

        g.users.extend([jack, tracy, tom])
        model.DBSession.add(g)

        p = model.Permission()
        p.permission_name = 'admin'
        p.description = 'This permission gives administrative right'
        p.groups.append(g)
        model.DBSession.add(p)

        p = model.Permission()
        p.permission_name = 'grader'
        p.description = 'This permission gives access to grade submissions'
        p.groups.append(g)
        model.DBSession.add(p)

        model.DBSession.flush()
        transaction.commit()

    except IntegrityError:
        print('Warning, there was a problem adding your auth data, '
              'it may have already been added:')
        import traceback
        print(traceback.format_exc())
        transaction.abort()
        print('Continuing with bootstrapping...')

    # <websetup.bootstrap.after.auth>
