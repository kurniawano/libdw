#!/usr/bin/env python
import wx
import finch 
import kinematics as kn

WINDOW_WIDTH=400
WINDOW_HEIGHT=300

class MainWindow(wx.Frame):
    def __init__(self,parent,title):
	    wx.Frame.__init__(self,parent,title=title,size=(WINDOW_WIDTH,WINDOW_HEIGHT))
	    #create panel
	    #self.manualPanel = wx.Panel(self)
	    #add buttons to panel
 	    imgRotLName = "object_rotate_left.png"
            imgRotL = wx.Image(imgRotLName,wx.BITMAP_TYPE_ANY).ConvertToBitmap()
            imgRotRName = "object_rotate_right.png"
            imgRotR = wx.Image(imgRotRName,wx.BITMAP_TYPE_ANY).ConvertToBitmap()
            imgFwdName = "arrow_full_up_32.png"
            imgFwd= wx.Image(imgFwdName,wx.BITMAP_TYPE_ANY).ConvertToBitmap()
            imgStopManName = "media_playback_stop.png"
            imgStopMan= wx.Image(imgStopManName,wx.BITMAP_TYPE_ANY).ConvertToBitmap()
            self.rotLButton = wx.BitmapButton(self, -1, bitmap=imgRotL, size=(imgRotL.GetWidth()+15,imgRotL.GetHeight()+15))
            self.rotRButton = wx.BitmapButton(self, -1, bitmap=imgRotR, size=(imgRotR.GetWidth()+15,imgRotR.GetHeight()+15))
            self.fwdButton = wx.BitmapButton(self, -1, bitmap=imgFwd, size=(imgFwd.GetWidth()+10,imgFwd.GetHeight()+10))
            self.stopManButton = wx.BitmapButton(self, -1, bitmap=imgStopMan, size=(imgStopMan.GetWidth()+10,imgStopMan.GetHeight()+10))

	    #create sizer for manual panel	
            self.manualSizer = wx.GridBagSizer(hgap=3,vgap=2)
            self.manualSizer.Add(self.rotLButton,pos=(1,0))
            self.manualSizer.Add(self.fwdButton,pos=(0,1))
            self.manualSizer.Add(self.rotRButton,pos=(1,2))
            self.manualSizer.Add(self.stopManButton,pos=(1,1))

   	    # connection button
            self.connectButton = wx.ToggleButton(self, -1, label="Connection")


	    #overall layout
            self.modeSizer = wx.BoxSizer(wx.VERTICAL)
            self.modeSizer.Add(self.connectButton, 1, flag=wx.ALIGN_CENTER)
            self.modeSizer.Add(self.manualSizer, 1, flag=wx.ALIGN_CENTER)
            self.SetSizer(self.modeSizer)
            self.SetAutoLayout(1)

            #bind event to method
            self.Bind(wx.EVT_TOGGLEBUTTON, self.onConnect,self.connectButton) 
            self.Bind(wx.EVT_BUTTON, self.onButtonClicked, self.fwdButton)
            self.Bind(wx.EVT_BUTTON, self.onButtonClicked, self.stopManButton)
            self.Bind(wx.EVT_BUTTON, self.onButtonClicked, self.rotLButton)
            self.Bind(wx.EVT_BUTTON, self.onButtonClicked, self.rotRButton)
            self.Show()

    def onConnect(self,e):
        if self.connectButton.GetValue():
            self.finch= finch.Finch()
        else:
            self.finch.close()

    def onButtonClicked(self,e):
        obj=e.GetEventObject()
        try:
            f=self.finch
        except:
            e.Skip()
        if obj ==self.fwdButton:
            f.wheels(0.5, 0.5)
        elif obj == self.stopManButton:
            f.wheels(0,0)
        elif obj== self.rotLButton:
            omega=2.5
            vl,vr = kn.getLRVel(0, omega,kn.FINCH_L)
            nvl,nvr = kn.getNormLRVelFinch(vl,vr)
            f.wheels(nvl,nvr)
        elif obj==self.rotRButton:
            omega=-2.5
            vl,vr = kn.getLRVel(0, omega,kn.FINCH_L)
            nvl,nvr = kn.getNormLRVelFinch(vl,vr)
            f.wheels(nvl,nvr)
        


	
app = wx.App(False)
frame = MainWindow(None, "Robot Controller")
app.MainLoop()
