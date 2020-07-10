# -*- coding: cp1252 -*-
import os
import sys
import zipfile
import wx
import subprocess
from omegalib import *

#importer
#v1.13


def verifyPackage(omgFile):
    if not os.path.isfile(omgFile):
        msgBox("Exporter","The file is not a valid import package!","error")
        print "File " + omgFile + " does not exist!"
        return False
    if not zipfile.is_zipfile(omgFile):
        msgBox("Exporter","The file is not a valid import package!","error")
        print "File " + omgFile + " is not an archive!"
        return False
    return True



class GUI:
    def __init__(self):
        self.omegaLocation = getOmegaHome()
        if not self.omegaLocation:
            msgBox("Importer","Could not read O-MEGA Configuration Directory!","error")
            sys.exit(-1)
        self.installedTemplates = getInstalledTemplates()
        self.app = wx.App(False)

    def start(self):
        self.importTemplate()

    def importTemplate(self):
        #import
        dlg = wx.FileDialog(None, "Choose a template file", "C:\\", "", "*.omg", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            #print filename
            #print dirname
            dlg.Destroy()
            filename = os.path.join(dirname, filename)
            #print "FILENAME: " + filename
            goOn=True
            if verifyPackage(filename):
                conflictList = isTemplateConflicting(filename)
                if conflictList:
                    message = "Some Templates are already present!\n"
                    for conflict in conflictList:
                        message += "Template " + conflict[0] + " already exists in Version " + conflict[
                            2] + ". New Version is " + conflict[1] + "\n"
                    message += "Do you want to continue the import?"
                    if askYesNo("Conflict detected!", message) == False:
                        goOn=False
                if goOn:
                    makeBackup()
                if goOn and installPackage(filename):
                    msgBox("Importer","Import successfull!")
                else:
                    msgBox("Importer","Import failed!","error")
            else:
                msgBox("Importer","Import failed!","error")
        #start EG new
        if sys.argv[1] and checkIfEventGhostIsClosed():
            command=[sys.argv[1]]
            if sys.argv[2]:
                command.append(sys.argv[2])
            DETACHED_PROCESS = 8
            subprocess.Popen(command, creationflags=DETACHED_PROCESS, close_fds=True)
gui = GUI()
gui.start()
