#!/usr/bin/env python
# encoding: utf-8

import threading
import subprocess
from abc import *

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
        pass

    def start(self):
        self._th = threading.Thread(target=self._work)
        self._th.start()

class SubProc(ProcBase):
    def __init__(self, call, done_queue=None, cb_queue=None, callback=None):
        super(SubProc, self).__init__(
                done_queue=done_queue, cb_queue=cb_queue, callback=callback)
        self._inp = None
        self._outp = None
        self._proc = None

        self.context = None
        self.call = call
        self.out = None
        self.err = None
        self.retcode = None

    def _work(self):
        if self._inp != None:
            inp = subprocess.PIPE
        else:
            inp = None
        self._proc = subprocess.Popen(self.call, shell=True, stdin=inp,
            stdout=subprocess.PIPE)

        (self.out, self.err) = self._proc.communicate(self._inp)
        self.retcode = self._proc.returncode

        if self.cb_queue and self._callback:
            self.cb_queue.put((self._callback, (self,)))
        self.done_queue.put(self)

    def kill(self):
        if self._proc and self._proc.returncode is None:
            self._proc.kill()

    def start(self, inp, context=None):
        self.kill()
        self.context = context
        self._inp = inp
        super(SubProc, self).start()

    def done(self):
        pass

class VimProc(SubProc):
    def __init__(self, call, vim_cb=None):
        super(VimProc, self).__init__(call, callback=VimProc.vim_call)
        self._vim_cb = vim_cb

    def vim_call(self):
        if self._vim_cb:
            import vim
            vim.command(self._vim_cb)

