
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

command! -nargs=* Amake py MAKER.make("<args>")
command! -nargs=* Remake py MAKER.remake("<args>")
