#! /bin/sh
#
# autobuild.sh
# Copyright (C) 2020 Yongwen Zhuang <zyeoman@163.com>
#
# Distributed under terms of the MIT license.
#


while inotifywait --exclude '(\.git/|.*\.(o|txt|sh|log)$)' -e close_write -r $PWD/ ; do
  $*
done
