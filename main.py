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
from PyQt5.QtCore import QRunnable, pyqtSlot, QThreadPool
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QLineEdit, QVBoxLayout, QLabel, QFileDialog, QProgressBar
import pytesseract


class Worker(QRunnable):
    def __init__(self, obj):
        super().__init__()
        self._obj = obj

    @pyqtSlot()
    def run(self):
        self._obj.prepare_frames(self._obj.input_path_line_edit.text(), 60 * 15)
        self._obj.remove_duplicates(3)
        shutil.rmtree('temp')
        self._obj.generate_txt()
        self._obj.create_pdf(self._obj.pdf_path_line_edit.text())
        self._obj.progress_bar.setValue(0)


class NotesFromLectureMaker:
    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract\tesseract.exe'
        app = QtWidgets.QApplication(sys.argv)
        self._window = QtWidgets.QWidget()
        self._window.setWindowTitle("NotesFromLectureMaker")
        self._window.setFixedSize(500, 150)
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
        btn_generate_pdf = QPushButton("Generate PDF")
        layout.addWidget(btn_generate_pdf)
        self._progress_bar = QProgressBar()
        layout.addWidget(self._progress_bar)
        self._window.setLayout(layout)

        btn_select_input_file.clicked.connect(self.set_input_path)
        btn_select_output_file.clicked.connect(self.set_output_path)
        self.threadpool = QThreadPool()
        worker = Worker(self)
        btn_generate_pdf.clicked.connect(lambda: self.threadpool.start(worker))
        self._window.show()
        sys.exit(app.exec_())

    def set_input_path(self):
        filename = QFileDialog.getOpenFileName(self._window, "Choose video", "",
                                               "Video Files (*.mp4 *.avi *.mkv *.mov *.flv);;")
        if filename[0]:
            self._input_path_line_edit.setText(filename[0])

    def set_output_path(self):
        filename = QFileDialog.getSaveFileName(self._window, "Create PDF", "", "Video Files (*.pdf);;")
        if filename[0]:
            self._pdf_path_line_edit.setText(filename[0])

    def prepare_frames(self, video_path, frames_step=3600):
        vidcap = cv2.VideoCapture(video_path)
        self._progress_bar.setMaximum(int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT)))
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
            self._progress_bar.setValue(count)
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
            cv2.imwrite("output/" + onlyfiles[0], cv2.imread('temp/' + onlyfiles[0]))
        for i in range(0, len(onlyfiles) - 1):
            img1 = cv2.imread('temp/' + onlyfiles[i], 0)
            img2 = cv2.imread('temp/' + onlyfiles[i + 1], 0)

            res = cv2.absdiff(img1, img2)
            res = res.astype(np.uint8)
            percentage = (np.count_nonzero(res) * 100) / res.size

            if percentage > trigger_value and cv2.countNonZero(img2) != 0:
                cv2.imwrite("output/" + onlyfiles[i + 1], cv2.imread('temp/' + onlyfiles[i + 1]))

    @staticmethod
    def create_pdf(output_path: str):
        onlyfiles = [f for f in listdir('output') if isfile(join('output', f))]
        if not onlyfiles:
            return
        onlyfiles = sorted(onlyfiles, key=lambda x: int(re.sub("[^0-9]", "", x)))
        images = [Image.open("output/" + f) for f in onlyfiles]
        images[0].save(
            output_path, "PDF", resolution=100.0, save_all=True, append_images=images[1:]
        )

    @staticmethod
    def generate_txt():
        onlyfiles = ["output/"+f for f in listdir('output') if isfile(join('output', f))]
        print(onlyfiles)
        for file in onlyfiles:
            img = cv2.imread(file)
            print(pytesseract.image_to_string(img))

    @property
    def input_path_line_edit(self):
        return self._input_path_line_edit

    @property
    def pdf_path_line_edit(self):
        return self._pdf_path_line_edit

    @property
    def progress_bar(self):
        return self._progress_bar


NotesFromLectureMaker()
