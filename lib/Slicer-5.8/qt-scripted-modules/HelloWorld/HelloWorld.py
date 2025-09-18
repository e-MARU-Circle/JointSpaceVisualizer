import slicer
from slicer.ScriptedLoadableModule import *
import logging
import qt

class HelloWorld(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Hello World"
        self.parent.categories = ["Examples"]
        self.parent.contributors = ["Test"]
        self.parent.helpText = "A minimal test module."

class HelloWorldWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        infoLabel = qt.QLabel("Hello World!")
        self.layout.addWidget(infoLabel)
        logging.info("Hello World module loaded successfully!")
