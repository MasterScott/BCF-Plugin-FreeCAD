import sys
if __name__ == "__main__":
    sys.path.append("../../")
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import (QAbstractListModel, QModelIndex, Slot, QDir,
        QPoint, QSize)


import bcfplugin.gui.plugin_model as model
import bcfplugin.gui.plugin_delegate as delegate
import bcfplugin.util as util


class CommentView(QListView):

    def __init__(self, parent = None):

        QListView.__init__(self, parent)
        self.setMouseTracking(True)
        self.lastEnteredIndex = None
        self.entered.connect(self.mouseEntered)
        self.delBtn = None


    @Slot()
    def mouseEntered(self, index):

        if self.delBtn is not None:
            self.deleteDelBtn()

        options = QStyleOptionViewItem()
        options.initFrom(self)

        btnText = "Delete"
        deleteButton = QPushButton(self)
        deleteButton.setText(btnText)
        deleteButton.clicked.connect(lambda: self.deleteElement(index))

        buttonFont = deleteButton.font()
        fontMetric = QFontMetrics(buttonFont)
        minWidth = fontMetric.width(btnText)
        minHeight = fontMetric.height()
        btnMinSize = QSize(minWidth, minHeight)
        deleteButton.setMinimumSize(btnMinSize)

        itemRect = self.rectForIndex(index)
        x = itemRect.width() - deleteButton.geometry().width()
        y = itemRect.y() + (itemRect.height() -
                deleteButton.geometry().height()) / 2
        deleteButton.move(x, y)

        deleteButton.show()
        self.delBtn = deleteButton


    def deleteDelBtn(self):

        self.delBtn.deleteLater()
        self.delBtn = None


    def deleteElement(self, index):

        util.debug("Deleting element at index {}".format(index.row()))
        success = index.model().removeRow(index)
        if success:
            self.deleteDelBtn()
        else:
            util.showError("Could not delete comment.")


class MyMainWindow(QWidget):

    def __init__(self):
        QWidget.__init__(self, None)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setObjectName("mainLayout")

        self.projectGroup = self.createProjectGroup()
        self.mainLayout.addWidget(self.projectGroup)

        self.topicGroup = self.createTopicGroup()
        self.topicGroup.hide()
        self.mainLayout.addWidget(self.topicGroup)

        self.commentGroup = self.createCommentGroup()
        self.commentGroup.hide()
        self.mainLayout.addWidget(self.commentGroup)

        self.setLayout(self.mainLayout)


    def createProjectGroup(self):

        projectGroup = QGroupBox()
        projectGroup.setObjectName("projectGroup")

        self.projectLayout = QHBoxLayout(projectGroup)
        self.projectLayout.setObjectName("projectLayout")

        self.projectLabel = QLabel("Open Project")
        self.projectLabel.setObjectName("projectLabel")
        self.projectLayout.addWidget(self.projectLabel)

        self.projectButton = QPushButton("Open")
        self.projectButton.setObjectName("projectButton")
        self.projectButton.clicked.connect(self.openProjectBtnHandler)
        self.projectLayout.addWidget(self.projectButton)

        return projectGroup


    def createTopicGroup(self):

        topicGroup = QGroupBox()
        topicGroup.setObjectName("topicGroup")

        self.topicLabel = QLabel("Topic: ")

        self.topicCb = QComboBox()
        self.topicCbModel = model.TopicCBModel()
        self.topicCb.setModel(self.topicCbModel)
        self.topicCb.currentIndexChanged.connect(self.topicCbModel.newSelection)

        self.topicHLayout = QHBoxLayout(topicGroup)
        self.topicHLayout.addWidget(self.topicLabel)
        self.topicHLayout.addWidget(self.topicCb)

        return topicGroup


    def createCommentGroup(self):

        commentGroup = QGroupBox()
        commentGroup.setObjectName("commentGroup")

        self.commentLayout = QVBoxLayout(commentGroup)
        self.commentList = CommentView()

        self.commentModel = model.CommentModel()
        self.commentList.setModel(self.commentModel)

        self.commentDelegate = delegate.CommentDelegate()
        self.commentList.setItemDelegate(self.commentDelegate)
        self.commentDelegate.invalidInput.connect(self.commentList.edit)

        self.commentList.doubleClicked.connect(
                lambda idx: self.commentList.edit(idx))
        self.topicCbModel.selectionChanged.connect(self.commentModel.resetItems)

        self.commentLayout.addWidget(self.commentList)

        self.commentPlaceholder = "comment -- author email"
        self.commentValidator = QRegExpValidator()
        self.commentValidator.setRegExp(delegate.commentRegex)
        self.newCommentEdit = QLineEdit()
        self.newCommentEdit.returnPressed.connect(self.checkAndAddComment)
        self.newCommentEdit.setPlaceholderText(self.commentPlaceholder)
        self.commentLayout.addWidget(self.newCommentEdit)

        return commentGroup


    def createViewpointGroup(self):
        #TODO: implement
        pass


    @Slot()
    def openProjectBtnHandler(self):

        dflPath = QDir.homePath()
        filename = QFileDialog.getOpenFileName(self, self.tr("Open BCF File"),
                dflPath,  self.tr("BCF Files (*.bcf *.bcfzip)"))
        if filename[0] != "":
            model.openProjectBtnHandler(filename[0])
            self.projectLabel.setText(model.getProjectName())
            self.projectButton.setText("Open other")
            self.topicCbModel.projectOpened()
            self.topicGroup.show()
            self.commentGroup.show()


    @Slot()
    def checkAndAddComment(self):

        util.debug("Pressed enter on the input")
        editor = self.newCommentEdit
        text = editor.text()
        if self.commentValidator.validate(text, 0) == QValidator.Invalid:
            QToolTip.showText(editor.mapToGlobal(QPoint()), "Invalid Input."\
                    " Template for a comment is: <comment text> -- <email address>")
            return
        self.addComment()


    @Slot()
    def addComment(self):

        text = self.newCommentEdit.text()
        success = self.commentModel.addComment(text)
        if not success:
            util.showError("Could not add a new comment")
            return

        # delete comment on successful addition
        self.newCommentEdit.setText("")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    plugin = MyMainWindow()
    plugin.show()

    app.exec_()
    sys.exit()
