
import cv2
import numpy as np
import os
import math
import time
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import datetime

#%%
WINDOW_SIZE_INIT = 200
CHANGE_VALUE_DRAWING = 3
CHANGE_VALUE_FOG = 3

#%%

class Brush:
    def __init__(self):
        self.size = 40
        self.radius = int(self.size / 2)
        self.shape = False

        self.x, self.y = np.mgrid[:2*self.radius, :2*self.radius]
        self.circle = (self.x - self.radius) ** 2 + (self.y - self.radius) ** 2
        self.circle_mask = (self.circle < self.radius ** 2).astype(int)
        self.circle_mask_neg = np.logical_not(self.circle_mask).astype(int)
        

#%%

class GUI:
    def __init__(self, master):
        self.master = master
        
        self.initGUI()
        
        self.brush = Brush()
        
        # images
        self.dm_image = np.zeros((WINDOW_SIZE_INIT,WINDOW_SIZE_INIT,3),np.uint8)
        self.player_image = np.zeros((WINDOW_SIZE_INIT,WINDOW_SIZE_INIT,3),np.uint8)
        self.img_w = 0
        self.img_h = 0
        self.overlay_player = 0
        self.overlay_dm = 0
        self.overlay_img = 0
        self.face_img = 0
        self.flag_picture_loaded = 0
        self.path = 0
        # alpha channel values for each overlay
        self.alpha_player = 255
        self.alpha_dm = 150
        
        # fog removal
        self.update_fog = False
        
        # other stuffos
        self.mouse_x = 0
        self.mouse_y = 0
        self.kill_loop = False
        self.rot_variable = 0
        
        # Zoom stuff
        self.flag_zoom = False
        self.rect_pnts = []
        self.zooming = False
        self.clone = 0
        self.no_zoomimg = 0
        
        # Draw
        self.draw_pnts = {}
        self.flag_draw = False
        self.flag_erase = False
        
            
    def initGUI(self):     
        # Set window size
        self.master.geometry('280x400')

        # Setting up tabs
        self.TAB_CONTROL = ttk.Notebook(self.master)
        # File load and save tab
        self.TAB_FILE = ttk.Frame(self.TAB_CONTROL)
        self.TAB_CONTROL.add(self.TAB_FILE, text='File')
        # Fog add/remove tab
        self.TAB_FOG = ttk.Frame(self.TAB_CONTROL)
        self.TAB_CONTROL.add(self.TAB_FOG, text='Fog')
        # Draw tab
        self.TAB_DRAW = ttk.Frame(self.TAB_CONTROL)
        self.TAB_CONTROL.add(self.TAB_DRAW, text='Draw')
        # 
        self.TAB_EXTRA = ttk.Frame(self.TAB_CONTROL)
        self.TAB_CONTROL.add(self.TAB_EXTRA, text='Extra')
        # Setup
        self.TAB_CONTROL.pack(expand=1, fill='both')
        
        ########################### FILE TAB #########################################
        # Load image button
        self.btn_load_image = tk.Button(self.TAB_FILE, text='Load image', command=self.selectImage)
        self.btn_load_image.place(x = 20, y = 30, width=120, height=30)
        # Write name and size of image
        self.filename_var = tk.StringVar()
        self.filename_var.set('Loaded image: ')
        self.text_filename = tk.Label(self.TAB_FILE, textvariable=self.filename_var, anchor='w')
        self.text_filename.place(x=20, y=60, width=200, height=20)
        
        # Load button
        self.btn_load_overlay = tk.Button(self.TAB_FILE, text='Load overlay', command=self.loadOverlay)
        self.btn_load_overlay.place(x=20, y=100, width=120, height=30)
        # Loading method chooser
        self.var_load = tk.IntVar()
        self.check_load = tk.Checkbutton(self.TAB_FILE, text='Load as addition', variable=self.var_load)
        self.check_load.place(x=20, y=130, width=120, height=30)
        # Save button
        self.btn_save = tk.Button(self.TAB_FILE, text='Save overlay', command=self.saveOverlay)
        self.btn_save.place(x=140, y=100, width=120, height=30)
        
        
        ########################## FOG TAB ###########################################
        # brush size
        self.text_brush = tk.Label(self.TAB_FOG, text='Brush size diameter [pixels]:')
        self.text_brush.place(x = 20, y = 20, width=240, height=30)
        self.sldr_brush = tk.Scale(self.TAB_FOG, from_=2, to=300, orient='horizontal')
        self.sldr_brush.bind('<ButtonRelease-1>', self.updateBrush)
        self.sldr_brush.set(40)
        self.sldr_brush.place(x = 20, y = 50, width=240, height=30)
        
        # fog add/remove chooser
        self.flag_fog = tk.IntVar()
        self.fog_choose = tk.Checkbutton(self.TAB_FOG, text='Add fog [W]', variable=self.flag_fog)
        self.fog_choose.place(x=140, y=100, width=120, height=30)
        # brush shape
        self.btn_shape = tk.Button(self.TAB_FOG, text='Square brush [S]', relief='raised', command=self.toggleBrush)
        self.btn_shape.place(x=20, y=100, width=120, height=30)
        
        # Remove all overlay
        self.btn_clearfog = tk.Button(self.TAB_FOG, text='Remove ALL fog', command=self.clearFog)
        self.btn_clearfog.place(x=20, y=150, width=120, height=30)
        # Add all overlay
        self.btn_addfog = tk.Button(self.TAB_FOG, text='Add ALL fog', command=self.addFog)
        self.btn_addfog.place(x=140, y=150, width=120, height=30)
        
        
        ########################## DRAW TAB ##########################################
        # Point size
        self.text_pnt = tk.Label(self.TAB_DRAW, text='Point size [pixels]:')
        self.text_pnt.place(x = 20, y = 20, width=240, height=30)
        self.sldr_pnt = tk.Scale(self.TAB_DRAW, from_=1, to=100, orient='horizontal', digits=1, resolution=1)
        self.sldr_pnt.set(5)
        self.sldr_pnt.place(x = 20, y = 50, width=240, height=30)
        # Draw button
        self.btn_draw = tk.Button(self.TAB_DRAW, text='Draw [Z]', command=self.toggleDraw)
        self.btn_draw.place(x=20, y=100, width=120, height=30)
        self.btn_erase = tk.Button(self.TAB_DRAW, text='Erase [V]', command=self.toggleErase)
        self.btn_erase.place(x=140, y=100, width=120, height=30)
        # Color sliders
        self.text_red = tk.Label(self.TAB_DRAW, text='Red')
        self.text_red.place(x = 20, y = 130, width=120, height=30)
        self.sldr_red = tk.Scale(self.TAB_DRAW, from_=0, to=255, orient='horizontal', digits=1, resolution=5)
        self.sldr_red.set(0)
        self.sldr_red.place(x = 140, y = 130, width=120, height=30)
        self.text_green = tk.Label(self.TAB_DRAW, text='Green')
        self.text_green.place(x = 20, y = 160, width=120, height=30)
        self.sldr_green = tk.Scale(self.TAB_DRAW, from_=0, to=255, orient='horizontal', digits=1, resolution=5)
        self.sldr_green.set(255)
        self.sldr_green.place(x = 140, y = 160, width=120, height=30)
        self.text_blue = tk.Label(self.TAB_DRAW, text='Blue')
        self.text_blue.place(x = 20, y = 190, width=120, height=30)
        self.sldr_blue = tk.Scale(self.TAB_DRAW, from_=0, to=255, orient='horizontal', digits=1, resolution=5)
        self.sldr_blue.set(0)
        self.sldr_blue.place(x = 140, y = 190, width=120, height=30)
        # Shapes
        self.btn_draw_circle = tk.Button(self.TAB_DRAW, text='Circle [C]', command=self.toggleDrawCircle)
        self.btn_draw_circle.place(x=20, y=230, width=120, height=30)
        self.btn_draw_cross = tk.Button(self.TAB_DRAW, text='Cross [X]', command=self.toggleDrawCross)
        self.btn_draw_cross.place(x=140, y=230, width=120, height=30)
        # Clear all
        self.btn_cleardraw = tk.Button(self.TAB_DRAW, text='Clear drawings [B]', command=self.clearDraw)
        self.btn_cleardraw.place(x=80, y=270, width=120, height=30)
        
        
        ########################## EXTRA TAB #########################################        
        # Zoom function
        self.sldr_zoom = tk.Scale(self.TAB_EXTRA, from_=1, to=5, orient='horizontal', digits=2, resolution=0.1)
        self.sldr_zoom.set(2)
        self.sldr_zoom.place(x = 140, y = 100, width = 120, height=30)
        # Begin zoom function
        self.btn_zoom = tk.Button(self.TAB_EXTRA, text='Zoom', command=self.zoom)
        self.btn_zoom.place(x = 20, y = 100, width = 120, height=30)
        
        # Rotating
        self.btn_rot_cw = tk.Button(self.TAB_EXTRA, text='Rotate CW', command=self.rotCW)
        self.btn_rot_cw.place(x=20, y=150, width=120, height=30)
        self.btn_rot_ccw = tk.Button(self.TAB_EXTRA, text='Rotate CCW', command=self.rotCCW)
        self.btn_rot_ccw.place(x=140, y=150, width=120, height=30)
        
        # Toggle grid
        self.var_grid = tk.IntVar()
        self.check_grid = tk.Checkbutton(self.TAB_EXTRA, text='Show grid', variable=self.var_grid)
        self.check_grid.place(x = 20, y = 210, width = 120, height = 30)
        self.sldr_grid = tk.Scale(self.TAB_EXTRA, from_=10, to=500, orient='horizontal', digits=1, resolution=10)
        self.sldr_grid.set(100)
        self.sldr_grid.place(x = 140, y = 210, width = 120, height = 30)
        
        ########################### QUIT BUTTON ######################################
        # Quit button
        self.btn_quit = tk.Button(self.master, text='Quit program', command=self.killAll)
        self.btn_quit.place(x=20, y=350, width=240, height=30)

    
    # DEFINING FUNCTIONS
    def drawRemoveFog(self, x, y):        
        flag_blend = False
        ymin = 0
        ymax = 0
        xmin = 0
        xmax = 0
        
        if(y > self.brush.radius and
                y < self.img_h - self.brush.radius and
                x > self.brush.radius and
                x < self.img_w - self.brush.radius):
            
            flag_blend = True
            ymin = y-self.brush.radius
            ymax = y+self.brush.radius
            xmin = x-self.brush.radius
            xmax = x+self.brush.radius
            
            if self.flag_fog.get():
                # Adding fog
                if self.brush.shape:
                    self.overlay_player[ymin:ymax,xmin:xmax,0] = self.alpha_player
                    self.overlay_dm[ymin:ymax,xmin:xmax,0] = self.alpha_dm
                else:
                    self.overlay_player[ymin:ymax,xmin:xmax,0] = np.logical_or(self.overlay_player[ymin:ymax,xmin:xmax,0],self.brush.circle_mask) * self.alpha_player
                    self.overlay_dm[ymin:ymax,xmin:xmax,0] = np.logical_or(self.overlay_dm[ymin:ymax,xmin:xmax,0],self.brush.circle_mask) * self.alpha_dm
            else:
                # Removing the area from the fog array
                if self.brush.shape:
                    self.overlay_player[ymin:ymax,xmin:xmax,0] = 0
                    self.overlay_dm[ymin:ymax,xmin:xmax,0] = 0
                else:
                    self.overlay_player[ymin:ymax,xmin:xmax,0] = np.logical_and(self.overlay_player[ymin:ymax,xmin:xmax,0],self.brush.circle_mask_neg) * self.alpha_player
                    self.overlay_dm[ymin:ymax,xmin:xmax,0] = np.logical_and(self.overlay_dm[ymin:ymax,xmin:xmax,0],self.brush.circle_mask_neg) * self.alpha_dm
            # For tracking the mouse
            self.mouse_x = x
            self.mouse_y = y
        
        return flag_blend, ymin, ymax, xmin, xmax
    
    # Remove-overlay drawing
    def fogUpdate(self, event, x, y, flags, params):
        if self.flag_picture_loaded:
            if event == cv2.EVENT_LBUTTONDOWN:
                self.update_fog = True
                flag_blend, ymin, ymax, xmin, xmax = self.drawRemoveFog(x, y)
                if flag_blend:
                    self.player_image[ymin:ymax,xmin:xmax,:] = self.blendFocused(self.overlay_player, ymin, ymax, xmin, xmax)
                    self.dm_image[ymin:ymax,xmin:xmax,:] = self.blendFocused(self.overlay_dm, ymin, ymax, xmin, xmax)
            elif event == cv2.EVENT_MOUSEMOVE:
                if self.update_fog is True:
                    flag_blend, ymin, ymax, xmin, xmax = self.drawRemoveFog(x, y)
                    if flag_blend:
                        self.player_image[ymin:ymax,xmin:xmax,:] = self.blendFocused(self.overlay_player, ymin, ymax, xmin, xmax)
                        self.dm_image[ymin:ymax,xmin:xmax,:] = self.blendFocused(self.overlay_dm, ymin, ymax, xmin, xmax)
                else:
                    self.mouse_x = x
                    self.mouse_y = y
            elif event == cv2.EVENT_MOUSEWHEEL:
                #sign of the flag shows direction of mousewheel
                if flags > 0:
                    self.changeBrushSizeHotKey(CHANGE_VALUE_FOG)
                else:
                    self.changeBrushSizeHotKey(-CHANGE_VALUE_FOG)
            elif event == cv2.EVENT_LBUTTONUP:
                self.update_fog = False

    
    # Reducing even further by only blending the relevant areas
    def blendFocused(self, overlay_input, ymin, ymax, xmin, xmax):        
        # Beginning blend
        background = 255-overlay_input[ymin:ymax,xmin:xmax,:]
        # Turn the masks into three channel, so we can use them as weights
        overlay_mask = cv2.cvtColor(overlay_input[ymin:ymax,xmin:xmax,:], cv2.COLOR_GRAY2BGR)
        background_mask = cv2.cvtColor(background, cv2.COLOR_GRAY2BGR)
        # Create a masked out face image, and masked out overlay
        # We convert the images to floating point in range 0.0 - 1.0
        face_part = self.face_img[ymin:ymax,xmin:xmax,:] * (background_mask * (1 / 255.0))
        overlay_part = self.overlay_img[ymin:ymax,xmin:xmax,:] * (overlay_mask * (1 / 255.0))
        # And finally just add them together, and rescale it back to an 8bit integer image    
        return np.uint8(cv2.addWeighted(face_part, 255.0, overlay_part, 255.0, 0.0))
    
    # Reducing computations of the blend, however require some more before-work
    def blendSimple(self, overlay_input):        
        # Beginning blend
        background = 255-overlay_input
        # Turn the masks into three channel, so we can use them as weights
        overlay_mask = cv2.cvtColor(overlay_input, cv2.COLOR_GRAY2BGR)
        background_mask = cv2.cvtColor(background, cv2.COLOR_GRAY2BGR)
        # Create a masked out face image, and masked out overlay
        # We convert the images to floating point in range 0.0 - 1.0
        face_part = self.face_img * (background_mask * (1 / 255.0))
        overlay_part = self.overlay_img * (overlay_mask * (1 / 255.0))
        # And finally just add them together, and rescale it back to an 8bit integer image    
        return np.uint8(cv2.addWeighted(face_part, 255.0, overlay_part, 255.0, 0.0))
    
    # For blending overlay (with alpha channel) with normal picture (no overlay necessary)
    def blend(self, face_img, overlay_t_img):
        # Split out the transparency mask from the colour info
        overlay_img = overlay_t_img[:,:,:3] # Grab the BRG planes
        overlay_mask = overlay_t_img[:,:,3:]  # And the alpha plane
        # Again calculate the inverse mask
        background_mask = 255 - overlay_mask
        # Turn the masks into three channel, so we can use them as weights
        overlay_mask = cv2.cvtColor(overlay_mask, cv2.COLOR_GRAY2BGR)
        background_mask = cv2.cvtColor(background_mask, cv2.COLOR_GRAY2BGR)
        # Create a masked out face image, and masked out overlay
        # We convert the images to floating point in range 0.0 - 1.0
        face_part = (face_img * (1 / 255.0)) * (background_mask * (1 / 255.0))
        overlay_part = (overlay_img * (1 / 255.0)) * (overlay_mask * (1 / 255.0))
        # And finally just add them together, and rescale it back to an 8bit integer image   
        return np.uint8(cv2.addWeighted(face_part, 255.0, overlay_part, 255.0, 0.0))
    
    def draw(self, event, x, y, flags, params):        
        if self.flag_picture_loaded:
            if event == cv2.EVENT_LBUTTONDOWN:
                if (x,y) not in self.draw_pnts:
                    self.draw_pnts[(x,y)] = ['point',(self.sldr_blue.get(),self.sldr_green.get(),self.sldr_red.get()),self.sldr_pnt.get()]
                self.flag_draw = True
            elif event == cv2.EVENT_MOUSEMOVE:
                if self.flag_draw:
                    if (x,y) not in self.draw_pnts:
                        self.draw_pnts[(x,y)] = ['point',(self.sldr_blue.get(),self.sldr_green.get(),self.sldr_red.get()),self.sldr_pnt.get()]
            elif event == cv2.EVENT_LBUTTONUP:
                self.flag_draw = False
            self.changeDrawSizeMouseWheel(event, flags, CHANGE_VALUE_DRAWING)
                    
    def drawCircle(self, event, x, y, flags, params):        
        if self.flag_picture_loaded:
            if event == cv2.EVENT_LBUTTONDOWN:
                if (x,y) not in self.draw_pnts:
                    self.draw_pnts[(x,y)] = ['circle',(self.sldr_blue.get(),self.sldr_green.get(),self.sldr_red.get()),self.sldr_pnt.get()]
        self.changeDrawSizeMouseWheel(event, flags, CHANGE_VALUE_DRAWING)
        
    def drawCross(self, event, x, y, flags, params):        
        if self.flag_picture_loaded:
            if event == cv2.EVENT_LBUTTONDOWN:
                if (x,y) not in self.draw_pnts:
                    self.draw_pnts[(x,y)] = ['cross',(self.sldr_blue.get(),self.sldr_green.get(),self.sldr_red.get()),self.sldr_pnt.get()]
        self.changeDrawSizeMouseWheel(event, flags, CHANGE_VALUE_DRAWING)
        
    def erase(self, event, x, y, flags, params):        
        if self.flag_picture_loaded:
            if event == cv2.EVENT_LBUTTONDOWN:
                for pnt in list(self.draw_pnts):
                    if math.sqrt((pnt[0]-x)**2+(pnt[1]-y)**2) < self.sldr_pnt.get():
                        del self.draw_pnts[pnt]
                self.flag_erase = True
            elif event == cv2.EVENT_MOUSEMOVE:
                if self.flag_erase:
                    for pnt in list(self.draw_pnts):
                        if math.sqrt((pnt[0]-x)**2+(pnt[1]-y)**2) < self.sldr_pnt.get():
                            del self.draw_pnts[pnt]
            elif event == cv2.EVENT_LBUTTONUP:
                self.flag_erase = False
        self.changeDrawSizeMouseWheel(event, flags, CHANGE_VALUE_DRAWING)
    
    # Button function in the tkinter window
    def selectImage(self):        
        # open a file chooser dialog and allow the user to select an input image
        self.path = filedialog.askopenfilename()
        if len(self.path) > 0:
            print('Chosen image: ' + str(self.path.split('/')[-1:])[2:-2])
            #### Loading chosen image ####
            img = cv2.imread(self.path,cv2.IMREAD_COLOR)
            
            # These are precalculated to reduce computations in the blend
            self.img_h = img.shape[0]
            self.img_w = img.shape[1]

            cv2.resizeWindow('Player window', self.img_w, self.img_h)
            cv2.resizeWindow('DM window', self.img_w, self.img_h)
            
            #### Setting up overlays and images for showing ####
            self.overlay_player = np.ones((img.shape[0],img.shape[1],1),np.uint8)*self.alpha_player
            self.overlay_dm = np.ones((img.shape[0],img.shape[1],1),np.uint8)*self.alpha_dm
            # These dont change, so they are precalculated to reduce computations
            self.overlay_img = np.zeros(img.shape,np.uint8) * (1 / 255.0) # OBS lol
            self.face_img = img * (1 / 255.0)
    
            # Initializing variables
            b_channel, g_channel, r_channel = cv2.split(np.zeros(img.shape,np.uint8))
            self.dm_image = self.blend(img,cv2.merge((b_channel, g_channel, r_channel, self.overlay_dm)))
            self.player_image = self.blend(img,cv2.merge((b_channel, g_channel, r_channel, self.overlay_player)))
            
            self.flag_picture_loaded = 1
            
            self.filename_var.set('Loaded image: ' + str(self.path.split('/')[-1:])[2:-2] + '    ' + '[' + str(self.img_w) + 'x' + str(self.img_h) + ']')
        else:
            print('No image chosen.')
    
    def saveOverlay(self):        
        if self.flag_picture_loaded:
            # just removing file extension, assuming only .jpg .png .jpeg
            if self.path[:-5] == '.jpeg':
                pathname = self.path[:-5]
            else:
                pathname = self.path[:-4]
    
            # Saving the numpy array
            currentDT = datetime.datetime.now()
            filename = pathname + '_overlay_{:d}x{:d}_{:d}{:d}{:d}_{:d}{:d}.npy'.format(self.img_w,self.img_h,currentDT.year,currentDT.month,currentDT.day,currentDT.hour,currentDT.minute)
            np.save(filename, self.overlay_dm/self.alpha_dm)
        else:
            print('No picture has been chosen yet.')
    
    def loadOverlay(self):        
        if self.flag_picture_loaded:
            path_overlay = filedialog.askopenfilename()
            if len(path_overlay) > 0:
                if path_overlay[-4:] == '.npy':
                    temp_overlay = np.load(path_overlay)
                    if (self.img_h == temp_overlay.shape[0]) and (self.img_w == temp_overlay.shape[1]):
                        if self.var_load.get():
                            self.overlay_dm = np.uint8(np.bitwise_and((self.overlay_dm > 0).astype(int),temp_overlay.astype(int))*self.alpha_dm)
                            self.overlay_player = np.uint8(np.bitwise_and((self.overlay_player > 0).astype(int),temp_overlay.astype(int))*self.alpha_player)
                        else:
                            self.overlay_dm = np.uint8(temp_overlay*self.alpha_dm)
                            self.overlay_player = np.uint8(temp_overlay*self.alpha_player)
                        # Blending
                        self.player_image = self.blendSimple(self.overlay_player)
                        self.dm_image = self.blendSimple(self.overlay_dm)
                    else:
                        print('Overlay size doesn\'t fit open image.')
                else:
                    print('Chosen file is not a numpy array (therefore not an overlay).')
        else:
            print('No picture has been chosen yet.')
    
    def killAll(self):        
        self.master.destroy()
        cv2.destroyAllWindows()
        self.kill_loop = True
        
    def updateBrush(self, val):        
        self.brush.size = self.sldr_brush.get()
        self.brush.radius = int(self.brush.size/2) # radius of brush
        
        if not self.brush.shape:
            self.brush.x, self.brush.y = np.mgrid[:2*self.brush.radius, :2*self.brush.radius]
            self.brush.circle = (self.brush.x - self.brush.radius) ** 2 + (self.brush.y - self.brush.radius) ** 2
            self.brush.circle_mask = (self.brush.circle < self.brush.radius ** 2).astype(int)
            self.brush.circle_mask_neg = np.logical_not(self.brush.circle_mask).astype(int)
    
    def clearFog(self):        
        if self.flag_picture_loaded:
            self.overlay_player.fill(0)
            self.overlay_dm.fill(0)
    
            self.player_image = self.blendSimple(self.overlay_player)
            self.dm_image = self.blendSimple(self.overlay_dm)
        else:
            print('No picture has been chosen yet.')
    
    def addFog(self):        
        if self.flag_picture_loaded:
            self.overlay_player.fill(self.alpha_player)
            self.overlay_dm.fill(self.alpha_dm)
    
            self.player_image = self.blendSimple(self.overlay_player)
            self.dm_image = self.blendSimple(self.overlay_dm)
        else:
            print('No picture has been chosen yet.')
    
    def toggleBrush(self):        
        self.brush.shape = not self.brush.shape
        self.updateBrush(True) # as it happens on buttonrelease event, it is necessary to pass dummy argument
        
        if self.btn_shape.config('relief')[-1] == 'sunken':
            self.btn_shape.config(relief='raised')
        else:
            self.btn_shape.config(relief='sunken')
    
    def toggleDraw(self):        
        if self.btn_draw.config('relief')[-1] == 'sunken':
            self.btn_draw.config(relief='raised')
            cv2.setMouseCallback('DM window',self.fogUpdate)
            self.flag_draw = False
        else:
            self.btn_draw.config(relief='sunken')
            cv2.setMouseCallback('DM window',self.draw)
            self.raiseOtherButtons(self.btn_draw)
    
    def toggleDrawCircle(self):        
        if self.btn_draw_circle.config('relief')[-1] == 'sunken':
            self.btn_draw_circle.config(relief='raised')
            cv2.setMouseCallback('DM window',self.fogUpdate)
        else:
            self.btn_draw_circle.config(relief='sunken')
            cv2.setMouseCallback('DM window',self.drawCircle)
            self.raiseOtherButtons(self.btn_draw_circle)
    
    def toggleDrawCross(self):        
        if self.btn_draw_cross.config('relief')[-1] == 'sunken':
            self.btn_draw_cross.config(relief='raised')
            cv2.setMouseCallback('DM window',self.fogUpdate)
        else:
            self.btn_draw_cross.config(relief='sunken')
            cv2.setMouseCallback('DM window',self.drawCross)
            self.raiseOtherButtons(self.btn_draw_cross)
    
    def toggleErase(self):        
        if self.btn_erase.config('relief')[-1] == 'sunken':
            self.btn_erase.config(relief='raised')
            cv2.setMouseCallback('DM window',self.fogUpdate)
            self.flag_erase = False
        else:
            self.btn_erase.config(relief='sunken')
            cv2.setMouseCallback('DM window',self.erase)
            self.raiseOtherButtons(self.btn_erase)
    
    def raiseOtherButtons(self, button):
        if button != self.btn_draw:
            self.btn_draw.config(relief='raised')
        if button != self.btn_erase:
            self.btn_erase.config(relief='raised')
        if button != self.btn_draw_circle:
            self.btn_draw_circle.config(relief='raised')
        if button != self.btn_draw_cross:
            self.btn_draw_cross.config(relief='raised')
    
    def clearDraw(self):
        self.draw_pnts = {}
    
    def zoomSelectPoints(self, event, x, y, flags, param):        
        if event == cv2.EVENT_LBUTTONDOWN:
            self.rect_pts = [(x, y)]
            self.zooming = True
    
        if event == cv2.EVENT_MOUSEMOVE:
            if self.zooming:
                clone2 = self.clone.copy()
                cv2.rectangle(clone2, self.rect_pts[0], (x,y), (0, 255, 0), 2)
                cv2.imshow('DM window',clone2)
    
        if event == cv2.EVENT_LBUTTONUP:
            self.rect_pts.append((x, y))
            # finding image area, and bounding it to the image dimensions
            ymin = np.amax([np.amin([self.rect_pts[0][1],self.rect_pts[1][1]]),0])
            ymax = np.amin([np.amax([self.rect_pts[0][1],self.rect_pts[1][1]]),self.img_h])
            xmin = np.amax([np.amin([self.rect_pts[0][0],self.rect_pts[1][0]]),0])
            xmax = np.amin([np.amax([self.rect_pts[0][0],self.rect_pts[1][0]]),self.img_w])
            
            if (xmax-xmin > 0) and (ymax-ymin > 0):
                zoomed_img = self.player_image[ymin:ymax,xmin:xmax,:]
                zoomed_img = cv2.resize(zoomed_img,None,fx=self.sldr_zoom.get(),fy=self.sldr_zoom.get())
    
                self.no_zoomimg += 1
                win_name_zoom = 'Zoom window ' + str(self.no_zoomimg)
                cv2.namedWindow(win_name_zoom)
                cv2.imshow(win_name_zoom, zoomed_img)
                cv2.setMouseCallback('DM window', self.fogUpdate)
                self.flag_zoom = False
                self.btn_zoom.config(relief='raised')
            else:
                print('Remember to mark area, keep mousebutton pressed for whole duration.')
            
            self.zooming = False
                
    def zoom(self):        
        if self.flag_picture_loaded:
            self.btn_zoom.config(relief='sunken')
    
            self.flag_zoom = True
            cv2.setMouseCallback('DM window', self.zoomSelectPoints)
            self.clone = self.dm_image.copy()
        else:
            print('No image loaded yet.')
    
    def rotCW(self):        
        self.rot_variable += 1
        
        if self.rot_variable >= 4:
            self.rot_variable = 0
    
    def rotCCW(self):        
        self.rot_variable -= 1
        
        if self.rot_variable <= -1:
            self.rot_variable = 3
    
    def showGrid(self, image):
        if self.var_grid.get():
            h_lines = np.arange(0,self.img_h,self.sldr_grid.get())
            v_lines = np.arange(0,self.img_w,self.sldr_grid.get())
            for line in h_lines:
                cv2.line(image,(0,line),(self.img_w,line),(175,175,175),1)
            for line in v_lines:
                cv2.line(image,(line,0),(line,self.img_h),(175,175,175),1)
    
    def drawShapes(self, image):
        '''
            draw_pnts[x]    0 - str, type of object
                            1 - tuple, color
                            2 - int, size
        '''
        for pnt in self.draw_pnts:
            if self.draw_pnts[pnt][0] == 'point':
                cv2.circle(image,pnt,self.draw_pnts[pnt][2],self.draw_pnts[pnt][1],-1)
            elif self.draw_pnts[pnt][0] == 'circle':
                cv2.circle(image,pnt,self.draw_pnts[pnt][2],self.draw_pnts[pnt][1],2)
            elif self.draw_pnts[pnt][0] == 'cross':
                cv2.line(image,(pnt[0]-self.draw_pnts[pnt][2],pnt[1]-self.draw_pnts[pnt][2]),(pnt[0]+self.draw_pnts[pnt][2],pnt[1]+self.draw_pnts[pnt][2]),self.draw_pnts[pnt][1],2)
                cv2.line(image,(pnt[0]+self.draw_pnts[pnt][2],pnt[1]-self.draw_pnts[pnt][2]),(pnt[0]-self.draw_pnts[pnt][2],pnt[1]+self.draw_pnts[pnt][2]),self.draw_pnts[pnt][1],2)
                
    def showFogBrush(self, image):
        if self.brush.shape:
            cv2.rectangle(image,(self.mouse_x-self.brush.radius,self.mouse_y-self.brush.radius),(self.mouse_x+self.brush.radius,self.mouse_y+self.brush.radius),(204,102,0),2)
        else:
            cv2.circle(image,(self.mouse_x,self.mouse_y),self.brush.radius,(204,102,0),2)
    
    def rotateScreen(self, image):
        if self.rot_variable == 1:
            image_shown = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        elif self.rot_variable == 2:
            image_shown = cv2.rotate(image, cv2.ROTATE_180)
        elif self.rot_variable == 3:
            image_shown = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            image_shown = image
        
        return image_shown
    
    def changeBrushSizeHotKey(self, change_val):
        self.brush.size += change_val
        self.sldr_brush.set(self.brush.size)
        self.updateBrush(True)
    
    def changeDrawSizeMouseWheel(self, event, flags, change_val):
        if event == cv2.EVENT_MOUSEWHEEL:
                #sign of the flag shows direction of mousewheel
                if flags > 0:
                    self.changeDrawSizeHotKey(change_val)
                else:
                    self.changeDrawSizeHotKey(-change_val)
    
    def changeDrawSizeHotKey(self, change_val):
        self.sldr_pnt.set(self.sldr_pnt.get()+change_val)
    
    def hotKeys(self, key):
        if (key & 0xFF) == 27:
            self.killAll()
        elif key == ord('w'):
            cv2.setMouseCallback('DM window', gui.fogUpdate)
            self.raiseOtherButtons(None)
            if self.flag_fog.get() == 1:
                self.flag_fog.set(0)
            else:
                self.flag_fog.set(1)
        elif key == ord('s'):
            self.toggleBrush()
        elif key == ord('a'):
            self.changeBrushSizeHotKey(-3)
        elif key == ord('d'):
            self.changeBrushSizeHotKey(3)
        elif key == ord('z'):
            self.toggleDraw()
            self.raiseOtherButtons(self.btn_draw)
        elif key == ord('x'):
            self.toggleDrawCross()
            self.raiseOtherButtons(self.btn_draw_cross)
        elif key == ord('c'):
            self.toggleDrawCircle()
            self.raiseOtherButtons(self.btn_draw_circle)
        elif key == ord('v'):
            self.toggleErase()
            self.raiseOtherButtons(self.btn_erase)
        elif key == ord('b'):
            self.clearDraw()

#%%
# Setup tkinter:
root = tk.Tk()
gui = GUI(root)



#%%
# Setup opencv
cv2.namedWindow('Player window', cv2.WINDOW_NORMAL)
cv2.namedWindow('DM window', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Player window', WINDOW_SIZE_INIT, WINDOW_SIZE_INIT)
cv2.resizeWindow('DM window', WINDOW_SIZE_INIT, WINDOW_SIZE_INIT)
cv2.setMouseCallback('DM window', gui.fogUpdate)

while(True):
    if not gui.flag_zoom:
        dm_image_shown = gui.dm_image.copy()
        player_image_shown = gui.player_image.copy()
        
        gui.showFogBrush(dm_image_shown)
        gui.drawShapes(dm_image_shown)
        gui.drawShapes(player_image_shown)
        gui.showGrid(dm_image_shown)
        gui.showGrid(player_image_shown)
        
        player_image_shown = gui.rotateScreen(player_image_shown)
        
        # Showing
        cv2.imshow('DM window',dm_image_shown)
        cv2.imshow('Player window',player_image_shown)
    
    else:
        gui.drawShapes(gui.clone)
        gui.showGrid(gui.clone)
        
        cv2.imshow('DM window', gui.clone)
    
    # And keeping the GUI running
    gui.master.update()
    
    key_press = cv2.waitKey(50)
    gui.hotKeys(key_press)
    
    if gui.kill_loop:
        break
