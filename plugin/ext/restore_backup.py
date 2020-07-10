# -*- coding: cp1252 -*-
import os
import sys
import zipfile
import wx
import shutil
from time import sleep
from omegalib import *
mswindows = (sys.platform == "win32")

#restore_backup
#v1.29


class GUI:
    def __init__(self):
        self.omegaLocation = getOmegaHome()
        if not self.omegaLocation:
            print "Could not read O-MEGA Installation Directory!"
            sys.exit(-1)
        self.app = wx.App(False)

    def start(self):
        if checkIfEventGhostIsClosed():
            self.restoreBackup()
        
    def getstatusoutput(cmd):
        """Return (status, output) of executing cmd in a shell."""
        if not mswindows:
            return commands.getstatusoutput(cmd)
        pipe = os.popen(cmd + ' 2>&1', 'r')
        text = pipe.read()
        sts = pipe.close()
        if sts is None: sts = 0
        if text[-1:] == '\n': text = text[:-1]
        return sts, text


    def deleteDir(path):
        """deletes the path entirely"""
        if mswindows: 
            cmd = "RMDIR "+ path +" /s /q"
        else:
            cmd = "rm -rf "+path
        result = self.getstatusoutput(cmd)
        if(result[0]!=0):
            #raise RuntimeError(result[1])
            msgBox("Backup Restorer",u"Could not delete a folder ("+path+u")!","error")
    
    def restoreBackup(self):
        dlg = wx.FileDialog(None, u"Choose a backup zip!", self.omegaLocation+u"\\backups", "", "*.zip", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            dlg.Destroy()
            filename = os.path.join(dirname, filename)
            #print "FILENAME: " + filename
            makeBackup()
            #remove web folder
            if os.path.exists(self.omegaLocation+u"\\web"):
                try:
                    shutil.rmtree(self.omegaLocation+u"\\web")
                    #self.deleteDir(self.omegaLocation+u"\\web")
                    
                except:
                    msgBox("Backup Restorer",u"Could not delete the webserver folder ("+self.omegaLocation+u"\\web)!","error")
                    return
                count=0
                while os.path.exists(self.omegaLocation+u"\\web"):
                    sleep(2)
                    count+=1
                    if count>10:
                        msgBox("Backup Restorer",u"Could not delete the webserver folder ("+self.omegaLocation+u"\\web)(2)!","error")
                        return
            #extract zip
            z=zipfile.ZipFile(filename,"r")
            try:
                os.mkdir(self.omegaLocation+"\\web")
                z.extractall(self.omegaLocation+"\\web")
            except:
                msgBox("Backup Restorer",u"Could not recreate the webserver folder ("+self.omegaLocation+u"\\web)!","error")
                return
            #remove and recover eg.xml
            try:
                os.remove(getEventghostXml())
                shutil.copyfile(self.omegaLocation+u"\\web\\EG.xml", getEventghostXml())
                os.remove(self.omegaLocation+u"\\web\\EG.xml")
            except:
                msgBox("Backup Restorer",u"Could not delete or recover "+getEventghostXml()+u", please recover "+getEventghostXml()+u" manually!","error")
            #remove and recover sg.xml
            try:
                os.remove(getSchedulghostXml())
                shutil.copyfile(self.omegaLocation+u"\\web\\SG.xml", getSchedulghostXml())
                os.remove(self.omegaLocation+u"\\web\\SG.xml")
            except:
                msgBox("Backup Restorer",u"Could not delete or recover "+getSchedulghostXml()+u", please recover "+getSchedulghostXml()+u" manually!","error")
            tmpStr = os.path.basename(filename)
            tmpStr = tmpStr.replace("O-Backup_", "")
            timestring = tmpStr.replace(".zip", "")
            #print "TIMESTRING: "+timestring
            msgBox("Backup Restorer","Restore successfull!")

gui = GUI()
gui.start()
