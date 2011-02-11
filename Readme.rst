Async Commands for Vim
======================

The goal of this project is to provide a simple async framework for Vim.

Currently, you can run a subprocess in the background and have Vim run a callback function when it is done. You can also run any Python code in the background, and get a callback when it is done.

There are also commands for running :make in the background:

- :Amake attempts to act exactly the same as :make, but runs in the background
- :Remake attempts to do the same, but will only allow one program to build at a time, so you can call :Remake as often as you like, and only one make process will be launched at a time. Eg. if you run :Remake, then while it's still compiling run :Remake 3 more times, once the first make process is done compiling, the quickfix window will be updated, then make will be called again.
