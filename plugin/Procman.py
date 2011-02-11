import Queue
import os, sys, re
import vim

import Async

DEFAULT_INTERVAL = "500"
INTERVAL_VAR = "g:async_interval"
REMAKE_AW_VAR = "g:async_remake_autowrite"
REMAKE_AW_DEFAULT = "0"

def _opt(var, default):
    if int(vim.eval('exists("%s")' % var)):
        try:
            return vim.eval(var)
        except:
            return default
    else:
        return default

class Maker(object):
    def __init__(self, procman):
        self._making = []
        self._do_remake = []
        self._procman = procman

    def _makeprg(self, args, makeprg=None):
        """ Gets a formatted makeprg. """
        if not makeprg:
            makeprg = vim.eval("expand(&makeprg)")

        makeprg = makeprg.replace("$*", args)

        file_exprs = re.findall(r'(?<!\\)(%(?::.)*)', makeprg)
        for file_expr in sorted(file_exprs, key=lambda s:-len(s)):
            expanded = vim.eval("expand('%s')" % (file_expr,))
            makeprg = makeprg.replace(file_expr, expanded)

        return makeprg

    def _remake_aw(self):
        if int(_opt(REMAKE_AW_VAR, REMAKE_AW_DEFAULT)):
            vim.command("up")

    def _cb_make(self, makeprg):
        if makeprg in self._making:
            self._making.remove(makeprg)
        if makeprg in self._do_remake:
            self._do_remake.remove(makeprg)
            self._remake_aw()
            self._make(makeprg)

    def _make(self, makeprg):
        self._making.append(makeprg)
        tpf = vim.eval("tempname()")

        command = self._procman.vim_shell(makeprg, tpf)
        vim_cb = "cget %s" % tpf
        cb = lambda x: self._cb_make(makeprg)

        self._procman.vim_call(command, vim_cb=vim_cb, callback=cb)

    def make(self, args="", makeprg=None, autowrite=None, cb=None):
        """ Attempts to emulate a vim :make in the background. """
        if autowrite or (autowrite is None and int(vim.eval("&autowrite"))):
            vim.command("up")

        makeprg = self._makeprg(args, makeprg)
        self._make(makeprg)

    def remake(self, args="", makeprg=None):
        """ Attempts to run make if it's not already running, otherwise
        it waits until make finishes and runs it again.
        """
        makeprg = self._makeprg(args, makeprg)

        if makeprg in self._making:
            if makeprg not in self._do_remake:
                self._do_remake.append(makeprg)
        else:
            self._remake_aw()
            self._make(makeprg)

class ProcMan(object):
    def __init__(self, use_idles=True):
        self._cb_queue = Queue.Queue()
        self._done_queue = Queue.Queue()
        self.procs = []
        self._norm = None
        self.sav_update()
        self.set_aus(use_idles)
        self._do_exit = False

    def set_update(self, new_update):
        vim.command("set updatetime=%d" % int(new_update))

    def sav_update(self):
        self._norm = vim.eval("&updatetime")

    @property
    def wait_update(self):
        return int(_opt(INTERVAL_VAR, DEFAULT_INTERVAL))

    @property
    def normal_update(self):
        return self._norm

    def add(self, proc):
        """ Adds the given proc to the procs list and sets up the queues. """
        self.set_update(self.wait_update)
        self.procs.append(proc)
        proc.cb_queue = self._cb_queue
        proc.done_queue = self._done_queue

    def vim_shell(self, run, redir=None):
        quo = vim.eval("&shellquote")
        if quo:
            run = run.replace(quo, "\\" + quo)

        command = "%s %s" % (vim.eval("&shell"), vim.eval("&shellcmdflag"))
        command += " " + quo + run + quo

        if redir:
            command += " " + vim.eval("&shellpipe") or "&>"
            command += " " + redir

        return command

    def call(self, proc_call, callback=None, inp="", context=None):
        """ Run a process in the background.
        It runs a subprocess calling 'proc_call', giving it 'inp'.
        When the process returns, and 'check()' is run, 'callback'
        will be run, and handed the Proc object from the run.
        """
        proc = Async.SubProc(proc_call, callback=callback)
        self.add(proc)
        proc.start(inp, context)
        return proc

    def vim_call(self, proc_call, vim_cb=None, inp="", callback=None):
        """ Run a process in the background.
        It runs a subprocess calling 'proc_call', giving it 'inp'.
        When the process returns, and 'check()' is run, 'vim_cb'
        will be run, as a vim command.
        """
        proc = Async.VimProc(proc_call, vim_cb=vim_cb, callback=callback)
        self.add(proc)
        proc.start(inp)
        return proc

    def end_all(self):
        """ Attempts to kill all active processes. """
        for proc in self.procs:
            proc.kill()

    def quit(self):
        self._do_exit = True
        self.end_all()

    def check(self, reidle_mode=None):
        """ Checks to see if any processes have finished, and
        runs their callback. Also resets any idle timers.
        """
        if self._do_exit:
            return

        while not self._cb_queue.empty():
            callback, obj = self._cb_queue.get()
            callback(obj)

        while not self._done_queue.empty():
            proc = self._done_queue.get()
            self.procs.remove(proc)

        if not self.procs:
            # Done procs
            self.set_update(self.normal_update)

        elif reidle_mode and reidle_mode == vim.eval("mode()"):
            # reset timer
            col = int(vim.eval("col('.')"))
            if col <= 1:
                keys = r"\<right>\<left>"
            else:
                keys = r"\<left>\<right>"
            vim.command('call feedkeys("%s", "%s")' % (keys, reidle_mode))

    def set_aus(self, idles=True):
        au_s = ["CursorHold", "CursorMoved", "InsertLeave", "CursorMovedI", "InsertEnter"]
        au_h = [("CursorHoldI", "i"), ("CursorHold", "n")]

        vim.command("au %s * py PROCS.check()" % (",".join(au_s)))
        for au, mode in au_h:
            vim.command('au %s * py PROCS.check("%s")' % (au, mode))
        vim.command('au VimLeavePre,VimLeave * py PROCS.quit()')

    def list_procs(self):
        for proc in self.procs:
            print proc
