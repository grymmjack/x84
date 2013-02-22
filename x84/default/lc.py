""" Last Callers script for x/84, http://github.com/jquast/x84 """
# this also allows viewing of '.plan' attribute string when set by user,
# or 'e'diting a user when executed by sysop -- gosub('profile', user)


def pak():
    """ Press any key prompt. """
    from x84.bbs import echo, getch
    msg_pak = u'PRESS ANY kEY'
    echo(u'\r\n%s ... ' % (msg_pak,))
    getch()
    return


def view_plan(handle):
    """ Display .plan file for handle. """
    from x84.bbs import getterminal, echo, Ansi, get_user
    term = getterminal()
    echo(u'\r\n\r\n')
    echo(Ansi(get_user(handle).get('.plan', u'No Plan.')).wrap(term.width))
    echo(u'\r\n')
    pak()


def dummy_pager(last_callers):
    """ Dummy pager for displaying last callers """
    # pylint: disable=R0914
    #         Too many local variables
    from x84.bbs import getterminal, getsession, echo, getch, ini
    from x84.bbs import LineEditor, Ansi, list_users, get_user, gosub
    session, term = getsession(), getterminal()
    msg_prompt = (
        u'\r\n%sONtiNUE, %stOP, %sON-StOP %siEW .PlAN%s ?\b\b' % (
        term.bold(u'[c]'),
        term.bold(u'[s]'),
        term.bold(u'n'),
        term.bold(u'[v]'),
        u' [e]dit USR' if (
        'sysop' in session.user.groups) else u'',))
    msg_partial = u'PARtiAl MAtChES'
    msg_prompt_handle = u'ViEW .PlAN ::- ENtER hANdlE: '

    redraw()
    echo(u'\r\n\r\n')
    nonstop = False
    row = 10  # after-art,
    for txt in last_callers:
        echo(Ansi(txt).ljust(term.width / 2).center(term.width))
        echo(u'\r\n')
        row += 1
        if ((not nonstop and row > 0 and 0 == (row % (term.height - 3)))
                or (row == len(last_callers) - 1)):
            echo(msg_prompt)
            inp = getch()
            row = 2
            if inp in (u's', u'S', u'q', u'Q', term.KEY_EXIT):
                return
            if inp in (u'v', u'V') or 'sysop' in session.user.groups and (
                    inp in (u'e', u'E')):
                echo(u'\r\n\r\n')
                echo(msg_prompt_handle)
                handle = LineEditor(ini.CFG.getint('nua', 'max_user')).read()
                usrlist = list_users()
                if handle is None or 0 == len(handle.strip()):
                    continue
                handle = handle.strip()
                if handle.lower() in [nick.lower() for nick in list_users()]:
                    user = get_user((nick for nick in usrlist
                                     if nick.lower() == handle.lower()).next())
                    if 'sysop' in session.user.groups and (
                            inp in (u'e', u'E')):
                        gosub('profile', user.handle)
                    else:
                        view_plan(user.handle)
                else:
                    misses = [nick for nick in usrlist.keys()
                              if nick.lower().startswith(handle[:1].lower())]
                    if len(misses) > 0:
                        echo(u'%s:\r\n\r\n%s\r\n' % (msg_partial,
                                                     Ansi(', '.join(misses)).wrap(term.width)))
                    continue
            if inp in ('n', u'N'):
                nonstop = True
            echo(u'\r\n\r\n')
    pak()


def refresh_opts(pager, handle):
    """ Refresh pager border with command keys available. """
    from x84.bbs import getsession, getterminal, get_user, find_user
    session, term = getsession(), getterminal()
    if not handle or not find_user(handle):
        has_plan = 0
    else:
        has_plan = 0 != len(get_user(handle).get('.plan', u'').strip())
    decorate = lambda key, desc: u''.join((
        term.bold(u'('), term.red_underline(key,),
        term.bold(u')'), term.bold_red(desc.split()[0]),
        u' '.join(desc.split()[1:]),
        term.bold_red(u' -'),))
    return pager.border() + pager.footer(u''.join((
        term.bold_red(u'- '),
        decorate(u'Escape/q', 'Uit'),
        decorate(u'v', 'iEW .PLAN') if has_plan else u'',
        decorate(u'e', 'dit USR') if 'sysop' in session.user.groups else u'',
    )))


def get_lightbar(lcallers, lcalls):
    """
    Return UI element for browsing last callers, given ``lcallers`` as
    a list of handles, and parallel array ``lcalls`` as unicode string
    to display for last call of each handle.
    """
    from x84.bbs import getterminal, Lightbar
    term = getterminal()
    assert term.height >= 10 and term.width >= 50
    width = max(min(term.width - 5, 50), 50)
    height = max(min(term.height - 13, 10), 10)
    xloc = (term.width / 2) - (width / 2)
    yloc = term.height - height
    pager = Lightbar(height, width, yloc, xloc)
    pager.glyphs['left-vert'] = pager.glyphs['right-vert'] = u''
    pager.colors['highlight'] = term.red_reverse
    pager.colors['border'] = term.yellow
    pager.xpadding, pager.ypadding = 2, 1
    pager.alignment = 'center'
    pager.update([(lcallers[n], txt,)
                  for (n, txt) in enumerate(lcalls.split('\n'))])
    return pager


def get_art(fname):
    """ Return ansi art center-aligned. """
    from x84.bbs import getterminal
    term = getterminal()
    buf = list()
    width = 0
    for line in open(fname):
        art_line = line.rstrip()[:term.width - 1]
        width = max(len(art_line), width)
        buf.append(art_line)
    return [line.center(width) for line in buf]


def redraw(pager=None):
    """ Returns unicode sequence suitable for redrawing screen. """
    from x84.bbs import getterminal
    import os
    term = getterminal()
    artfile = os.path.join(os.path.dirname(__file__), 'art', 'lc.asc')
    # return banner, artfile contents, pager refreshed
    return u''.join((
        u'\r\n\r\n',
        term.bold_red(u'/'.rjust(
            pager.xloc if pager is not None else term.width / 3)),
        term.red(u'/'), u'l', term.red('AS'),
        term.bold_red('t '), u'C', term.red('A'),
        term.bold_red('ll'), term.red('ERS'),
        u'\r\n',
        u'\r\n'.join(get_art(artfile)),
        u'\r\n',
        u'\r\n' * (pager.height if pager is not None else 0),
        pager.border() if pager is not None else u'',
        pager.refresh() if pager is not None else u'',))


def lc_retrieve():
    """
    Returns tuple of ([nicknames,] u'text'), where 'text' describes in Ansi
    color the last callers to the system, and 'nicknames' is simply a list
    of last callers (for lightbar selection key).
    """
    # pylint: disable=R0914
    #         Too many local variables
    from x84.bbs import list_users, get_user, ini, timeago, getterminal
    import time
    term = getterminal()
    udb = dict()
    for handle in list_users():
        user = get_user(handle)
        udb[(user.lastcall, handle)] = (user.calls, user.location)
    padd_handle = (ini.CFG.getint('nua', 'max_user') + 2)
    padd_origin = (ini.CFG.getint('nua', 'max_location') + 2)
    rstr = u''
    nicks = []
    for ((tm_lc, handle), (_nc, origin)) in (reversed(sorted(udb.items()))):
        is_sysop = 'sysop' in get_user(handle).groups
        rstr += (term.bold_red(u'@') if is_sysop else u''
                 ) + (handle.ljust(padd_handle - (2 if is_sysop else 1)))
        rstr += term.red(origin.ljust(padd_origin))
        rstr += timeago(time.time() - tm_lc)
        rstr += u'\n'
        nicks.append(handle)
    return (nicks, rstr.rstrip())


def main():
    """ Main procedure. """
    from x84.bbs import getsession, getterminal, echo, getch, gosub
    session, term = getsession(), getterminal()
    lcallers, lcalls_txt = lc_retrieve()
    lbr = None
    dirty = True
    handle = None

    if (0 == term.number_of_colors
            or session.user.get('expert', False)):
        echo(redraw(None))
        return dummy_pager(lcalls_txt.split('\n'))

    while lbr is None or not lbr.quit:
        if dirty or lbr is None or session.poll_event('refresh'):
            session.activity = u'Viewing last callers'
            lcallers, lcalls_txt = lc_retrieve()
            pos = lbr.position if lbr is not None else (0, 0)
            lbr = get_lightbar(lcallers, lcalls_txt)
            if pos:
                lbr.position = pos
            echo(redraw(lbr))
            echo(refresh_opts(lbr, handle))
        sel = lbr.selection[0]
        if sel != handle or dirty:
            handle = sel
            echo(refresh_opts(lbr, handle))
            echo(lbr.pos(lbr.yloc + (lbr.height - 1)))
            dirty = False
            continue
        inp = getch(1)
        if inp is not None:
            if inp in (u'v', u'V'):
                view_plan(handle)
                dirty = True
            elif inp in (u'e', u'E') and 'sysop' in session.user.groups:
                gosub('profile', handle)
                dirty = True
            else:
                echo(lbr.process_keystroke(inp))
