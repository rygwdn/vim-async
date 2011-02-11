#!/usr/bin/env python
# encoding: utf-8

import threading
import subprocess
from abc import *
import time

POLL_INTERVAL = 0.1

class ProcBase:
    __metaclass__ = ABCMeta

    def __init__(self, done_queue=None, cb_queue=None, callback=None):
        self._th = None
        self._callback = callback
        self.done_queue = done_queue
        self.cb_queue = cb_queue

    @abstractmethod
    def _work(self):
        pass

    @abstractmethod
    def kill(self):
        pass

    def done(self):
        if self.cb_queue and self._callback:
            self.cb_queue.put((self._callback, self))
        self.done_queue.put(self)

    def start(self):
        self._th = threading.Thread(target=self._work)
        self._th.start()

class SubProc(ProcBase):
    def __init__(self, call, callback=None, **kwargs):
        super(SubProc, self).__init__(callback=callback, **kwargs)
        self._proc = None
        self._alive = True

        self.context = None
        self.call = call
        self.retcode = None

    def _work(self):
        try:
            inp = self._inp
            self._proc = subprocess.Popen(self.call, shell=True,
                    stdout=subprocess.PIPE, # squelch output
                    stderr=subprocess.PIPE,
                    stdin=(inp and subprocess.PIPE or None))

            while self._proc.returncode is None and self._alive:
                self._proc.poll()

                if inp:
                    self._proc.stdin.write(inp)
                    self._proc.stdin.close()
                    inp = None

                time.sleep(POLL_INTERVAL)

            self.retcode = self._proc.returncode

        finally:
            self.done()

    def kill(self):
        if self._proc and self._proc.returncode is None:
            self._alive = False
            self._proc.terminate()
            self._proc.kill()

    def start(self, inp, context=None):
        self.kill()
        self.context = context
        self._inp = inp
        super(SubProc, self).start()

    def __str__(self):
        return "Subprocess: <%s>" % self.call

class VimProc(SubProc):
    def __init__(self, call, vim_cb=None, callback=None, **kwargs):
        super(VimProc, self).__init__(
                call,
                callback=lambda x: self.vim_call(x, vim_cb, callback),
                **kwargs)

    def vim_call(self, x, vim_cb, cb=None):
        """ cb is an extra callback. """
        try:
            if vim_cb:
                import vim
                vim.command(vim_cb)
        finally:
            if cb:
                cb(x)

