
if !has("python")
    finish
endif

python << EOF
import vim
import Queue
import os, sys

sys.path.append(vim.eval("expand('<sfile>:h')"))

import Async

class ProcMan(object):
    def __init__(self):
        self._cb_queue = Queue.Queue()
        self._done_queue = Queue.Queue()
        self.procs = []
        self._norm = None
        self.sav_update()

    def set_update(self, new_update):
        vim.command("set updatetime=%d" % int(new_update))

    def sav_update(self):
        self._norm = vim.eval("&updatetime")

    @property
    def wait_update(self):
        return 500

    @property
    def normal_update(self):
        return self._norm

    def add(self, proc):
        """ Adds the given proc to the procs list and sets up the queues. """
        self.set_update(self.wait_update)
        self.procs.append(proc)
        proc.cb_queue = self._cb_queue
        proc.done_queue = self._done_queue

    def make(self, command):
        tpf = vim.eval("tempname()")
        self.vim_call("%s &> %s" % (command, tpf), vim_cb="cget %s" % tpf)

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

    def vim_call(self, proc_call, vim_cb=None, inp=""):
        """ Run a process in the background.
        It runs a subprocess calling 'proc_call', giving it 'inp'.
        When the process returns, and 'check()' is run, 'vim_cb'
        will be run, as a vim command.
        """
        proc = Async.VimProc(proc_call, vim_cb=vim_cb)
        self.add(proc)
        proc.start(inp)
        return proc

    def end_all(self):
        """ Attempts to kill all active processes. """
        for proc in self.procs:
            proc.kill()

    def check(self):
        """ Checks to see if any processes have finished, and
        runs their callback.
        """
        while not self._cb_queue.empty():
            callback, args = self._cb_queue.get()
            callback(*args)

        while not self._done_queue.empty():
            proc = self._done_queue.get()
            proc.done()
            self.procs.remove(proc)

        if not self.procs:
            # Done procs
            self.set_update(self.normal_update)
        else:
            # reset timer
            col = vim.eval("col('.')")
            if col == 1:
                vim.command('call feedkeys("\<right>\<left>", "n")')
            else:
                vim.command('call feedkeys("\<left>\<right>", "n")')

PROCS = ProcMan()

au_s = ["CursorHoldI", "CursorHold", "CursorMoved",
        "CursorMovedI", "InsertEnter", "InsertLeave"]
vim.command("au %s * py PROCS.check()" % (",".join(au_s)))

EOF
