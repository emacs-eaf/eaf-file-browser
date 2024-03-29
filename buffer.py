#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2018 Andy Stewart
#
# Author:     Andy Stewart <lazycat.manatee@gmail.com>
# Maintainer: Andy Stewart <lazycat.manatee@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import signal
import subprocess
import tempfile
import uuid

from core.buffer import Buffer
from core.utils import *
from core.utils import get_free_port, get_local_ip, message_to_emacs
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class AppBuffer(Buffer):
    def __init__(self, buffer_id, url, argument):
        Buffer.__init__(self, buffer_id, url, argument, False)

        self.add_widget(FileUploaderWidget(url, self.theme_background_color, self.theme_foreground_color))

    def destroy_buffer(self):
        os.kill(self.buffer_widget.background_process.pid, signal.SIGKILL)

        super().destroy_buffer()

        message_to_emacs("Stop: {0} -> {1}".format(self.buffer_widget.address, self.buffer_widget.url))

    @interactive
    def update_theme(self):
        super().update_theme()

        self.buffer_widget.change_color(self.theme_background_color, self.theme_foreground_color)

class FileUploaderWidget(QWidget):
    def __init__(self, url, background_color, foreground_color):
        QWidget.__init__(self)

        self.setStyleSheet("background-color: transparent;")

        self.url = os.path.expanduser(url)

        self.file_name_font = QFont()
        self.file_name_font.setPointSize(48)

        self.file_name_label = QLabel()
        self.file_name_label.setText("Your smartphone file will be shared at\n{0}".format(url))
        self.file_name_label.setFont(self.file_name_font)
        self.file_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_name_label.setStyleSheet("color: {}".format(foreground_color))

        self.qrcode_label = QLabel()

        self.notify_font = QFont()
        self.notify_font.setPointSize(24)
        self.notify_label = QLabel()
        self.notify_label.setText("Scan the QR code above to upload a file from your smartphone.\nMake sure the smartphone is connected to the same WiFi network as this computer.")
        self.notify_label.setFont(self.notify_font)
        self.notify_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.notify_label.setStyleSheet("color: {}".format(foreground_color))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(self.qrcode_label, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(self.file_name_label, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(40)
        layout.addWidget(self.notify_label, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        self.port = get_free_port()
        self.local_ip = get_local_ip()
        self.address = "http://{0}:{1}".format(self.local_ip, self.port)

        self.qrcode_label.setPixmap(get_qrcode_pixmap(self.address))

        tmp_db_file = os.path.join(tempfile.gettempdir(), "filebrowser-" + uuid.uuid1().hex + ".db")
        self.background_process = subprocess.Popen(
            "filebrowser --noauth -d {0} --address {1} -p {2}".format(tmp_db_file, self.local_ip, self.port),
            cwd=self.url,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True)
        message_to_emacs("Start: {0} -> {1}".format(self.address, self.url))

    def change_color(self, background_color, foreground_color):
        self.setStyleSheet("background-color: {};".format(background_color))
        self.file_name_label.setStyleSheet("color: {}".format(foreground_color))
        self.notify_label.setStyleSheet("color: {}".format(foreground_color))
