import cv2
import re
import shutil
import os
from os import listdir
from os.path import isfile, join
from PIL import Image
import numpy as np
import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QLineEdit, QVBoxLayout, QLabel, QFileDialog


class NotesFromLectureMaker:
    def __init__(self):
        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QWidget()
        window.setWindowTitle("NotesFromLectureMaker")
        window.setFixedSize(500, 150)
        layout = QVBoxLayout()

        # Input file
        input_file_row = QHBoxLayout()
        self._input_path_line_edit = QLineEdit()
        input_file_row.addWidget(QLabel("Input path:"))
        input_file_row.addWidget(self._input_path_line_edit)
        btn_select_input_file = QPushButton("Select File")
        input_file_row.addWidget(btn_select_input_file)

        # PDF
        output_file_row = QHBoxLayout()
        self._pdf_path_line_edit = QLineEdit()
        output_file_row.addWidget(QLabel("PDF path:"))
        output_file_row.addWidget(self._pdf_path_line_edit)
        btn_select_output_file = QPushButton("Select File")
        output_file_row.addWidget(btn_select_output_file)

        layout.addLayout(input_file_row)
        layout.addLayout(output_file_row)
        btn_start = QPushButton("Start")
        layout.addWidget(btn_start)
        window.setLayout(layout)

        # TODO: QFileDialog
        btn_start.clicked.connect(self.preprocess)

        window.show()
        sys.exit(app.exec_())

    def preprocess(self):
        self.prepare_frames(self._input_path_line_edit.text(), 60 * 15)
        self.remove_duplicates(2)
        shutil.rmtree('temp')
        self.create_pdf(self._pdf_path_line_edit.text())

    def prepare_frames(self, video_path, frames_step=3600):
        print('video path: ', video_path)
        vidcap = cv2.VideoCapture(video_path)
        success, image = vidcap.read()
        count = 0
        try:
            os.mkdir("temp")
        except:
            print('File already exists!')

        while success:
            cv2.imwrite("temp/frame%d.jpg" % count, image)
            success, image = vidcap.read()
            count += frames_step
            vidcap.set(cv2.CAP_PROP_POS_FRAMES, count)

    def remove_duplicates(self, trigger_value):
        onlyfiles = [f for f in listdir('temp') if isfile(join('temp', f))]
        if not onlyfiles:
            return
        onlyfiles = sorted(onlyfiles, key=lambda x: int(re.sub("[^0-9]", "", x)))

        try:
            os.mkdir("output")
        except:
            shutil.rmtree('output')
            os.mkdir("output")

        start_img = cv2.imread('temp/' + onlyfiles[0], 0)
        if cv2.countNonZero(start_img) != 0:
            cv2.imwrite("output/" + onlyfiles[0], start_img)
        for i in range(0, len(onlyfiles) - 1):
            img1 = cv2.imread('temp/' + onlyfiles[i], 0)
            img2 = cv2.imread('temp/' + onlyfiles[i + 1], 0)

            res = cv2.absdiff(img1, img2)
            res = res.astype(np.uint8)
            percentage = (np.count_nonzero(res) * 100) / res.size

            if percentage > trigger_value and cv2.countNonZero(img2) != 0:
                cv2.imwrite("output/" + onlyfiles[i + 1], img2)

    @staticmethod
    def create_pdf(output_path: str):
        print('output: ', output_path)
        images = [
            Image.open("output/" + f)
            for f in [f for f in listdir('output') if isfile(join('output', f))]
        ]
        images[0].save(
            output_path, "PDF", resolution=100.0, save_all=True, append_images=images[1:]
        )


NotesFromLectureMaker()