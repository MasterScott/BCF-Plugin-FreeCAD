import os
import sys
import logging
import platform
import pyperclip
import subprocess
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import (QAbstractListModel, QModelIndex, Slot, Signal,
        QDir, QPoint, QSize, QTimer)

import bcfplugin
import bcfplugin.gui.plugin_model as model
import bcfplugin.gui.plugin_delegate as delegate
import bcfplugin.util as util
from bcfplugin.rdwr.viewpoint import Viewpoint
from bcfplugin.gui.views.topicadddialog import TopicAddDialog
from bcfplugin.gui.views.projectcreatedialog import ProjectCreateDialog


logger = bcfplugin.createLogger(__name__)


OBJECTNAME = "bcfplugin"
""" Name of the main window of the plugin. """


def tr(self, text):

    """ Placeholder for the Qt translate function. """

    return self.tr(text)


def createNotificationLabel():

    """ Creates a label intended to show raw text notifications. """

    lbl = QLabel()
    lbl.hide()

    return lbl


def showNotification(self, text):

    """ Shows a notification with content `text` in `notificationLabel` of
    `self`.

    The label is shown for 2 1/2 seconds and then it is hidden again.
    """

    self.notificationLabel.setText(text)
    self.notificationLabel.show()
    if not hasattr(self, "notificationTimer"):
        self.notificationTimer = QTimer()
        self.notificationTimer.timeout.connect(lambda:
                self.notificationLabel.hide())
    self.notificationTimer.start(2500)


class CommentView(QListView):

    """ View showing comment to the user.

    The comment elements are drawn by the CommentDelegate. This class mainly
    maintains the delete button that appears over the "mouse hovered" comment.
    It also emits the event where a comment referencing a viewpoint is selected.
    At all times at most one delete button will be shown/drawn.
    """

    specialCommentSelected = Signal((Viewpoint))
    """ Emitted when a comment, referencing a viewpoint is selected. """


    def __init__(self, parent = None):

        QListView.__init__(self, parent)
        self.setMouseTracking(True)
        self.lastEnteredIndex = None
        """ Index of the list item over whose are the mouse hovered at last """
        self.entered.connect(self.mouseEntered)
        self.delBtn = None
        """ Reference to the delete button. """

        # create editor for a double left click on a comment
        self.doubleClicked.connect(lambda idx: self.commentList.edit(idx))


    @Slot()
    def mouseEntered(self, index):

        """ Display a delete button if the mouse hovers over a comment.

        The button is then wired to a dynamically created clicked handler. This
        handler will be passed the index of the hovered over element as
        parameter. """

        if self.delBtn is not None:
            self.deleteDelBtn()

        options = QStyleOptionViewItem()
        options.initFrom(self)

        btnText = self.tr("Delete")
        deleteButton = QPushButton(self)
        deleteButton.setText(btnText)
        deleteButton.clicked.connect(lambda: self.deleteElement(index))

        buttonFont = deleteButton.font()
        fontMetric = QFontMetrics(buttonFont)
        btnMinSize = fontMetric.boundingRect(btnText).size()
        deleteButton.setMinimumSize(btnMinSize)

        itemRect = self.rectForIndex(index)
        x = itemRect.width() - deleteButton.geometry().width()
        vOffset = self.verticalOffset() # scroll offset
        y = itemRect.y() - vOffset + itemRect.height() - deleteButton.geometry().height()
        deleteButton.move(x, y)

        deleteButton.show()
        self.delBtn = deleteButton


    def currentChanged(self, current, previous):

        """ If the current comment links to a viewpoint then select that
        viewpoint in viewpointsList.  """

        model = current.model()
        if model is None:
            # no topic is selected, so no comments are loaded
            return

        viewpoint = model.referencedViewpoint(current)
        if viewpoint is not None:
            self.specialCommentSelected.emit(viewpoint)


    def resizeEvent(self, event):

        """ Propagates the new width of the widget to the delegate """

        newSize = self.size()
        self.itemDelegate().setWidth(newSize.width())
        QListView.resizeEvent(self, event)


    @Slot()
    def deleteDelBtn(self):

        """ Delete the comment delete button from the view. """

        if self.delBtn is not None:
            self.delBtn.deleteLater()
            self.delBtn = None


    def deleteElement(self, index):

        """ Handler for deleting a comment when the comment delete button was
        pressed """

        logger.debug("Deleting element at index {}".format(index.row()))
        success = index.model().removeRow(index)
        if success:
            self.deleteDelBtn()
        else:
            util.showError("Could not delete comment.")


class SnapshotView(QListView):

    """ Custom list, showing elements horizontally and setting their size to fit
    the window.

    Elements take up equal space in the list view. If there are N elements to be
    displayed, each one gets WIDTH/N units of the width of the view. In case of
    resizing the new sizes are calculated automatically.
    """

    def __init__(self, parent = None):

        QListView.__init__(self, parent)
        screen = util.getCurrentQScreen()
        ppm = screen.logicalDotsPerInch() / util.MMPI
        """ Pixels per millimeter """

        self.minIconSize = QSize(ppm * 20, ppm * 20)
        """ Minimum size of an icon is 2x2cm. """

        self.doubleClicked.connect(self.openSnapshot)
        self.setFlow(QListView.LeftToRight)


    def resizeEvent(self, event):

        """ Recalculate the size each element is allowed to occupy. """

        QListView.resizeEvent(self, event)

        newSize = self.size()
        rowCount = self.model().rowCount()
        rowCount = rowCount if rowCount > 0 else 1
        marginsLeftRight = (self.contentsMargins().left() +
                self.contentsMargins().right())
        marginsTopBottom = (self.contentsMargins().top() +
                self.contentsMargins().bottom())

        logger.debug("Margins of snapshot list: {}".format(marginsLeftRight))
        newItemWidth = newSize.width()
        newItemWidth -= self.spacing() * (rowCount)
        newItemWidth -= marginsLeftRight
        newItemWidth /= rowCount
        newItemSize = QSize(newItemWidth, newSize.height())

        # use minimum values if result is too small
        if (newItemWidth < self.minIconSize.width()):
            newItemSize.setWidth(self.minIconSize.width())
        if (newItemSize.height() < self.minIconSize.height()):
            newItemSize.setHeight(self.minIconSize.height())

        self.model().setSize(newItemSize)
        self.setIconSize(newItemSize)


    @Slot()
    def openSnapshot(self, idx):

        """ Opens the snapshot in original resolution an a new label opened in a
        separate window. """

        img = self.model().realImage(idx)
        lbl = QLabel(self)
        lbl.setWindowFlags(Qt.Window)
        lbl.setPixmap(img)
        lbl.show()


class ViewpointsListView(QListView):

    """ Ordinary ListView, adding hooks to activate a viewpoint in the object
    view of FreeCAD. """


    def __init__(self, parent = None):

        QListView.__init__(self, parent)


    @Slot(Viewpoint)
    def selectViewpoint(self, viewpoint: Viewpoint):

        """ Selects the `viewpoint` in the list. """

        start = self.model().createIndex(0, 0)
        searchValue = str(viewpoint.file) + " (" + str(viewpoint.id) + ")"
        matches = self.model().match(start, Qt.DisplayRole, searchValue)
        if len(matches) > 0:
            self.setCurrentIndex(matches[0])


    @Slot(QModelIndex, QPushButton)
    def activateViewpoint(self, index, rstBtn):

        """ Activates the viewpoint given by `index` in FreeCAD's object view.
        """

        result = self.model().activateViewpoint(index)
        if result:
            rstBtn.show()


    def findViewpoint(self, desired: Viewpoint):

        """ Searches for the `desired` viewpoint in the model.

        Returns the indes in the model if found, otherwise -1 is returned.
        """

        index = -1
        for i in range(0, self.model().rowCount()):
            index = self.model().createIndex(i, 0)
            data = self.model().data(index, Qt.DisplayRole)

            if str(desired.id) in data:
                index = i
                break

        return index


class TopicMetricsDialog(QDialog):

    """ Dialog showing details to a topic.

    Details include:
        - all simple xml nodes contained in the topic node, shown as
          Property:Value table
        - a list of additional documents, specified in the topic node
        - a list of related topics, specified in the topic node
    """

    def __init__(self, parent = None):

        QDialog.__init__(self, parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # setup table for simple xml nodes.
        self.topicMetrics = QTableView()
        self.topicMetrics.setModel(parent.topicDetailsModel)
        self.setMinVertTableSize(self.topicMetrics)
        self.topicMetrics.setItemDelegate(parent.topicDetailsDelegate)
        self.layout.addWidget(self.topicMetrics)

        # setup list showing additional documents
        self.addDocGroup = QGroupBox()
        self.addDocGroup.setTitle(self.addDocGroup.tr("Additional Documents"))
        self.addDocGroupLayout = QVBoxLayout(self.addDocGroup)
        self.addDocTable = QTableView()
        self.addDocTable.setModel(parent.addDocumentsModel)
        self.setMinVertTableSize(self.addDocTable)
        self.addDocTable.doubleClicked.connect(self.openDocRef)
        self.addDocTable.clicked.connect(self.showDoubleClickHint)
        self.addDocGroupLayout.addWidget(self.addDocTable)
        if parent.addDocumentsModel.rowCount() == 0:
            self.addDocTable.hide()
        self.layout.addWidget(self.addDocGroup)

        # setup list showing related topics.
        self.relTopGroup = QGroupBox()
        self.relTopGroup.setTitle(self.relTopGroup.tr("Related Topics"))
        self.relTopGroupLayout = QVBoxLayout(self.relTopGroup)
        self.relTopList = QListView()
        self.relTopList.setModel(parent.relTopModel)
        self.relTopGroupLayout.addWidget(self.relTopList)
        if parent.relTopModel.rowCount() == 0:
            self.relTopList.hide()
        self.layout.addWidget(self.relTopGroup)

        self.notificationLabel = createNotificationLabel()
        # add it to the main windows members because it is accessed in
        # openDocRef()
        self.layout.addWidget(self.notificationLabel)


    @Slot()
    def openDocRef(self, index):

        """ Opens an additional document specified by `index` or copies the path
        to clipboard.

        The behavior is determined by the column, in which the double clicked
        element resides. For elements in the first column it is tried to open
        them with the default application of the platform.
        For elements in the second column the content is copied to the
        clipboard.
        """

        filePath = index.model().getFilePath(index)
        if index.column() == 0:
            if filePath is not None:
                system = platform.system()
                if system == "Darwin": # this my dear friend is macOS
                    subprocess.call(["open", filePath])
                elif system == "Windows": # ... well, MS Windows
                    os.startfile(filePath)
                else: # good old linux derivatives
                    subprocess.call(["xdg-open", filePath])
        else: # copy path to clipboard and notify the user about it
            pyperclip.copy(index.model().data(index))
            showNotification(self, "Copied path to clipboard.")


    @Slot(QModelIndex)
    def showDoubleClickHint(self, index):

        """ Shows a notification, informing about the double click behavior. """

        if index.column() == 0:
            showNotification(self, "Double click to open document.")
        elif index.column() == 1:
            showNotification(self, "Double click to copy path.")


    def setMinVertTableSize(self, table):

        """ This function calculates the minimum vertical size the table needs
        to display its contents without a scrollbar and sets it.

        This function assumes that it is called after the model is set.
        This code was adapted from:
        https://stackoverflow.com/questions/42458735/how-do-i-adjust-a-qtableview-height-according-to-contents
        """

        totalHeight = 0
        for i in range(0, table.verticalHeader().count()):
            if not table.verticalHeader().isSectionHidden(i):
                totalHeight += table.verticalHeader().sectionSize(i)

        if not table.horizontalScrollBar().isHidden():
            totalHeight += table.horizontalScrollBar().height()

        if not table.horizontalHeader().isHidden():
            totalHeight += table.horizontalHeader().height()

        logger.info("Setting size of AddDocTable to {}".format(totalHeight))
        table.setMinimumHeight(totalHeight)



class MyMainWindow(QWidget):

    """ ... well this is the main window.

    The UI consists of roughly three big sections:
        - the Project/Topic section containing controls to operate on a project
          and topic respectively
        - the comment section: showing a list of comments and a QLineEdit to add
          new comments.
        - the snapshot section: composed of a stacked widget and a combobox to
          switch between the widgets in the stack. The first widget shows a
          horizontal list of snapshots specified in the topic, the second widget
          shows a vertical list of all viewpoints specified in the topic.
    These sections are added to a QSplitter to allow the user to easily resize
    them at will.

    From the main window two form dialogs can be opened. The first one for
    creating a new project. The second one creates a new topic in a new project.

    Two data windows can also be opened: one showing information about a
    particular topic (the topic metrics window) and the other one displaying a
    snapshot in its original resolution.

    Also for a more event driven approach the signal `projectOpened` is defined.
    It gets emitted when a project was opened.
    """

    projectOpened = Signal()

    def __init__(self):
        QWidget.__init__(self, None)

        self.setObjectName(OBJECTNAME)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setObjectName("mainLayout")
        self.setWindowTitle("BCF-Plugin")

        self.mainSplitter = self.setupSplitter()
        self.mainLayout.addWidget(self.mainSplitter)

        # setup/add of the project/topic section
        self.projectGroup = self.createProjectTopicGroup()
        self.mainSplitter.addWidget(self.projectGroup)

        # setup/add of the comment section, initially hidden
        self.commentGroup = self.createCommentGroup()
        self.commentGroup.hide()
        self.mainSplitter.addWidget(self.commentGroup)

        # setup/add of the snapshot section, initially hidden
        self.snapshotArea = self.createSnapshotGroup()
        self.snapshotArea.hide()
        self.mainSplitter.addWidget(self.snapshotArea)

        # create and add a notification label for the main window
        self.notificationLabel = createNotificationLabel()
        self.mainLayout.addWidget(self.notificationLabel)

        """ Handlers for buttons associated with a topic """
        self.projectOpenButton.clicked.connect(self.openProjectBtnHandler)
        # after a project is opened, a project cannot be created anymore.
        self.projectOpenButton.clicked.connect(self.projectCreateButton.hide)
        self.projectSaveButton.clicked.connect(self.saveProjectHandler)
        self.projectCreateButton.clicked.connect(self.showCreateProjectDialog)

        """ handlers for an opened project """
        self.projectOpened.connect(self.projectSaveButton.show)
        self.projectOpened.connect(self.openedProjectUiHandler)
        # reset models for every opened project
        self.projectOpened.connect(self.topicListModel.projectOpened)
        self.projectOpened.connect(self.commentModel.resetItems)
        self.projectOpened.connect(self.commentList.deleteDelBtn)
        self.projectOpened.connect(self.snapshotModel.resetItems)
        self.projectOpened.connect(self.viewpointsModel.resetItems)
        self.projectOpened.connect(self.relTopModel.resetItems)

        # reset both the combobox and the stacked widget beneath to the first
        # index for an opened project
        self.projectOpened.connect(lambda: self.snStack.setCurrentIndex(0))
        self.projectOpened.connect(lambda: self.snStackSwitcher.setCurrentIndex(0))
        self.projectOpened.connect(self.hideCommentSnapshotGroup)
        self.projectOpened.connect(self.topicNameLbl.hide)


        self.topicListModel.selectionChanged.connect(lambda x:
                self.showCommentSnapshotGroup())
        self.topicListModel.selectionChanged.connect(lambda x:
                self.newCommentEdit.setDisabled(False))

        # reset ui after a topic switch, to not display any artifacts from the
        # previous topic
        self.topicListModel.selectionChanged.connect(self.showCommentSnapshotGroup)
        self.topicListModel.selectionChanged.connect(self.commentModel.resetItems)
        self.topicListModel.selectionChanged.connect(self.commentList.deleteDelBtn)
        self.topicListModel.selectionChanged.connect(self.snapshotModel.resetItems)
        self.topicListModel.selectionChanged.connect(self.viewpointsModel.resetItems)
        self.topicListModel.selectionChanged.connect(self.topicDetailsBtn.show)
        self.topicListModel.selectionChanged.connect(self.topicDetailsModel.resetItems)
        self.topicListModel.selectionChanged.connect(self.addDocumentsModel.resetItems)
        self.topicListModel.selectionChanged.connect(self.relTopModel.resetItems)
        self.topicListModel.selectionChanged.connect(lambda x:
                self.topicNameLbl.show())
        self.topicListModel.selectionChanged.connect(lambda topic:
                self.topicNameLbl.setText(topic.title))
        # reset both the combobox and the stacked widget beneath to the first
        # index for a topic switch
        self.topicListModel.selectionChanged.connect(lambda: self.snStack.setCurrentIndex(0))
        self.topicListModel.selectionChanged.connect(lambda: self.snStackSwitcher.setCurrentIndex(0))
        # connect the stacked widget with the combobox
        self.snStackSwitcher.activated.connect(self.snStack.setCurrentIndex)
        # select a viewpoint if a referncing comment is selected
        self.commentList.specialCommentSelected.connect(lambda x:
                self.snStack.setCurrentIndex(1))
        self.commentList.specialCommentSelected.connect(lambda x:
                self.snStackSwitcher.setCurrentIndex(1))
        self.commentList.specialCommentSelected.connect(self.viewpointList.selectViewpoint)
        # open the topic metrics window
        self.topicDetailsBtn.pressed.connect(self.showTopicMetrics)
        self.topicAddBtn.pressed.connect(self.showAddTopicForm)
        # activate a viewpoint using viewController.py
        self.viewpointList.doubleClicked.connect(lambda x:
                self.viewpointList.activateViewpoint(x, self.viewpointResetBtn))
        self.viewpointResetBtn.clicked.connect(self.viewpointsModel.resetView)
        self.viewpointResetBtn.clicked.connect(self.viewpointResetBtn.hide)
        # delete delete button if the view is scrolled
        self.commentList.verticalScrollBar().valueChanged.connect(lambda x:
                self.commentList.deleteDelBtn())

        self.setLayout(self.mainLayout)

        self.openFilePath = ""


    def setupSplitter(self):

        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        return splitter


    def createProjectTopicGroup(self):

        topFrame = QFrame()
        topLayout = QHBoxLayout(topFrame)
        topLayout.setSpacing(0)
        topMargins = topLayout.contentsMargins()
        topMargins.setBottom(0)
        topMargins.setLeft(0)
        topMargins.setRight(0)
        topLayout.setContentsMargins(topMargins)

        projFrame = QFrame()
        projLayout = QVBoxLayout(projFrame)
        projMargins = projLayout.contentsMargins()
        projMargins.setLeft(0)
        projMargins.setBottom(0)
        projLayout.setContentsMargins(projMargins)
        topLayout.addWidget(projFrame)

        self.projectSaveButton = QPushButton(self.tr("Save"))
        self.projectSaveButton.setObjectName("projectSaveButton")
        self.projectSaveButton.hide()

        self.projectOpenButton = QPushButton(self.tr("Open"))
        self.projectOpenButton.setObjectName("projectOpenButton")

        self.projectCreateButton = QPushButton(self.tr("Create"))
        self.projectCreateButton.setObjectName("projectCreateButton")

        projLayout.addWidget(self.projectOpenButton)
        projLayout.addWidget(self.projectCreateButton)
        projLayout.addWidget(self.projectSaveButton)
        projLayout.addStretch(20)

        topicFrame = QFrame()
        topicLayout = QVBoxLayout(topicFrame)
        topicMargins = topicLayout.contentsMargins()
        topicMargins.setRight(0)
        topicMargins.setBottom(0)
        topicLayout.setContentsMargins(topicMargins)
        topLayout.addWidget(topicFrame)

        self.topicAddBtn = QPushButton(self.tr("Add Topic"))
        self.topicAddBtn.setObjectName("addTopicBtn")
        self.topicAddBtn.hide()

        self.topicDetailsBtn = QPushButton(self.tr("Details"))
        self.topicDetailsBtn.setObjectName("topicDetailsBtn")
        self.topicDetailsBtn.hide()

        topicBtnLayout = QHBoxLayout()
        topicBtnLayout.addWidget(self.topicAddBtn)
        topicBtnLayout.addWidget(self.topicDetailsBtn)

        self.topicNameLbl = QLabel()

        self.topicList = QListView()
        self.topicListModel = model.TopicCBModel()
        self.topicList.setModel(self.topicListModel)
        self.topicList.setObjectName("topicList")
        self.topicList.doubleClicked.connect(self.topicListModel.newSelection)
        logger.debug("Connected double click signal to newSelection slot")
        self.topicList.hide()

        topicLayout.addWidget(self.topicNameLbl)
        topicLayout.addLayout(topicBtnLayout)
        topicLayout.addWidget(self.topicList)

        # setup models for topic details window
        self.topicDetailsModel = model.TopicMetricsModel()
        self.topicDetailsDelegate = delegate.TopicMetricsDelegate()
        self.addDocumentsModel = model.AdditionalDocumentsModel()
        self.relTopModel = model.RelatedTopicsModel()

        return topFrame


    def createCommentGroup(self):

        commentGroup = QFrame()
        commentGroup.setObjectName("commentGroup")

        self.commentLayout = QVBoxLayout(commentGroup)
        self.commentLayout.setSpacing(0)
        self.commentLayout.setMargin(0)
        self.commentList = CommentView()

        self.commentModel = model.CommentModel()
        self.commentList.setModel(self.commentModel)

        self.commentDelegate = delegate.CommentDelegate()
        self.commentList.setItemDelegate(self.commentDelegate)

        self.commentLayout.addWidget(self.commentList)

        self.commentPlaceholder = self.tr("Enter a new comment here")
        self.newCommentEdit = QLineEdit()
        self.newCommentEdit.returnPressed.connect(self.checkAndAddComment)
        self.newCommentEdit.setPlaceholderText(self.commentPlaceholder)
        self.newCommentEdit.setDisabled(True)

        self.commentLayout.addWidget(self.newCommentEdit)

        return commentGroup


    def createSnapshotGroup(self):

        snGroup = QFrame()
        self.snGroupLayout = QVBoxLayout(snGroup)
        self.snGroupLayout.setSpacing(0)
        self.snGroupLayout.setMargin(0)

        self.snapshotModel = model.SnapshotModel()
        self.snapshotList = SnapshotView()
        self.snapshotList.setModel(self.snapshotModel)

        self.viewpointsModel = model.ViewpointsListModel(self.snapshotModel)
        self.viewpointList = ViewpointsListView()
        self.viewpointList.setModel(self.viewpointsModel)

        self.snStack = QStackedWidget()
        self.snStack.addWidget(self.snapshotList)
        self.snStack.addWidget(self.viewpointList)

        self.viewpointResetBtn = QPushButton(self.tr("Reset View"))
        self.viewpointResetBtn.hide()

        self.snStackSwitcher = QComboBox()
        self.snStackSwitcher.addItem(self.tr("Snapshot Bar"))
        self.snStackSwitcher.addItem(self.tr("Viewpoint List"))

        self.snGroupLayout.addWidget(self.snStackSwitcher)
        self.snGroupLayout.addWidget(self.snStack)
        self.snGroupLayout.addWidget(self.viewpointResetBtn)

        return snGroup


    @Slot()
    def openedProjectUiHandler(self):

        logger.info("setting up view")

        self.projectOpenButton.setText(self.tr("Open other"))
        self.topicList.show()
        self.topicAddBtn.show()


    @Slot()
    def hideCommentSnapshotGroup(self):

        self.commentGroup.hide()
        self.snapshotArea.hide()


    @Slot()
    def showCommentSnapshotGroup(self):

        self.commentGroup.show()
        self.snapshotArea.show()


    @Slot()
    def openProjectBtnHandler(self):

        lastPath = self.openFilePath
        dflPath = lastPath if lastPath != "" else QDir.homePath()

        filename = QFileDialog.getOpenFileName(self, self.tr("Open BCF File"),
                dflPath,  self.tr("BCF Files (*.bcf *.bcfzip)"))
        if filename[0] != "":
            model.openProjectBtnHandler(filename[0])
            self.openFilePath = filename[0]
            self.projectOpened.emit()


    @Slot()
    def checkAndAddComment(self):

        editor = self.newCommentEdit
        text = editor.text()

        if util.isAuthorSet():
            modAuthor = util.getAuthor()
        else:
            delegate.openAuthorsDialog(None)

        self.addComment()


    @Slot()
    def addComment(self):

        text = self.newCommentEdit.text()
        success = self.commentModel.addComment((text, util.getAuthor()))
        if not success:
            util.showError(self.tr("Could not add a new comment"))
            return

        # delete comment on successful addition
        self.newCommentEdit.setText("")


    @Slot()
    def saveProjectHandler(self):

        dflPath = self.openFilePath
        filename = QFileDialog.getSaveFileName(self, self.tr("Save BCF File"),
                dflPath,  self.tr("BCF Files (*.bcf *.bcfzip)"))
        if filename[0] != "":
            logger.debug("Got a file to write to: {}.".format(filename))
            model.saveProject(filename[0])


    @Slot()
    def showTopicMetrics(self):

        metricsWindow = TopicMetricsDialog(self)
        metricsWindow.show()


    @Slot()
    def showAddTopicForm(self):

        addTopicForm = TopicAddDialog(self)
        addTopicForm.exec()
        self.topicListModel.updateTopics()


    def closeEvent(self, event):

        if util.getDirtyBit():
            self.showExitSaveDialog()

        logger.debug("Deleting temporary directory {}".format(util.getSystemTmp()))
        util.deleteTmp()


    def closeSaveProject(self, dialog):

        self.saveProjectHandler()
        dialog.done(0)


    def showExitSaveDialog(self):

        dialog = QDialog(self)
        buttons = QDialogButtonBox(QDialogButtonBox.Save |
                QDialogButtonBox.Close, dialog)
        label = QLabel(self.tr("Save before closing?"))

        layout = QVBoxLayout(dialog)
        layout.addWidget(label)
        layout.addWidget(buttons)
        dialog.setLayout(layout)

        buttons.accepted.connect(lambda: self.closeSaveProject(dialog))
        buttons.rejected.connect(lambda: dialog.done(0))
        dialog.exec()


    def showCreateProjectDialog(self):

        dialog = ProjectCreateDialog(self)
        dialog.exec()

        self.projectOpened.emit()


    def deleteStretch(self):

        """ Delete the first QSpacerItem found in mainLayout """

        for idx in range(0, self.mainLayout.count()):
            child = self.mainLayout.itemAt(idx)
            if issubclass(type(child), QSpacerItem):
                self.mainLayout.takeAt(idx)
                break


if __name__ == "__main__":
    app = QApplication(sys.argv)

    plugin = MyMainWindow()
    plugin.show()

    app.exec_()
    sys.exit()
