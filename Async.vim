
if !has("python")
    finish
endif

python << EOF
import vim

sys.path.append(vim.eval("expand('<sfile>:h')"))

import Procman
import Async


PROCS = Procman.ProcMan()
MAKER = Procman.Maker(PROCS)
EOF

command! -nargs=+ Async py PROCS.call("<args>")
command! -nargs=0 AsyncList py PROCS.list_procs()
command! -nargs=0 AsyncKill py PROCS.end_all()

command! -nargs=* Amake py MAKER.make("<args>")
command! -nargs=* Remake py MAKER.remake("<args>")

" py PROCS.call("cat > test", inp="this is input\n")
" py PROCS.vim_call("cat > test", inp="this is input", vim_cb='echom "done"')
