#!/usr/bin/env python
import wx

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

	# create buttons for auto mode
	self.spotButton = wx.Button(self, -1, "Spot")
	self.homeButton= wx.Button(self, -1, "Home")
	self.stopButton= wx.Button(self, -1, "Stop")
	self.startButton= wx.Button(self, -1, "Start")

	self.autoSizer = wx.BoxSizer(wx.HORIZONTAL)
	self.autoSizer.Add(self.startButton, 1, wx.EXPAND)
	self.autoSizer.Add(self.stopButton, 1, wx.EXPAND)
	self.autoSizer.Add(self.spotButton, 1, wx.EXPAND)
	self.autoSizer.Add(self.homeButton, 1, wx.EXPAND)

	# connection button
 	imgConName = "connect.png"
	imgCon = wx.Image(imgConName,wx.BITMAP_TYPE_ANY).ConvertToBitmap()
 	imgDisConName = "disconnect.png"
	imgDisCon = wx.Image(imgDisConName,wx.BITMAP_TYPE_ANY).ConvertToBitmap()
	self.connectButton = wx.BitmapButton(self, -1, bitmap=imgCon, size=(imgCon.GetWidth(), imgCon.GetHeight()))
	self.closeButton = wx.BitmapButton(self, -1, bitmap=imgDisCon, size=(imgDisCon.GetWidth(), imgDisCon.GetHeight()))
	self.connSizer = wx.BoxSizer(wx.HORIZONTAL)
	self.connSizer.Add(self.connectButton, 1, wx.EXPAND)
	self.connSizer.Add(self.closeButton, 1, wx.EXPAND)

	#overall layout
	self.modeSizer = wx.BoxSizer(wx.VERTICAL)
	self.modeSizer.Add(self.connSizer, 1, wx.EXPAND)
	self.modeSizer.Add(self.manualSizer, 1, flag=wx.ALIGN_CENTER)
	self.modeSizer.Add(self.autoSizer, 1, wx.EXPAND)
	self.SetSizer(self.modeSizer)
	self.SetAutoLayout(1)
	self.Show()
	
app = wx.App(False)
frame = MainWindow(None, "Robot Controller")
app.MainLoop()
