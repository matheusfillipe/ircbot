#!/bin/bash
[[ "$1" == "install" ]] && python setup.py install --user 
[[ "$1" == "update" ]] && (rm -r dist; rm -r re_ircbot.egg-info; python3 setup.py sdist bdist_wheel; python3 -m twine upload dist/* --verbose) || echo "Use update or install"
