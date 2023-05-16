# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_dark_alpha.ui'
##
## Created by: Qt User Interface Compiler version 6.2.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QFormLayout, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)
import img_rc

class Ui_ColorPicker(object):
    def setupUi(self, ColorPicker):
        if not ColorPicker.objectName():
            ColorPicker.setObjectName(u"ColorPicker")
        ColorPicker.resize(400, 300)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ColorPicker.sizePolicy().hasHeightForWidth())
        ColorPicker.setSizePolicy(sizePolicy)
        ColorPicker.setMinimumSize(QSize(400, 300))
        ColorPicker.setMaximumSize(QSize(400, 300))
        ColorPicker.setStyleSheet(u"QWidget{\n"
"	background-color: none;\n"
"}\n"
"\n"
"/*  LINE EDIT */\n"
"QLineEdit{\n"
"	color: rgb(221, 221, 221);\n"
"	background-color: #303030;\n"
"	border: 2px solid #303030;\n"
"	border-radius: 5px;\n"
"	selection-color: rgb(16, 16, 16);\n"
"	selection-background-color: rgb(221, 51, 34);\n"
"	font-family: Segoe UI;\n"
"	font-size: 11pt;\n"
"}\n"
"QLineEdit::focus{\n"
"	border-color: #aaaaaa;\n"
"}\n"
"\n"
"/* PUSH BUTTON */\n"
"QPushButton{\n"
"	border: 2px solid #aaa;\n"
"	border-radius: 5px;\n"
"	font-family: Segoe UI;\n"
"	font-size: 9pt;\n"
"	font-weight: bold;\n"
"	color: #ccc;\n"
"	width: 100px;\n"
"}\n"
"QPushButton:hover{\n"
"	border: 2px solid #aaa;\n"
"	color: #222;\n"
"	background-color: #aaa;\n"
"}\n"
"QPushButton:pressed{\n"
"	border: 2px solid #aaa;\n"
"	color: #222;\n"
"	background-color: #aaa;\n"
"}")
        self.verticalLayout = QVBoxLayout(ColorPicker)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.drop_shadow_frame = QFrame(ColorPicker)
        self.drop_shadow_frame.setObjectName(u"drop_shadow_frame")
        self.drop_shadow_frame.setStyleSheet(u"QFrame{\n"
"background-color: #202020;\n"
"border-radius: 10px;\n"
"}")
        self.drop_shadow_frame.setFrameShape(QFrame.StyledPanel)
        self.drop_shadow_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.drop_shadow_frame)
        self.verticalLayout_3.setSpacing(10)
        self.verticalLayout_3.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.title_bar = QFrame(self.drop_shadow_frame)
        self.title_bar.setObjectName(u"title_bar")
        self.title_bar.setMinimumSize(QSize(0, 32))
        self.title_bar.setStyleSheet(u"background-color: rgb(48, 48, 48);")
        self.title_bar.setFrameShape(QFrame.StyledPanel)
        self.title_bar.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.title_bar)
        self.horizontalLayout_2.setSpacing(5)
        self.horizontalLayout_2.setContentsMargins(10, 10, 10, 10)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(10, 0, 10, 0)
        self.horizontalSpacer = QSpacerItem(16, 0, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.window_title = QLabel(self.title_bar)
        self.window_title.setObjectName(u"window_title")
        sizePolicy.setHeightForWidth(self.window_title.sizePolicy().hasHeightForWidth())
        self.window_title.setSizePolicy(sizePolicy)
        self.window_title.setMaximumSize(QSize(16777215, 16777215))
        self.window_title.setStyleSheet(u"QLabel{\n"
"	color: #fff;\n"
"	font-family: Segoe UI;\n"
"	font-size: 9pt;\n"
"}")
        self.window_title.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.window_title)

        self.exit_btn = QPushButton(self.title_bar)
        self.exit_btn.setObjectName(u"exit_btn")
        self.exit_btn.setMinimumSize(QSize(16, 16))
        self.exit_btn.setMaximumSize(QSize(16, 16))
        self.exit_btn.setFocusPolicy(Qt.NoFocus)
        self.exit_btn.setStyleSheet(u"QPushButton{\n"
"	border: none;\n"
"	background-color: #aaaaaa;\n"
"	border-radius: 8px\n"
"}\n"
"QPushButton:hover{\n"
"	background-color: #666666;\n"
"}")
        icon = QIcon()
        icon.addFile(u":/img/exit.ico", QSize(), QIcon.Normal, QIcon.Off)
        self.exit_btn.setIcon(icon)
        self.exit_btn.setIconSize(QSize(12, 12))

        self.horizontalLayout_2.addWidget(self.exit_btn)


        self.verticalLayout_3.addWidget(self.title_bar)

        self.content_bar = QFrame(self.drop_shadow_frame)
        self.content_bar.setObjectName(u"content_bar")
        self.content_bar.setLayoutDirection(Qt.LeftToRight)
        self.content_bar.setStyleSheet(u"QWidget{\n"
"border-radius: 5px\n"
"}\n"
"#color_view{\n"
"	border-bottom-left-radius: 7px;\n"
"	border-bottom-right-radius: 7px;\n"
"}\n"
"#black_overlay{\n"
"	border-bottom-left-radius: 6px;\n"
"	border-bottom-right-radius: 6px;\n"
"}")
        self.content_bar.setFrameShape(QFrame.StyledPanel)
        self.content_bar.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.content_bar)
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setContentsMargins(10, 10, 10, 10)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(10, 0, 10, 0)
        self.color_view = QFrame(self.content_bar)
        self.color_view.setObjectName(u"color_view")
        self.color_view.setMinimumSize(QSize(200, 200))
        self.color_view.setMaximumSize(QSize(200, 200))
        self.color_view.setStyleSheet(u"/* ALL CHANGES HERE WILL BE OVERWRITTEN */;\n"
"background-color: qlineargradient(x1:1, x2:0, stop:0 hsl(0%,100%,50%), stop:1 rgba(255, 255, 255, 255));\n"
"\n"
"")
        self.color_view.setFrameShape(QFrame.StyledPanel)
        self.color_view.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.color_view)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.black_overlay = QFrame(self.color_view)
        self.black_overlay.setObjectName(u"black_overlay")
        self.black_overlay.setStyleSheet(u"background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0, 0, 0, 0), stop:1 rgba(0, 0, 0, 255));\n"
"\n"
"\n"
"")
        self.black_overlay.setFrameShape(QFrame.StyledPanel)
        self.black_overlay.setFrameShadow(QFrame.Raised)
        self.selector = QFrame(self.black_overlay)
        self.selector.setObjectName(u"selector")
        self.selector.setGeometry(QRect(194, 20, 12, 12))
        self.selector.setMinimumSize(QSize(12, 12))
        self.selector.setMaximumSize(QSize(12, 12))
        self.selector.setStyleSheet(u"background-color:none;\n"
"border: 1px solid white;\n"
"border-radius: 5px;")
        self.selector.setFrameShape(QFrame.StyledPanel)
        self.selector.setFrameShadow(QFrame.Raised)
        self.black_ring = QLabel(self.selector)
        self.black_ring.setObjectName(u"black_ring")
        self.black_ring.setGeometry(QRect(1, 1, 10, 10))
        self.black_ring.setMinimumSize(QSize(10, 10))
        self.black_ring.setMaximumSize(QSize(10, 10))
        self.black_ring.setBaseSize(QSize(10, 10))
        self.black_ring.setStyleSheet(u"background-color: none;\n"
"border: 1px solid black;\n"
"border-radius: 5px;")

        self.verticalLayout_2.addWidget(self.black_overlay)


        self.horizontalLayout.addWidget(self.color_view)

        self.frame_2 = QFrame(self.content_bar)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setMinimumSize(QSize(40, 0))
        self.frame_2.setStyleSheet(u"")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.hue_bg = QFrame(self.frame_2)
        self.hue_bg.setObjectName(u"hue_bg")
        self.hue_bg.setGeometry(QRect(10, 0, 20, 200))
        self.hue_bg.setMinimumSize(QSize(20, 200))
        self.hue_bg.setStyleSheet(u"background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(255, 0, 0, 255), stop:0.166 rgba(255, 255, 0, 255), stop:0.333 rgba(0, 255, 0, 255), stop:0.5 rgba(0, 255, 255, 255), stop:0.666 rgba(0, 0, 255, 255), stop:0.833 rgba(255, 0, 255, 255), stop:1 rgba(255, 0, 0, 255));\n"
"border-radius: 5px;")
        self.hue_bg.setFrameShape(QFrame.StyledPanel)
        self.hue_bg.setFrameShadow(QFrame.Raised)
        self.hue_selector = QLabel(self.frame_2)
        self.hue_selector.setObjectName(u"hue_selector")
        self.hue_selector.setGeometry(QRect(7, 185, 26, 15))
        self.hue_selector.setMinimumSize(QSize(26, 0))
        self.hue_selector.setStyleSheet(u"background-color: #aaa;\n"
"border-radius: 5px;")
        self.hue = QFrame(self.frame_2)
        self.hue.setObjectName(u"hue")
        self.hue.setGeometry(QRect(7, 0, 26, 200))
        self.hue.setMinimumSize(QSize(20, 200))
        self.hue.setStyleSheet(u"background-color: none;")
        self.hue.setFrameShape(QFrame.StyledPanel)
        self.hue.setFrameShadow(QFrame.Raised)

        self.horizontalLayout.addWidget(self.frame_2)

        self.editfields = QFrame(self.content_bar)
        self.editfields.setObjectName(u"editfields")
        self.editfields.setMinimumSize(QSize(110, 200))
        self.editfields.setMaximumSize(QSize(120, 200))
        self.editfields.setStyleSheet(u"QLabel{\n"
"	font-family: Segoe UI;\n"
"font-weight: bold;\n"
"	font-size: 11pt;\n"
"	color: #aaaaaa;\n"
"	border-radius: 5px;\n"
"}\n"
"")
        self.editfields.setFrameShape(QFrame.StyledPanel)
        self.editfields.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.editfields)
        self.formLayout.setSpacing(5)
        self.formLayout.setContentsMargins(10, 10, 10, 10)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setHorizontalSpacing(5)
        self.formLayout.setVerticalSpacing(5)
        self.formLayout.setContentsMargins(15, 0, 15, 1)
        self.color_vis = QLabel(self.editfields)
        self.color_vis.setObjectName(u"color_vis")
        self.color_vis.setMinimumSize(QSize(0, 24))
        self.color_vis.setStyleSheet(u"/* ALL CHANGES HERE WILL BE OVERWRITTEN */;\n"
"background-color: rgb(255, 255, 255);\n"
"")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.color_vis)

        self.lastcolor_vis = QLabel(self.editfields)
        self.lastcolor_vis.setObjectName(u"lastcolor_vis")
        self.lastcolor_vis.setMinimumSize(QSize(0, 24))
        self.lastcolor_vis.setStyleSheet(u"/* ALL CHANGES HERE WILL BE OVERWRITTEN */;\n"
"background-color: rgb(0, 0, 0);")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.lastcolor_vis)

        self.lbl_red = QLabel(self.editfields)
        self.lbl_red.setObjectName(u"lbl_red")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.lbl_red)

        self.red = QLineEdit(self.editfields)
        self.red.setObjectName(u"red")
        self.red.setAlignment(Qt.AlignCenter)
        self.red.setClearButtonEnabled(False)

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.red)

        self.lbl_green = QLabel(self.editfields)
        self.lbl_green.setObjectName(u"lbl_green")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.lbl_green)

        self.green = QLineEdit(self.editfields)
        self.green.setObjectName(u"green")
        self.green.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.green)

        self.lbl_blue = QLabel(self.editfields)
        self.lbl_blue.setObjectName(u"lbl_blue")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.lbl_blue)

        self.blue = QLineEdit(self.editfields)
        self.blue.setObjectName(u"blue")
        self.blue.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.blue)

        self.lbl_hex = QLabel(self.editfields)
        self.lbl_hex.setObjectName(u"lbl_hex")
        self.lbl_hex.setStyleSheet(u"font-size: 14pt;")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.lbl_hex)

        self.hex = QLineEdit(self.editfields)
        self.hex.setObjectName(u"hex")
        self.hex.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.hex)

        self.lbl_alpha = QLabel(self.editfields)
        self.lbl_alpha.setObjectName(u"lbl_alpha")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.lbl_alpha)

        self.alpha = QLineEdit(self.editfields)
        self.alpha.setObjectName(u"alpha")
        self.alpha.setAlignment(Qt.AlignCenter)

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.alpha)


        self.horizontalLayout.addWidget(self.editfields)


        self.verticalLayout_3.addWidget(self.content_bar)

        self.button_bar = QFrame(self.drop_shadow_frame)
        self.button_bar.setObjectName(u"button_bar")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.button_bar.sizePolicy().hasHeightForWidth())
        self.button_bar.setSizePolicy(sizePolicy1)
        self.button_bar.setStyleSheet(u"QFrame{\n"
"background-color: #1d1d1d;\n"
"padding: 5px\n"
"}\n"
"")
        self.button_bar.setFrameShape(QFrame.StyledPanel)
        self.button_bar.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.button_bar)
        self.horizontalLayout_3.setSpacing(10)
        self.horizontalLayout_3.setContentsMargins(10, 10, 10, 10)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(100, 0, 100, 0)
        self.buttonBox = QDialogButtonBox(self.button_bar)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)

        self.horizontalLayout_3.addWidget(self.buttonBox)


        self.verticalLayout_3.addWidget(self.button_bar)


        self.verticalLayout.addWidget(self.drop_shadow_frame)

#if QT_CONFIG(shortcut)
        self.lbl_red.setBuddy(self.red)
        self.lbl_green.setBuddy(self.green)
        self.lbl_blue.setBuddy(self.blue)
        self.lbl_hex.setBuddy(self.blue)
        self.lbl_alpha.setBuddy(self.blue)
#endif // QT_CONFIG(shortcut)
        QWidget.setTabOrder(self.red, self.green)
        QWidget.setTabOrder(self.green, self.blue)

        self.retranslateUi(ColorPicker)

        QMetaObject.connectSlotsByName(ColorPicker)
    # setupUi

    def retranslateUi(self, ColorPicker):
        ColorPicker.setWindowTitle(QCoreApplication.translate("ColorPicker", u"Form", None))
        self.window_title.setText(QCoreApplication.translate("ColorPicker", u"<strong>COLOR</strong> PICKER", None))
        self.exit_btn.setText("")
        self.black_ring.setText("")
        self.hue_selector.setText("")
        self.color_vis.setText("")
        self.lastcolor_vis.setText("")
        self.lbl_red.setText(QCoreApplication.translate("ColorPicker", u"R", None))
        self.red.setText(QCoreApplication.translate("ColorPicker", u"255", None))
        self.lbl_green.setText(QCoreApplication.translate("ColorPicker", u"G", None))
        self.green.setText(QCoreApplication.translate("ColorPicker", u"255", None))
        self.lbl_blue.setText(QCoreApplication.translate("ColorPicker", u"B", None))
        self.blue.setText(QCoreApplication.translate("ColorPicker", u"255", None))
        self.lbl_hex.setText(QCoreApplication.translate("ColorPicker", u"#", None))
        self.hex.setText(QCoreApplication.translate("ColorPicker", u"ffffff", None))
        self.lbl_alpha.setText(QCoreApplication.translate("ColorPicker", u"A", None))
        self.alpha.setText(QCoreApplication.translate("ColorPicker", u"100", None))
    # retranslateUi

