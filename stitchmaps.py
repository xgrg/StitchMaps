#!/usr/bin/env python

from PyQt4 import QtCore, QtGui
from PIL import Image

ready_to_click = False
is_scroll_visible = False

def compute_match(im1,im2,pos):
    import numpy as np
    d1 = np.array(im1)
    d2 = np.array(im2)
    d1b = d1[pos[1]:pos[1]+d2.shape[0], pos[0]:pos[0]+d2.shape[1]]
    d3 = np.abs(d1b.astype(np.float) - d2.astype(np.float)).mean(2)
    mask = (d1b[:,:] != [255,255,255]).mean(2).astype(np.bool)
    d4 = d3[mask==True]
    if d4.size == 0: return 100
    pc = np.abs(d4).sum() / (255.0 * d4.size) * 100.0
    return pc

def display_match(f1, f2, pos):
    im2 = Image.open(str(f1))
    im1 = Image.new('RGB', (im2.size[0]+1000*2, im2.size[1]+500*2), color=(255,255,255))
    im1.paste(im2, (1000,500))
    im2 = Image.open(str(f2))
    im1.paste(im2, pos)
    im1.show()


def adjust_match(f1, f2, pos):
    print 'adjusting...'
    im2 = Image.open(str(f1))
    im1 = Image.new('RGB', (im2.size[0]+1000*2, im2.size[1]+500*2), color=(255,255,255))
    im1.paste(im2, (1000,500))
    im2 = Image.open(str(f2))
    import numpy as np
    d1 = np.array(im1)
    d2 = np.array(im2)
    mini = 100
    posmin = pos
    r = 3
    threshold = 1
    for i in range(-r,r):
        for j in range(-r,r):
            d1b = d1[pos[1]+j:pos[1]+j+d2.shape[0], pos[0]+i:pos[0]+i+d2.shape[1]]
            d3 = np.abs(d1b.astype(np.float) - d2.astype(np.float)).mean(2)
            mask = (d1b[:,:] != [255,255,255]).mean(2).astype(np.bool)
            d4 = d3[mask==True]
            if d4.size == 0: continue
            pc = np.abs(d4).sum() / (255.0 * d4.size) * 100.0
            #if pc < 1:
            #    posmin = (pos[0]+i, pos[1]+j)
            #    print 'found perfect match', posmin, pc
            #    return posmin

            if pc < mini:
                mini = pc
                posmin = (pos[0]+i, pos[1]+j)

    print 'mini:', posmin, mini, '(', posmin[0]-pos[0], posmin[1]-pos[1],')'
    if mini > 75: print 'WARNING: probably wrong'
    return posmin


class clickableQLabel(QtGui.QLabel):
    def __init__(self, parent = None):
        super(QtGui.QLabel, self).__init__(parent)

        self.setMouseTracking(True)

    def mouseMoveEvent(self, e):
        global ready_to_click
        global is_scroll_visible
        cursor =QtGui.QCursor()
        x,y = e.pos().x(), e.pos().y()
        scale_factor = self.ui.scaleFactor

        vbar_value = self.ui.scrollArea.verticalScrollBar().value()
        vbar_ratio = vbar_value / float(self.ui.scrollArea.verticalScrollBar().maximum())\
            if self.ui.scrollArea.verticalScrollBar().maximum() != 0 else 0
        hbar_value = self.ui.scrollArea.horizontalScrollBar().value()
        hbar_ratio =  hbar_value / float(self.ui.scrollArea.horizontalScrollBar().maximum())\
            if self.ui.scrollArea.horizontalScrollBar().maximum() != 0 else 0
        status = ['scale:', self.ui.scaleFactor,\
             'vbar:', self.ui.scrollArea.verticalScrollBar().value(),\
             self.ui.scrollArea.verticalScrollBar().maximum(), vbar_ratio,\
             'hbar:', self.ui.scrollArea.horizontalScrollBar().value(),\
             self.ui.scrollArea.horizontalScrollBar().maximum(), hbar_ratio]
        image_size = self.ui.imageLabel.pixmap().size()
        image_size = (image_size.width(), image_size.height())
        status.extend(['x,y:',x,y, image_size])

        is_scroll_visible = True\
            if self.ui.scrollArea.verticalScrollBar().maximum() !=0 or \
                self.ui.scrollArea.horizontalScrollBar().maximum() != 0\
        else False

        x = int(x/scale_factor)
        y = int(y/scale_factor)
        status.extend(['(x,y) pos in image:', x,y])

        if ready_to_click: # and not is_scroll_visible:
               self.ui.stitch_position =  (x-885/2,y-471/2)
               try:
                   status = ['(match : %s)'%compute_match(self.ui.raw_image, self.ui.stitchimage, self.ui.stitch_position), status]
               except ValueError:
                   status.append('(EXCEPTION)')


               self.ui.display_image((self.ui.stitchfn, self.ui.stitch_position))

        status.extend([self.ui.fileName, getattr(self.ui, 'stitchfn', 'nostitch')])
        self.ui.status_bar.showMessage(' '.join([str(i) for i in status]))

    def mousePressEvent(self, e):
        global ready_to_click
        if ready_to_click:
            ready_to_click = not ready_to_click
        print 'clicked ready to stitch is', ready_to_click


        if QtGui.qApp.mouseButtons() & QtCore.Qt.RightButton:
            vbar_value = self.ui.scrollArea.verticalScrollBar().value()
            hbar_value = self.ui.scrollArea.horizontalScrollBar().value()
            print 'scrollsave', vbar_value, hbar_value

            self.ui.fileName = '/tmp/toto.png'
            print 'Creating backup'
            import os
            os.system('cp %s %s.bak'%(self.ui.fileName, self.ui.fileName))
            print 'Saving image as %s'%self.ui.fileName
            self.ui.saveImage()
            print 'Reloading it'
            self.ui.load_image(self.ui.fileName)

            self.ui.scrollArea.horizontalScrollBar().setValue(hbar_value)
            self.ui.scrollArea.verticalScrollBar().setValue(vbar_value)




class ImageViewer(QtGui.QMainWindow):
    def __init__(self):
        super(ImageViewer, self).__init__()

        self.printer = QtGui.QPrinter()
        self.scaleFactor = 0.0

        self.imageLabel = clickableQLabel()
        self.imageLabel.ui = self
        self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
        self.imageLabel.setSizePolicy(QtGui.QSizePolicy.Ignored,
                QtGui.QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.setCentralWidget(self.scrollArea)
        self.status_bar = self.statusBar()

        self.createActions()
        self.createMenus()

        self.setWindowTitle("StitchMaps")
        self.resize(1300, 600)


    def keyPressEvent(self, e):
        global ready_to_click
        if e.key() == QtCore.Qt.Key_Space:
            adj_pos = adjust_match(self.fileName, self.stitchfn, self.stitch_position)
            self.stitch_position =  adj_pos
            self.load_image(self.fileName, (self.stitchfn, self.stitch_position))
            ready_to_click = False
        elif e.key() == QtCore.Qt.Key_Backspace:
                print('ctrl+click')
                ready_to_click = False
                self.load_image(self.fileName)
        elif e.key() in [QtCore.Qt.Key_Z, QtCore.Qt.Key_E]:
            import os.path as osp
            from glob import glob
            d = osp.split(str(self.stitchfn))[0]
            print 'dir:', d
            files = glob('%s/*.jpg'%d)
            files.extend(glob('%s/*.png'%d))
            files = sorted(files)
            index_file = files.index(str(self.stitchfn))
            print 'index_file', index_file

            if e.key() == QtCore.Qt.Key_E:
                if index_file != len(files) - 1:
                    next_file = files[index_file + 1]
                    print 'next', next_file
                    self.load_stitch_image(next_file)
                else:
                    print 'next file not found'

            if e.key() == QtCore.Qt.Key_Z:
                if index_file != 0:
                    prev_file = files[index_file - 1]
                    print 'prev', prev_file
                    self.load_stitch_image(prev_file)
                else:
                    print 'prev file not found'

    def load_stitch_image(self, fileName):
        global ready_to_click
        image = QtGui.QImage(fileName)
        if image.isNull():
            QtGui.QMessageBox.information(self, "Image Viewer",
                    "Cannot load %s." % fileName)
            return
        self.stitchfn = str(fileName)
        stitchimage = Image.open(str(self.stitchfn))
        self.stitchimage = stitchimage

        self.updateActions()
        ready_to_click = True


    def open(self):
        self.fileName = QtGui.QFileDialog.getOpenFileName(self, "Open File",
                QtCore.QDir.currentPath())
        self.load_image(self.fileName)

    def display_image(self, stitchdata=None):
        if not stitchdata is None:
            stitchfn, (x,y) = stitchdata
            im = self.raw_image.copy()
            im.paste(self.stitchimage, (x,y))
        data = im.convert('RGBA').tobytes('raw', 'BGRA')
        self.image = QtGui.QImage(data, im.size[0], im.size[1], QtGui.QImage.Format_ARGB32)
        self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(self.image))

        if stitchdata is None:

            self.printAct.setEnabled(True)
            self.fitToWindowAct.setEnabled(True)
        self.updateActions()

    def load_image(self, fileName, stitchdata=None):
        if fileName:
            im2 = Image.open(str(fileName))
            im = Image.new('RGB', (im2.size[0]+1000*2, im2.size[1]+500*2), color=(255,255,255))
            im.paste(im2, (1000,500))
            self.raw_image = im
            if not stitchdata is None:
                stitchfn, (x,y) = stitchdata
                stitchimage = Image.open(str(stitchfn))
                self.stitchimage = stitchimage
                im.paste(stitchimage, (x,y))
            data = im.convert('RGBA').tobytes('raw', 'BGRA')
            self.image = QtGui.QImage(data, im.size[0], im.size[1], QtGui.QImage.Format_ARGB32)
            self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(self.image))

            self.scaleFactor = 1.0
            if stitchdata is None:

                self.printAct.setEnabled(True)
                self.fitToWindowAct.setEnabled(True)
            self.updateActions()

            if not self.fitToWindowAct.isChecked():
                self.imageLabel.adjustSize()

            if not stitchdata is None:
                self.scaleImage(1.0)

    def print_(self):
        dialog = QtGui.QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QtGui.QPainter(self.printer)
            rect = painter.viewport()
            size = self.imageLabel.pixmap().size()
            size.scale(rect.size(), QtCore.Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.imageLabel.pixmap().rect())
            painter.drawPixmap(0, 0, self.imageLabel.pixmap())

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()

        self.updateActions()

    def openStitchedIm(self):
        global ready_to_click
        fileName = QtGui.QFileDialog.getOpenFileName(self, "Open File",
                QtCore.QDir.currentPath())
        if fileName:
            self.load_stitch_image(fileName)

    def autocrop(self, img, bgcolor):
        ''' Crops an image given a background color '''

        from PIL import Image, ImageChops

        if img.mode == "RGBA":
                img_mode = "RGBA"
        elif img.mode != "RGB":
                img_mode = "RGB"
                img = img.convert("RGB")
        else:
                img_mode = "RGB"
        bg = Image.new(img_mode, img.size, bgcolor)
        diff = ImageChops.difference(img, bg)
        bbox = diff.getbbox()
        return img.crop(bbox)


    def qt_to_pil_image(self, qimg):
        ''' Converting a Qt Image or Pixmap to PIL image '''

        from PyQt4 import Qt
        from PIL import Image, ImageChops
        import cStringIO
        buffer = Qt.QBuffer()
        buffer.open(Qt.QIODevice.ReadWrite)
        qimg.save(buffer, 'PNG')
        strio = cStringIO.StringIO()
        strio.write(buffer.data())
        buffer.close()
        strio.seek(0)
        pil_im = Image.open(strio)
        return pil_im

    def saveImage(self):
        im = self.qt_to_pil_image(self.image)
        self.autocrop(im, (255,255,255)).save('/tmp/toto.png', format='png')

    def about(self):
        QtGui.QMessageBox.about(self, "About Image Viewer",
                "print an image")

    def createActions(self):
        self.openAct = QtGui.QAction("&Open...", self, shortcut="Ctrl+O",
                triggered=self.open)

        self.printAct = QtGui.QAction("&Print...", self, shortcut="Ctrl+P",
                enabled=False, triggered=self.print_)

        self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
                triggered=self.close)

        self.zoomInAct = QtGui.QAction("Zoom &In (25%)", self,
                shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)

        self.zoomOutAct = QtGui.QAction("Zoom &Out (25%)", self,
                shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)

        self.normalSizeAct = QtGui.QAction("&Normal Size", self,
                 enabled=False, triggered=self.normalSize)

        self.fitToWindowAct = QtGui.QAction("&Fit to Window", self,
                enabled=False, checkable=True, shortcut="Ctrl+F",
                triggered=self.fitToWindow)

        self.aboutAct = QtGui.QAction("&About", self, triggered=self.about)

        self.stitchAct = QtGui.QAction("Stitch new image", self,
                enabled=True, triggered=self.openStitchedIm,shortcut="Ctrl+S")

        self.saveAct = QtGui.QAction("Save image", self,
                enabled=True, triggered=self.saveImage)

        self.aboutQtAct = QtGui.QAction("About &Qt", self,
                triggered=QtGui.qApp.aboutQt)

    def createMenus(self):
        self.fileMenu = QtGui.QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QtGui.QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)
        self.viewMenu.addAction(self.stitchAct)
        self.viewMenu.addAction(self.saveAct)

        self.helpMenu = QtGui.QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.03)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))


if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)
    imageViewer = ImageViewer()
    imageViewer.show()
    sys.exit(app.exec_())
