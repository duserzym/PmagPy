#!/usr/bin/env pythonw

#--------------------------------------------------------------
# converting magnetometer files to MagIC format
#--------------------------------------------------------------
import wx
import os
import pmag
import subprocess
import pmag_widgets as pw
import wx.grid
import subprocess
import ErMagicBuilder

class import_magnetometer_data(wx.Dialog):
    def __init__(self,parent,id,title,WD):
        wx.Dialog.__init__(self, parent, id, title)
        self.WD=WD
        self.InitUI()
        self.SetTitle(title)
        self.parent=parent
        
    def InitUI(self):

        self.panel = wx.Panel(self)
        vbox=wx.BoxSizer(wx.VERTICAL)

        formats=['generic format','SIO format','CIT format','2G-binary format','HUJI format','LDEO format','IODP SRM (csv) format','PMD (ascii) format','TDT format']
        sbs = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, 'step 1: choose file format' ), wx.VERTICAL )

        sbs.AddSpacer(5)
        self.oc_rb0 = wx.RadioButton(self.panel, -1,label=formats[0],name='0', style=wx.RB_GROUP)
        sbs.Add(self.oc_rb0)
        sbs.AddSpacer(5)
        sbs.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
        sbs.AddSpacer(5)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioButtonSelect, self.oc_rb0)
        

        for i in range(1,len(formats)):
            command="self.oc_rb%i = wx.RadioButton(self.panel, -1, label='%s', name='%i')"%(i,formats[i],i)
            exec command
            command="sbs.Add(self.oc_rb%i)"%(i)
            exec command
            sbs.AddSpacer(5)
            #
            command = "self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioButtonSelect, self.oc_rb%i)" % (i)
            exec command
            #

        self.oc_rb0.SetValue(True)
        self.checked_rb = self.oc_rb0


        
        #---------------------
        # OK/Cancel buttons
        #---------------------
                
        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton =  wx.Button(self.panel, id=-1, label='Import file')
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.nextButton = wx.Button(self.panel, id=-1, label='Next step')
        self.Bind(wx.EVT_BUTTON, self.on_nextButton, self.nextButton)
        hboxok.Add(self.okButton)
        hboxok.AddSpacer(20)
        hboxok.Add(self.cancelButton )
        hboxok.AddSpacer(20)
        hboxok.Add(self.nextButton )

        #-----------------------
        # design the frame
        #-----------------------
        
        vbox.AddSpacer(10)
        vbox.Add(sbs)
        vbox.AddSpacer(10)
        vbox.Add(hboxok)
        vbox.AddSpacer(10)

        hbox1=wx.BoxSizer(wx.HORIZONTAL)
        hbox1.AddSpacer(10)
        hbox1.Add(vbox)
        hbox1.AddSpacer(10)

        self.panel.SetSizer(hbox1)
        hbox1.Fit(self)

    def on_cancelButton(self,event):
        self.Destroy()

    def on_okButton(self,event):
        file_type = self.checked_rb.Label.split()[0] # extracts name of the checked radio button
        if file_type == 'generic':
            dia = convert_generic_files_to_MagIC(self,self.WD)
        elif file_type == 'SIO':
            dia = convert_SIO_files_to_MagIC(self, self.WD)
        elif file_type == 'CIT':
            dia = convert_CIT_files_to_MagIC(self, self.WD)
        elif file_type == '2G-binary':
            dia = convert_2G_binary_files_to_MagIC(self, self.WD)
        elif file_type == 'HUJI':
            dia = convert_HUJI_files_to_MagIC(self, self.WD)
        elif file_type == 'LDEO':
            dia = convert_LDEO_files_to_MagIC(self, self.WD)
        elif file_type == 'IODP':
            dia = convert_IODP_csv_files_to_MagIC(self, self.WD)
        elif file_type == 'PMD':
            dia = convert_PMD_files_to_MagIC(self, self.WD)
        elif file_type == 'TDT':
            COMMAND = "TDT_magic.py -WD {}".format(self.WD)
            os.system(COMMAND)
            return True
        dia.Center()
        dia.Show()


    def OnRadioButtonSelect(self, event):
        self.checked_rb = event.GetEventObject()


    def on_nextButton(self,event):
        self.Destroy()
        combine_dia = combine_magic_dialog(self.WD)
        combine_dia.Show()
        combine_dia.Center()
        
#--------------------------------------------------------------
# MagIC generic files conversion
#--------------------------------------------------------------


class convert_generic_files_to_MagIC(wx.Frame):
    """"""
    title = "PmagPy generic file conversion"

    def __init__(self,parent,WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.panel.SetScrollbars(20, 20, 50, 50)
        self.max_files=1
        self.WD=WD
        self.parent=parent
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        #---sizer infor ----

        TEXT="convert generic file to MagIC format"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)
            

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)
        
        #---sizer 1 ----
        self.bSizer1 = pw.labeled_text_field(pnl)

        #---sizer 2 ----
        # unique because only accepts 1 experiment type
        TEXT="Experiment:"
        self.bSizer2 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.HORIZONTAL)
        self.gridBSizer = wx.GridBagSizer(5, 10)
        self.label1 = wx.StaticText(pnl, label=TEXT)
        self.experiments_names=['Demag (AF and/or Thermal)','Paleointensity-IZZI/ZI/ZI','ATRM 6 positions','AARM 6 positions','cooling rate','TRM']
        self.protocol_info = wx.ComboBox(self.panel, -1, self.experiments_names[0], size=(300,25),choices=self.experiments_names, style=wx.CB_READONLY)
        self.gridBSizer.Add(self.label1, (0, 0))
        self.gridBSizer.Add(self.protocol_info, (1, 0))
        self.bSizer2.Add(self.gridBSizer, wx.ALIGN_LEFT)
        #
        self.Bind(wx.EVT_COMBOBOX, self.on_select_protocol, self.protocol_info)
        self.bSizer2a = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.HORIZONTAL )
        text = 'Cooling Rate, format is xxx,yyy,zzz with no spaces  '
        self.cooling_rate = wx.TextCtrl(pnl)
        self.bSizer2a.AddMany([wx.StaticText(pnl, label=text), self.cooling_rate])
        

        #---sizer 3 ----
        self.bSizer3 = pw.lab_field(pnl)

        #---sizer 4 ----
        # unique because only allows 4 choices (most others have ncn choices)
        self.bSizer4 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        self.sample_naming_conventions=['sample=specimen','no. of initial characters','no. of terminal characters','character delimited']
        self.sample_naming_convention = wx.ComboBox(self.panel, -1, self.sample_naming_conventions[0], size=(250,25), choices=self.sample_naming_conventions, style=wx.CB_READONLY)
        self.sample_naming_convention_char = wx.TextCtrl(self.panel, id=-1, size=(40,25))
        gridbSizer4 = wx.GridSizer(2, 2, 0, 10)
        gridbSizer4.AddMany( [(wx.StaticText(self.panel,label="specimen-sample naming convention",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (wx.StaticText(self.panel,label="delimiter/number (if necessary)",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (self.sample_naming_convention,wx.ALIGN_LEFT),
            (self.sample_naming_convention_char,wx.ALIGN_LEFT)])
        #bSizer4.Add(self.sample_specimen_text,wx.ALIGN_LEFT)
        self.bSizer4.AddSpacer(10)
        self.bSizer4.Add(gridbSizer4,wx.ALIGN_LEFT)
        
        #---sizer 5 ----

        self.bSizer5 = wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        self.site_naming_conventions=['site=sample','no. of initial characters','no. of terminal characters','character delimited']
        self.site_naming_convention_char = wx.TextCtrl(self.panel, id=-1, size=(40,25))
        self.site_naming_convention = wx.ComboBox(self.panel, -1, self.site_naming_conventions[0], size=(250,25), choices=self.site_naming_conventions, style=wx.CB_READONLY)
        gridbSizer5 = wx.GridSizer(2, 2, 0, 10)
        gridbSizer5.AddMany( [(wx.StaticText(self.panel,label="sample-site naming convention",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (wx.StaticText(self.panel,label="delimiter/number (if necessary)",style=wx.TE_CENTER),wx.ALIGN_LEFT),
            (self.site_naming_convention,wx.ALIGN_LEFT),
            (self.site_naming_convention_char,wx.ALIGN_LEFT)])
        self.bSizer5.AddSpacer(10)
        self.bSizer5.Add(gridbSizer5,wx.ALIGN_LEFT)

        #---sizer 6 ----

        TEXT="Location name:"
        self.bSizer6 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 7 ----
        self.bSizer7 = pw.replicate_measurements(pnl)

        #---buttons ---
        
        hboxok = pw.btn_panel(self, pnl)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer2a, flag=wx.ALIGN_LEFT|wx.TOP, border=5)

        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=5)
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP|wx.BOTTOM, border=5)
        vbox.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(5)


        self.hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        self.hbox_all.AddSpacer(20)
        self.hbox_all.AddSpacer(vbox)
        self.hbox_all.AddSpacer(20)
        
        self.panel.SetSizer(self.hbox_all)
        self.bSizer2a.ShowItems(False)
        self.hbox_all.Fit(self)
        self.Show()
        self.Centre()


    def on_select_protocol(self, event):
        if self.protocol_info.GetValue() == "cooling rate":
            self.bSizer2a.ShowItems(True)
        else:
            self.bSizer2a.ShowItems(False)
        self.hbox_all.Fit(self)


    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, self.WD, event, text)


    def on_okButton(self,event):

        # generic_magic.py -WD WD - f FILE -fsa er_samples.txt -F OUTFILE.magic -exp [Demag/PI/ATRM 6/AARM 6/CR  -samp X Y -site  X Y -loc LOCNAME -dc B PHI THETA [-A] -WD path 
        
        ErrorMessage=""
        #-----------
        FILE = str(self.bSizer0.file_path.GetValue())

        #-----------
        # WD="/".join(FILE.split("/")[:-1])
        WD=self.WD
        magicoutfile=os.path.split(FILE)[1]+".magic"
        print "magicoutfile", magicoutfile
        OUTFILE=os.path.join(self.WD,magicoutfile)
        #-----------
        #OUTFILE=self.WD+"/"+FILE.split('/')[-1]+".magic"
        #-----------
        EXP=""
        exp=str(self.protocol_info.GetValue())
        if exp=='Demag (AF and/or Thermal)': 
            EXP='Demag'
        elif exp=='Paleointensity-IZZI/ZI/ZI': 
            EXP='PI'
        elif exp=='ATRM 6 positions': 
            EXP='ATRM 6'
        elif exp=='AARM 6 positions': 
            EXP = 'AARM 6'
        elif exp=='cooling rate': 
            cooling = self.cooling_rate.GetValue()
            EXP='CR {}'.format(cooling)
        #-----------
        SAMP="1 0" #default
        
        samp_naming_convention=str(self.sample_naming_convention.GetValue())
        try:
            samp_naming_convention_char=int(self.sample_naming_convention_char.GetValue())
        except:
             samp_naming_convention_char="0"
                    
        if samp_naming_convention=='sample=specimen':
            SAMP="1 0"
        elif samp_naming_convention=='no. of initial characters':
            SAMP="0 %i"%int(samp_naming_convention_char)
        elif samp_naming_convention=='no. of terminal characters':
            SAMP="1 %s"%samp_naming_convention_char
        elif samp_naming_convention=='character delimited':
            SAMP="2 %s"%samp_naming_convention_char
                        
        #-----------
        
        SITE="1 0" #default
        
        sit_naming_convention=str(self.site_naming_convention.GetValue())
        try:
            sit_naming_convention_char=int(self.site_naming_convention_char.GetValue())
        except:
             sit_naming_convention_char="0"
                    
        if sit_naming_convention=='sample=specimen':
            SITE="1 0"
        elif sit_naming_convention=='no. of initial characters':
            SITE="0 %i"%int(sit_naming_convention_char)
        elif sit_naming_convention=='no. of terminal characters':
            SITE="1 %s"%sit_naming_convention_char
        elif sit_naming_convention=='character delimited':
            SITE="2 %s"%sit_naming_convention_char
        
        #-----------        

        if str(self.bSizer6.return_value()) != "":
            LOC="-loc \"%s\""%str(self.bSizer6.return_value())
        else:
            LOC=""
        #-----------        
        
        LABFIELD=" "
        try:
            B_uT, DEC, INC = self.bSizer3.return_value().split()
        except ValueError:
            B_uT, DEC, INC = '', '', ''

        if EXP != "Demag":
            LABFIELD="-dc "  +B_uT+ " " + DEC + " " + INC

        #-----------        

        DONT_AVERAGE=" "
        if not self.bSizer7.return_value():
            DONT_AVERAGE="-A"   

        #-----------   
        # some special  
        
        SAMP_OUTFILE = magicoutfile[:magicoutfile.find('.')] + "_er_samples.txt"
        COMMAND="generic_magic.py -WD %s -f %s -fsa er_samples.txt -F %s -exp %s  -samp %s -site %s %s %s %s -Fsa %s"\
        %(WD,FILE,OUTFILE,EXP,SAMP,SITE,LOC,LABFIELD,DONT_AVERAGE, SAMP_OUTFILE)

        print "-I- Running Python command:\n %s"%COMMAND

        #subprocess.call(COMMAND, shell=True)        
        os.system(COMMAND)                                          
        #--
        MSG="file converted to MagIC format file:\n%s.\n\n See Termimal (Mac) or command prompt (windows) for errors"% OUTFILE
        dlg1 = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()

        self.Destroy()
        self.parent.Raise()


    def on_cancelButton(self,event):
        self.Destroy()
        self.parent.Raise()
        
    def on_helpButton(self, event):
        pw.on_helpButton("generic_magic.py -h")

    def get_sample_name(self,specimen,sample_naming_convenstion):
        if sample_naming_convenstion[0]=="sample=specimen":
            sample=specimen
        elif sample_naming_convenstion[0]=="no. of terminal characters":
            n=int(sample_naming_convenstion[1])*-1
            sample=specimen[:n]
        elif sample_naming_convenstion[0]=="character delimited":
            d=sample_naming_convenstion[1]
            sample_splitted=specimen.split(d)
            if len(sample_splitted)==1:
                sample=sample_splitted[0]
            else:
                sample=d.join(sample_splitted[:-1])
        return sample
                            
    def get_site_name(self,sample,site_naming_convenstion):
        if site_naming_convenstion[0]=="site=sample":
            site=sample
        elif site_naming_convenstion[0]=="no. of terminal characters":
            n=int(site_naming_convenstion[1])*-1
            site=sample[:n]
        elif site_naming_convenstion[0]=="character delimited":
            d=site_naming_convenstion[1]
            site_splitted=sample.split(d)
            if len(site_splitted)==1:
                site=site_splitted[0]
            else:
                site=d.join(site_splitted[:-1])
        
        return site
        
#--------------------------------------------------------------
# dialog for combine_magic.py 
#--------------------------------------------------------------


class combine_magic_dialog(wx.Frame):
    """"""
    title = "Combine magic files"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel =  wx.ScrolledWindow(self) #wx.Panel(self)
        self.panel.SetScrollbars(20, 20, 50, 50)
        self.max_files = 1
        self.WD=WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        #---sizer infor ----

        TEXT="Step 2: \nCombine different MagIC formatted files to one file named 'magic_measurements.txt'"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)
            

        #---sizer 0 ----
        bSizer0 =  wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.HORIZONTAL )
        #self.file_path = wx.TextCtrl(self.panel, id=-1, size=(400,25), style=wx.TE_READONLY)
        self.add_file_button = wx.Button(self.panel, id=-1, label='add file',name='add')
        self.Bind(wx.EVT_BUTTON, self.on_add_file_button, self.add_file_button)    
        self.add_all_files_button = wx.Button(self.panel, id=-1, label="add all files with '.magic' suffix",name='add_all')
        self.Bind(wx.EVT_BUTTON, self.on_add_all_files_button, self.add_all_files_button)    
        #TEXT="Choose file (no spaces are alowd in path):"
        #bSizer0.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_CENTER)
        bSizer0.AddSpacer(5)
        bSizer0.Add(self.add_file_button,wx.ALIGN_LEFT)
        bSizer0.AddSpacer(5)
        bSizer0.Add(self.add_all_files_button,wx.ALIGN_LEFT)
        bSizer0.AddSpacer(5)
                
        #------------------

        bSizer1 =  wx.StaticBoxSizer( wx.StaticBox( self.panel, wx.ID_ANY, "" ), wx.VERTICAL )
        self.file_paths = wx.TextCtrl(self.panel, id=-1, size=(500,200), style=wx.TE_MULTILINE)
        #self.add_file_button = wx.Button(self.panel, id=-1, label='add',name='add')
        #self.Bind(wx.EVT_BUTTON, self.on_add_file_button, self.add_file_button)    
        TEXT="files list:"
        bSizer1.AddSpacer(5)
        bSizer1.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)        
        bSizer1.AddSpacer(5)
        bSizer1.Add(self.file_paths,wx.ALIGN_LEFT)
        bSizer1.AddSpacer(5)
                
        #------------------
                     
        self.okButton = wx.Button(self.panel, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        self.nextButton = wx.Button(self.panel, id=-1, label='Skip')
        self.Bind(wx.EVT_BUTTON, self.on_nextButton, self.nextButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        hboxok.Add(self.okButton)
        hboxok.Add(self.cancelButton )
        hboxok.Add(self.nextButton )

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(bSizer0, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(bSizer1, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(5)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)
        
        self.panel.SetSizer(hbox_all)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()
                        
    
    def on_add_file_button(self,event):

        dlg = wx.FileDialog(
            None,message="choose MagIC formatted measurement file",
            defaultDir=self.WD,
            defaultFile="",
            style=wx.OPEN | wx.CHANGE_DIR 
            )
        if dlg.ShowModal() == wx.ID_OK:
            full_path = dlg.GetPath()
            infile = full_path[full_path.rfind('/')+1:]
            self.file_paths.AppendText(infile + "\n")

    def on_add_all_files_button(self,event):
        all_files=os.listdir(self.WD)
        for F in all_files:
            F=str(F)
            if len(F)>6:
                if F[-6:]==".magic":
                    self.file_paths.AppendText(F+"\n")
                     
        
        
    def on_cancelButton(self,event):
        self.Destroy()

    def on_nextButton(self, event):
        combine_dia = combine_everything_dialog(self.WD)
        combine_dia.Show()
        combine_dia.Center()
        self.Destroy()

    def on_okButton(self,event):
        files_text=self.file_paths.GetValue()
        files=files_text.strip('\n').replace(" ","").split('\n')
        COMMAND="combine_magic.py -F magic_measurements.txt -f %s"%(" ".join(files) )       
        print "-I- Running Python command:\n %s"%COMMAND
        os.chdir(self.WD)     
        os.system(COMMAND)                                          
        MSG="%i file are merged to one MagIC format file:\n magic_measurements.txt.\n\n See Termimal (Mac) or command prompt (windows) for errors"%(len(files))
        dlg1 = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()
        self.on_nextButton(event)
        self.Destroy()




class combine_everything_dialog(wx.Frame):
    """"""
    title = "Combine er_* files"

    def __init__(self,WD):
        wx.Frame.__init__(self, None, wx.ID_ANY, self.title)
        self.panel =  wx.ScrolledWindow(self) #wx.Panel(self)
        self.panel.SetScrollbars(20, 20, 50, 50)
        self.max_files = 1
        self.WD=WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        #---sizer infor ----

        TEXT="Step 3: \nCombine different MagIC formatted files to one file name (if necessary).  All files should be from the working directory."
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl,label=TEXT),wx.ALIGN_LEFT)
            
        self.bSizer0 = pw.combine_files(self, "er_specimens.txt")
        self.bSizer1 = pw.combine_files(self, "er_samples.txt")
        self.bSizer2 = pw.combine_files(self, "er_sites.txt")
        
        #------------------
                     
        self.okButton = wx.Button(self.panel, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.on_okButton, self.okButton)

        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        hboxok.Add(self.okButton)
        hboxok.Add(self.cancelButton )

        hboxfiles = wx.BoxSizer(wx.HORIZONTAL)
        hboxfiles.AddMany([self.bSizer0, self.bSizer1, self.bSizer2])

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.AddSpacer(10)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.BOTTOM, border=5)
        vbox.AddSpacer(10)
        vbox.Add(hboxfiles, flag=wx.ALIGN_LEFT)
        vbox.AddSpacer(10)
        vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(5)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)
        
        self.panel.SetSizer(hbox_all)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()
                        

    def on_cancelButton(self,event):
        self.Destroy()

    def on_okButton(self,event):
        er_specimens = self.bSizer0.file_paths.GetValue()
        er_samples = self.bSizer1.file_paths.GetValue()
        er_sites = self.bSizer2.file_paths.GetValue()
        spec_files = " ".join(er_specimens.split('\n'))
        samp_files = " ".join(er_samples.split('\n'))
        site_files = " ".join(er_sites.split('\n'))
        new_files = []
        if spec_files:
            COMMAND0="combine_magic.py -F er_specimens.txt -f %s"%(spec_files)
            print "-I- Running Python command:\n %s"%COMMAND0
            os.system(COMMAND0) 
            new_files.append("er_specimens.txt")
        if samp_files:
            COMMAND1="combine_magic.py -F er_samples.txt -f %s"%(samp_files)
            print "-I- Running Python command:\n %s"%COMMAND1
            os.system(COMMAND1) 
            new_files.append("er_samples.txt")
        if site_files:
            COMMAND2="combine_magic.py -F er_sites.txt -f %s"%(site_files)
            print "-I- Running Python command:\n %s"%COMMAND2
            os.system(COMMAND2)
            new_files.append("er_sites.txt")
        new = '\n' + '\n'.join(new_files)
        MSG = "Created new file(s): {} \nSee Termimal (Mac) or command prompt (windows) for details and errors".format(new)
        dlg1 = wx.MessageDialog(None,caption="Message:", message=MSG ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()
        self.Destroy()





class convert_SIO_files_to_MagIC(wx.Frame):
    """stuff"""
    title = "PmagPy SIO file conversion"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.panel.SetScrollbars(20, 20, 50, 50)
        self.max_files = 1 # but maybe it could take more??
        self.WD=WD
        self.InitUI()


    def InitUI(self):
        pnl = self.panel

        TEXT = "SIO Format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)
#        bSizer_info.Add(wx.StaticText(self), wx.ALIGN_LEFT)

        self.bSizer0 = pw.choose_file(pnl, method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.labeled_text_field(pnl)

        #---sizer 2 ----
        self.bSizer2 = pw.experiment_type(pnl)

        #---sizer 3 ----
        self.bSizer3 = pw.lab_field(pnl)

        #---sizer 4 ----
        self.bSizer4 = pw.specimen_n(pnl)

        #---sizer 4a ----
        self.bSizer4a = pw.select_ncn(pnl)

        #---sizer 5 ----
        TEXT="Location name:"
        self.bSizer5 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 6 ---
        TEXT="Instrument name (optional):"
        self.bSizer6 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 7 ----
        self.bSizer7 = pw.replicate_measurements(pnl)

        #---sizer 8 ----

        TEXT = "peak AF field (mT) if ARM: "
        self.bSizer8 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 9 ----

        TEXT = "Coil number for ASC impulse coil (if treatment units in Volts): "
        self.bSizer9 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 10 ---
        self.bSizer10 = pw.synthetic(pnl)

        #---buttons ----
        hboxok = pw.btn_panel(self, pnl)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.Add(self.bSizer5, flag=wx.ALIGN_LEFT)
        hbox0.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        #hbox0a = wx.BoxSizer(wx.HORIZONTAL)
        #hbox0a.Add(self.bSizer4, flag=wx.ALIGN_LEFT)
        #hbox0a.Add(self.bSizer4a, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)
        hbox1 =wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.bSizer8, flag=wx.ALIGN_LEFT)
        hbox1.Add(self.bSizer9, flag=wx.ALIGN_LEFT|wx.LEFT, border=5)

        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        #vbox.Add(hbox0a, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer4a, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(hbox0, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(hbox1, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(self.bSizer10, flag=wx.ALIGN_LEFT|wx.TOP, border=8)
        vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
        vbox.AddSpacer(20)


        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)
        
        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()
        

    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, self.WD, event, text)

    def on_okButton(self, event):
        SIO_file = self.bSizer0.return_value()
        #outfile = SIO_file + '.magic'
        magicoutfile=os.path.split(SIO_file)[1]+".magic"
        outfile =os.path.join(self.WD,magicoutfile)
        samp_outfile = magicoutfile[:magicoutfile.find('.')] + "_er_samples.txt"
        user = self.bSizer1.return_value()
        if user:
            user = "-usr " + user
        experiment_type = self.bSizer2.return_value()
        if experiment_type:
            experiment_type = "-LP " + experiment_type
        lab_field = self.bSizer3.return_value()
        if lab_field:
            lab_field = "-dc " + lab_field
        spc = self.bSizer4.return_value()
        ncn = self.bSizer4a.return_value()
        loc_name = self.bSizer5.return_value()
        if loc_name:
            loc_name = "-loc " + loc_name
        instrument = self.bSizer6.return_value()
        if instrument:
            instrument = "-ins " + instrument
        replicate = self.bSizer7.return_value()
        if replicate:
            replicate = ''
        else:
            replicate = '-A'
        peak_AF = self.bSizer8.return_value()
        if peak_AF:
            peak_AF = "-ac " + peak_AF
        coil_number = self.bSizer9.return_value()
        if coil_number:
            coil_number = "-V " + coil_number
        synthetic = self.bSizer10.return_value()
        if synthetic:
            synthetic = '-syn ' + synthetic
        else:
            synthetic = ''
        COMMAND = "sio_magic.py -F {0} -f {1} {2} {3} {4} -spc {5} -ncn {6} {7} {8} {9} {10} {11} {12} -Fsa {13}".format(outfile, SIO_file, user, experiment_type, loc_name,spc, ncn, lab_field, peak_AF, coil_number, instrument, replicate, synthetic, samp_outfile)
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton("sio_magic.py -h")



class convert_CIT_files_to_MagIC(wx.Frame):
    """stuff"""
    title = "PmagPy CIT file conversion"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.max_files = 1 # but maybe it could take more??
        self.WD = WD
        self.InitUI()


    def InitUI(self):
        pnl = self.panel

        TEXT = "CIT Format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        TEXT="Measurer (optional):"
        self.bSizer1 = pw.labeled_text_field(pnl, TEXT)
        
        #---sizer 2 ----
        self.bSizer2 = pw.sampling_particulars(pnl)

        #---sizer 3 ----
        self.bSizer3 = pw.lab_field(pnl)

        #---sizer 4 ----
        self.bSizer4 = pw.select_ncn(pnl)

        #---sizer 5 ---
        TEXT = "specify number of characters to designate a specimen, default = 0"
        self.bSizer5 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 6 ----
        TEXT="Location name:"
        self.bSizer6 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 7 ---
        TEXT = "peak AF field (mT) if ARM: "
        self.bSizer7 = pw.labeled_text_field(pnl, TEXT)


        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)

        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(20)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)
        
        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()


    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, self.WD, event, text)

    def on_okButton(self, event):
        wd = self.WD
        full_file = self.bSizer0.return_value()
        ind = full_file.rfind('/')
        CIT_file = full_file[ind+1:] 
        input_directory = full_file[:ind+1]
        if input_directory:
            ID = "-ID " + input_directory
        else:
            ID = ''
        outfile = CIT_file + ".magic"
        samp_outfile = CIT_file[:CIT_file.find('.')] + "_er_samples.txt"
        spec_outfile = CIT_file[:CIT_file.find('.')] + "_er_specimens.txt"
        site_outfile = CIT_file[:CIT_file.find('.')] + "_er_sites.txt"
        user = self.bSizer1.return_value()
        if user:
            user = "-usr " + user
        spec_num = self.bSizer5.return_value()
        if spec_num:
            spec_num = "-spc " + spec_num
        else:
            spec_num = "-spc 0" # defaults to 0 if user doesn't choose number
        loc_name = self.bSizer6.return_value()
        if loc_name:
            loc_name = "-loc " + loc_name
        ncn = self.bSizer4.return_value()
        particulars = self.bSizer2.return_value()
        if particulars:
            particulars = "-mcd " + particulars
        lab_field = self.bSizer3.return_value()
        if lab_field:
            lab_field = "-dc " + lab_field
        peak_AF = self.bSizer7.return_value()
        if peak_AF:
            peak_AF = "-ac " + peak_AF
        COMMAND = "CIT_magic.py -WD {} -f {} -F {} {} {} {} {} -ncn {} {} {} {} -Fsp {} -Fsi {} -Fsa {}".format(wd, CIT_file, outfile, particulars, spec_num, loc_name, user, ncn, peak_AF, lab_field, ID, spec_outfile, site_outfile, samp_outfile)
        #print COMMAND
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton("CIT_magic.py -h")



class convert_HUJI_files_to_MagIC(wx.Frame):

    """ """
    title = "PmagPy HUJI file conversion"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        TEXT = "HUJI format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.labeled_text_field(pnl)

        #---sizer 2 ----
        self.bSizer2 = pw.experiment_type(pnl)

        #---sizer 3 ----
        self.bSizer3 = pw.lab_field(pnl)

        #---sizer 4 ----
        self.bSizer4 = pw.select_ncn(pnl)

        #---sizer 5 ---
        TEXT = "specify number of characters to designate a specimen, default = 0"
        self.bSizer5 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 6 ----
        TEXT="Location name:"
        self.bSizer6 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 7 ---
        TEXT = "peak AF field (mT) if ARM: "
        self.bSizer7 = pw.labeled_text_field(pnl, TEXT)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)

        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(20)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)
        
        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()


    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, self.WD, event, text)

    def on_okButton(self, event):
        """
        grab user input values, format them, and run HUJI_magic.py with the appropriate flags
        """
        HUJI_file = self.bSizer0.return_value()
        magicoutfile=os.path.split(HUJI_file)[1]+".magic"
        outfile=os.path.join(self.WD,magicoutfile)
        user = self.bSizer1.return_value()
        if user:
            user = '-usr ' + user
        experiment_type = self.bSizer2.return_value()
        if not experiment_type:
            pw.simple_warning("You must select an experiment type")
            return False
        lab_field = self.bSizer3.return_value()
        if lab_field:
            lab_field = '-dc ' + lab_field
        ncn = self.bSizer4.return_value()
        spc = self.bSizer5.return_value()
        if not spc:
            spc = '-spc 0'
        else:
            spc = '-spc ' + spc
        loc_name = self.bSizer6.return_value()
        if loc_name:
            loc_name = '-loc ' + loc_name
        peak_AF = self.bSizer7.return_value()
        COMMAND = "HUJI_magic.py -f {} -F {} {} -LP {} {} -ncn {} {} {} {}".format(HUJI_file, outfile, user, experiment_type, loc_name, ncn, lab_field, spc, peak_AF)
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton("HUJI_magic.py -h")


class convert_2G_binary_files_to_MagIC(wx.Frame):

    """PmagPy 2G-binary conversion """
    title = "PmagPy 2G-binary file conversion"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        TEXT = "Folder containing one or more 2G-binary format files"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        #self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)
        self.bSizer0 = pw.choose_dir(pnl, btn_text = 'add', method = self.on_add_dir_button)

        #---sizer 1 ----
        self.bSizer1 = pw.sampling_particulars(pnl)

        #---sizer 2 ----
        ncn_keys = ['XXXXY', 'XXXX-YY', 'XXXX.YY', 'XXXX[YYY] where YYY is sample designation, enter number of Y', 'sample name=site name', 'Site is entered under a separate column', '[XXXX]YYY where XXXX is the site name, enter number of X']
        self.bSizer2 = pw.select_ncn(pnl, ncn_keys)

        #---sizer 3 ----
        TEXT = "specify number of characters to designate a specimen, default = 1"
        self.bSizer3 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 4 ----
        self.bSizer4 = pw.select_specimen_ocn(pnl)

        #---sizer 5 ----
        TEXT="Location name:"
        self.bSizer5 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 6 ---
        TEXT="Instrument name (optional):"
        self.bSizer6 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 7 ----
        self.bSizer7 = pw.replicate_measurements(pnl)


        #---buttons ---
        hboxok = pw.btn_panel(self, pnl) # creates ok, cancel, help buttons and binds them to appropriate methods

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)

        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(20)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)
        
        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()

    #---button methods ---

    def on_add_dir_button(self,event):
        text = "choose directory of files to convert to MagIC"
        pw.on_add_dir_button(self.panel, self.WD, event, text)

    def on_okButton(self, event):
        WD = self.WD
        directory = self.bSizer0.return_value()
        files = os.listdir(directory)
        files = [str(f) for f in files if str(f).endswith('.dat')]
        ID = "-ID " + directory
        if self.bSizer1.return_value():
            particulars = self.bSizer1.return_value()
            mcd = '-mcd ' + particulars
        else:
            mcd = ''
        ncn = self.bSizer2.return_value()
        spc = self.bSizer3.return_value()
        if not spc:
            spc = '-spc 1'
        else:
            spc = '-spc ' + spc
        ocn = self.bSizer4.return_value()
        loc_name = self.bSizer5.return_value()
        if loc_name:
            loc_name = "-loc " + loc_name
        instrument = self.bSizer6.return_value()
        if instrument:
            instrument = "-ins " + instrument
        replicate = self.bSizer7.return_value()
        if replicate:
            replicate = '-a'
        else:
            replicate = ''
        samp_outfile = files[0][:files[0].find('.')] + "_" + files[-1][:files[-1].find('.')] + "_er_samples.txt"
        sites_outfile = files[0][:files[0].find('.')] + "_" + files[-1][:files[-1].find('.')] + "_er_sites.txt"
        for f in files:
            file_2G_bin = f
            outfile = file_2G_bin + ".magic"
            COMMAND = "2G_bin_magic.py -WD {} -f {} -F {} -Fsa {} -Fsi {} -ncn {} {} {} -ocn {} {} {} {}".format(WD, file_2G_bin, outfile, samp_outfile, sites_outfile, ncn, mcd, spc, ocn, loc_name, replicate, ID)
            if files.index(f) == (len(files) - 1): # terminate process on last file call
                pw.run_command_and_close_window(self, COMMAND, outfile)
            else:
                pw.run_command(self, COMMAND, outfile)



    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton("2G_bin_magic.py -h")



class convert_LDEO_files_to_MagIC(wx.Frame):

    """ """
    title = "PmagPy LDEO file conversion"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        TEXT = "LDEO format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.labeled_text_field(pnl)

        #---sizer 2 ---
        self.bSizer2 = pw.experiment_type(pnl)
        
        #---sizer 3 ----
        self.bSizer3 = pw.lab_field(pnl)

        #---sizer 4 ----
        self.bSizer4 = pw.select_ncn(pnl)

        #---sizer 5 ----
        TEXT = "specify number of characters to designate a specimen, default = 0"
        self.bSizer5 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 6 ---
        TEXT="Location name:"
        self.bSizer6 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 7 ---
        TEXT="Instrument name (optional):"
        self.bSizer7 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 8 ---
        self.bSizer8 = pw.replicate_measurements(pnl)

        #---sizer 9 ----
        TEXT = "peak AF field (mT) if ARM: "
        self.bSizer9 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 10 ---
        TEXT = "Coil number for ASC impulse coil (if treatment units in Volts): "
        self.bSizer10 = pw.labeled_text_field(pnl, TEXT)

        #---sizer 11 ---
        self.bSizer11 = pw.synthetic(pnl)
        

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.RIGHT, border=5)
        hbox0.Add(self.bSizer7, flag=wx.ALIGN_LEFT)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.bSizer9, flag=wx.ALIGN_LEFT|wx.RIGHT, border=5)
        hbox1.Add(self.bSizer10, flag=wx.ALIGN_LEFT)

        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer8, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(hbox1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer11, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.AddSpacer(10)
        vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER|wx.BOTTOM, border=20)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)
        
        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()


    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, self.WD, event, text)

    def on_okButton(self, event):
        LDEO_file = self.bSizer0.return_value()
        magicoutfile=os.path.split(LDEO_file)[1]+".magic"
        outfile=os.path.join(self.WD,magicoutfile)
        samp_outfile = os.path.join(self.WD, magicoutfile[:magicoutfile.find('.')] + '_er_samples.txt')
        synthetic_outfile = os.path.join(self.WD, magicoutfile[:magicoutfile.find('.')] + '_er_synthetics.txt')
        user = self.bSizer1.return_value()
        if user:
            user = "-usr " + user
        experiment_type = self.bSizer2.return_value()
        if experiment_type:
            experiment_type = "-LP " + experiment_type
        lab_field = self.bSizer3.return_value()
        if lab_field:
            lab_field = "-dc " + lab_field
        ncn = self.bSizer4.return_value()
        spc = self.bSizer5.return_value()
        if spc:
            spc = "-spc " + spc
        else:
            spc = "-spc 0"
        loc_name = self.bSizer6.return_value()
        if loc_name:
            loc_name = "-loc " + loc_name
        instrument = self.bSizer7.return_value()
        if instrument:
            instrument = "-ins " + instrument
        replicate = self.bSizer8.return_value()
        if replicate:
            replicate = ""
        else:
            replicate = "-A"
        AF_field = self.bSizer9.return_value()
        if AF_field:
            AF_field = "-ac " + AF_field
        coil_number = self.bSizer10.return_value()
        if coil_number:
            coil_number = "-V " + coil_number
        synthetic = self.bSizer11.return_value()
        if synthetic:
            synthetic = '-syn ' + synthetic
        else:
            synthetic = ''
        COMMAND = "LDEO_magic.py -f {0} -F {1} {2} {3} {4} -ncn {5} {6} {7} {8} {9} {10} {11} {12} -Fsa {13} -Fsy {14}".format(LDEO_file, outfile, user, experiment_type, lab_field, ncn, spc, loc_name, instrument, replicate, AF_field, coil_number, synthetic, samp_outfile, synthetic_outfile)
        #print COMMAND
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton("LDEO_magic.py -h")




class convert_IODP_csv_files_to_MagIC(wx.Frame):

    """ """
    title = "PmagPy IODP csv conversion"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        TEXT = "IODP csv format file"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        self.bSizer1 = pw.replicate_measurements(pnl)
        
        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)

        vbox.AddSpacer(10)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.AddSpacer(10)
        #vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(20)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)
        
        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()


    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, self.WD, event, text)

    def on_okButton(self, event):
        wd = self.WD
        full_file = self.bSizer0.return_value()
        index = full_file.rfind('/')
        IODP_file = full_file[index+1:]
        outfile = IODP_file + ".magic"
        ID = full_file[:index+1] 
        spec_outfile = IODP_file[:IODP_file.find('.')] + "_er_specimens.txt" 
        samp_outfile = IODP_file[:IODP_file.find('.')] + "_er_samples.txt" 
        site_outfile = IODP_file[:IODP_file.find('.')] + "_er_sites.txt"
        replicate = self.bSizer1.return_value()
        if replicate:
            replicate = ''
        else:
            replicate = "-A"
        COMMAND = "IODP_csv_magic.py -WD {0} -f {1} -F {2} {3} -ID {4} -Fsp {5} -Fsa {6} -Fsi {7}".format(wd, IODP_file, outfile, replicate, ID, spec_outfile, samp_outfile, site_outfile)
        #print COMMAND
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton("-h")



# template for an import window
class convert_PMD_files_to_MagIC(wx.Frame):

    """ """
    title = "PmagPy PMD (ascii) file conversion"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        TEXT = "Folder containing one or more PMD format files"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_dir(pnl, 'add', method = self.on_add_dir_button)

        #---sizer 1 ----
        self.bSizer1 = pw.labeled_text_field(pnl)
        
        #---sizer 2 ----
        ncn_keys = ['XXXXY', 'XXXX-YY', 'XXXX.YY', 'XXXX[YYY] where YYY is sample designation, enter number of Y', 'sample name=site name', 'Site is entered under a separate column', '[XXXX]YYY where XXXX is the site name, enter number of X']
        self.bSizer2 = pw.select_ncn(pnl, ncn_keys)

        #---sizer 3 ---
        #        TEXT = "specify number of characters to designate a specimen, default = 0"
        #        self.bSizer3 = pw.labeled_text_field(pnl, TEXT)
        self.bSizer3 = pw.specimen_n(pnl)


        #---sizer 4 ----
        TEXT="Location name:"
        self.bSizer4 = pw.labeled_text_field(pnl, TEXT)


        #---sizer 5 ----
        self.bSizer5 = pw.sampling_particulars(pnl)

        #---sizer 6 ---
        self.bSizer6 = pw.replicate_measurements(pnl)

        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)

        #------
        vbox=wx.BoxSizer(wx.VERTICAL)

        vbox.AddSpacer(10)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.AddSpacer(10)
        #vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(20)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)
        
        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()


    def on_add_dir_button(self,event):
        text = "choose directory of files to convert to MagIC"
        pw.on_add_dir_button(self.panel, self.WD, event, text)

    def on_okButton(self, event):
        WD = self.WD
        directory = self.bSizer0.return_value()
        files = os.listdir(directory)
        files = [str(f) for f in files if str(f).endswith('.pmd')]
        if files:
            samp_outfile = files[0][:files[0].find('.')] + files[-1][:files[-1].find('.')] + "_er_samples.txt"
        else:
            raise Exception("No pmd files found in {}, try a different directory".format(WD))
        ID = "-ID " + directory
        user = self.bSizer1.return_value()
        if user:
            user = "-usr " + user
        ncn = self.bSizer2.return_value()
        spc = self.bSizer3.return_value() or 0
        loc_name = self.bSizer4.return_value()
        if loc_name:
            loc_name = "-loc " + loc_name
        particulars = self.bSizer5.return_value()
        if particulars:
            particulars = "-mcd " + particulars
        replicate = self.bSizer6.return_value()
        if replicate:
            replicate = ''
        else:
            replicate = '-A'
        for f in files:
            outfile = f + ".magic"
            samp_outfile = f[:f.find('.')] + "_er_samples.txt"
            COMMAND = "PMD_magic.py -WD {} -f {} -F {} -Fsa {} {} -ncn {} {} -spc {} {} {}".format(WD, f, outfile, samp_outfile, user, ncn, particulars, spc, replicate, ID)
            if files.index(f) == len(files) -1:
                pw.run_command_and_close_window(self, COMMAND, outfile)
            else:
                pw.run_command(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton("PMD_magic.py -h")





# template for an import window
class something(wx.Frame):

    """ """
    title = "PmagPy ___ file conversion"

    def __init__(self, parent, WD):
        wx.Frame.__init__(self, parent, wx.ID_ANY, self.title)
        self.panel = wx.ScrolledWindow(self)
        self.WD = WD
        self.InitUI()

    def InitUI(self):

        pnl = self.panel

        TEXT = "Hello here is a bunch of text"
        bSizer_info = wx.BoxSizer(wx.HORIZONTAL)
        bSizer_info.Add(wx.StaticText(pnl, label=TEXT), wx.ALIGN_LEFT)

        #---sizer 0 ----
        self.bSizer0 = pw.choose_file(pnl, 'add', method = self.on_add_file_button)

        #---sizer 1 ----
        
        #---sizer 2 ----

        #---sizer 3 ----

        #---sizer 4 ----

        #---sizer 5 ---

        #---sizer 6 ----

        #---sizer 7 ---


        #---buttons ---
        hboxok = pw.btn_panel(self, pnl)


        #------
        vbox=wx.BoxSizer(wx.VERTICAL)

        vbox.AddSpacer(10)
        vbox.Add(bSizer_info, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        vbox.Add(self.bSizer0, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer1, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer2, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer3, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer4, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer5, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer6, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.Add(self.bSizer7, flag=wx.ALIGN_LEFT|wx.TOP, border=10)
        #vbox.AddSpacer(10)
        #vbox.Add(wx.StaticLine(pnl), 0, wx.ALL|wx.EXPAND, 5)
        vbox.Add(hboxok, flag=wx.ALIGN_CENTER)        
        vbox.AddSpacer(20)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)
        
        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()


    def on_add_file_button(self,event):
        text = "choose file to convert to MagIC"
        pw.on_add_file_button(self.bSizer0, self.WD, event, text)

    def on_okButton(self, event):
        COMMAND = ""
        pw.run_command_and_close_window(self, COMMAND, outfile)

    def on_cancelButton(self,event):
        self.Destroy()
        self.Parent.Raise()

    def on_helpButton(self, event):
        pw.on_helpButton("-h")


#=================================================================
# demag_orient:
# read/write demag_orient.txt
# calculate sample orientation
#=================================================================

class OrientFrameGrid(wx.Frame):

    def __init__(self,parent,id,title,WD,Data_hierarchy,size):
        wx.Frame.__init__(self, parent, -1, title, size=size)
        
        #--------------------
        # initialize stuff
        #--------------------
        
        self.WD=WD
        self.Data_hierarchy=Data_hierarchy
        
        #--------------------
        # menu bar
        #--------------------
        
        self.menubar = wx.MenuBar()
        menu_file = wx.Menu()
        m_open_file = menu_file.Append(-1, "&Open orientation file", "")
        self.Bind(wx.EVT_MENU, self.on_m_open_file, m_open_file)
        m_save_file = menu_file.Append(-1, "&Save orientation file", "")
        self.Bind(wx.EVT_MENU, self.on_m_save_file, m_save_file)
        m_calc_orient = menu_file.Append(-1, "&Calculate samples orientation", "")
        self.Bind(wx.EVT_MENU, self.on_m_calc_orient, m_calc_orient)
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

        #--------------------
        # get the orientation data
        # 1) from file  demag_orient.txt
        # 2) from Data_hierarchy
        # and save it to self.orient_data={}
        #--------------------

        self.samples_list=self.Data_hierarchy['samples']         
        self.orient_data={}
        try:
            self.orient_data=self.read_magic_file(self.WD+"/demag_orient.txt",1,"sample_name")  
        except:
            pass
        for sample in self.samples_list:
            if sample not in self.orient_data.keys():
               self.orient_data[sample]={} 
               self.orient_data[sample]["sample_name"]=sample
               
            if sample in Data_hierarchy['site_of_sample'].keys():
                self.orient_data[sample]["site_name"]=Data_hierarchy['site_of_sample'][sample]
            else:
                self.orient_data[sample]["site_name"]=""

        #--------------------
        # create the grid sheet
        #--------------------
                                    
        self.create_sheet()
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        # save the template
        self.on_m_save_file(None)
        self.Show()                

        TEXT="A template for a file named 'demag_orient.txt', which contains samples orientation data was created in MagIC working directory.\n\n"
        TEXT=TEXT+"You can view/modify demag_orient.txt using this Python frame, or using Excel.\n\n"
        TEXT=TEXT+"If you choose to use Excel:\n"
        TEXT=TEXT+"1) Fill in data.\n"        
        TEXT=TEXT+"2) Save file as 'tab delimited'\n"
        TEXT=TEXT+"3) Import demag_orient.txt to the Python frame by choosing from the menu-bar: File -> Open orientation file\n\n"
        TEXT=TEXT+"After orientation data is filled in the Python frame choose from the menu-bar: File -> Calculate samples orientations"
        dlg1 = wx.MessageDialog(self,caption="Message:", message=TEXT ,style=wx.OK)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            dlg1.Destroy()    
    
            
    def create_sheet(self):    
        '''
        creat an editable grid showing deamg_orient.txt 
        '''
        #--------------------------------
        # orient.tx support many other headers
        # but here I put only 
        # the essential headers for 
        # sample orientation
        #--------------------------------
        
        self.headers=["sample_orientation_flag",
                 "sample_name",
                 #"site_name",
                 "mag_azimuth",
                 "field_dip",
                 "bedding_dip_direction",
                 "bedding_dip",
                 "shadow_angle",
                 "lat",
                 "long",
                 "date",
                 "hhmm",
                 "GPS_baseline",
                 "GPS_Az",
                 #"participants",
                 #"magic_method_codes"
                 ]

        #--------------------------------
        # create the grid
        #--------------------------------
        
        samples_list=self.orient_data.keys()
        samples_list.sort()
        self.samples_list = [ sample for sample in samples_list if sample is not "" ] 
        self.grid = wx.grid.Grid(self, -1)        
        self.grid.ClearGrid()
        self.grid.CreateGrid(len(self.samples_list), len(self.headers))

        #--------------------------------
        # color the columns by groups 
        #--------------------------------
        
        for i in range(len(self.samples_list)):
            self.grid.SetCellBackgroundColour(i, 0, "LIGHT GREY")
            self.grid.SetCellBackgroundColour(i, 1, "LIGHT STEEL BLUE")
            self.grid.SetCellBackgroundColour(i, 2, "YELLOW")
            self.grid.SetCellBackgroundColour(i, 3, "YELLOW")
            self.grid.SetCellBackgroundColour(i, 4, "PALE GREEN")
            self.grid.SetCellBackgroundColour(i, 5, "PALE GREEN")
            self.grid.SetCellBackgroundColour(i, 6, "LIGHT BLUE")
            self.grid.SetCellBackgroundColour(i, 7, "LIGHT BLUE")
            self.grid.SetCellBackgroundColour(i, 8, "LIGHT BLUE")
            self.grid.SetCellBackgroundColour(i, 9, "LIGHT BLUE")
            self.grid.SetCellBackgroundColour(i, 10, "LIGHT BLUE")
            self.grid.SetCellBackgroundColour(i, 11, "LIGHT MAGENTA")
            self.grid.SetCellBackgroundColour(i, 12, "LIGHT MAGENTA")
        
        #--------------------------------
        # fill headers names
        #--------------------------------
        
        for i in range(len(self.headers)):
            self.grid.SetColLabelValue(i, self.headers[i])

        #--------------------------------
        # fill data from self.orient_data
        #--------------------------------
        
        for sample in self.samples_list:
            for key in self.orient_data[sample].keys():
                if key in self.headers:
                    sample_index=self.samples_list.index(sample)
                    i=self.headers.index(key)
                    self.grid.SetCellValue(sample_index,i, self.orient_data[sample][key])
                        
        #--------------------------------

        self.grid.AutoSize()
        
                
    def on_m_open_file(self,event):
        '''
        open orient.txt
        read the data
        display the data from the file in a new grid
        '''
        dlg = wx.FileDialog(
            self, message="choose orient file",
            defaultDir=self.WD, 
            defaultFile="",
            style=wx.OPEN | wx.CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            orient_file = dlg.GetPath()
            dlg.Destroy()
            new_data=self.read_magic_file(orient_file,1,"sample_name") 
            if len(new_data)>0:
                self.orient_data={}
                self.orient_data=new_data
            self.create_sheet()

    def on_m_save_file(self,event):
        
        '''
        save demag_orient.txt
        (only the columns that appear on the grid frame)
        '''
        
        fout=open(self.WD+"/demag_orient.txt",'w')
        STR="tab\tdemag_orient\n"
        fout.write(STR)
        STR="\t".join(self.headers)+"\n"
        fout.write(STR)
        for sample in self.samples_list:
            STR=""
            for header in self.headers:                
                sample_index=self.samples_list.index(sample)
                i=self.headers.index(header)
                value=self.grid.GetCellValue(sample_index,i)
                STR=STR+value+"\t"
            fout.write(STR[:-1]+"\n")
        if event!=None: 
            dlg1 = wx.MessageDialog(None,caption="Message:", message="data saved in file demag_orient.txt" ,style=wx.OK|wx.ICON_INFORMATION)
            dlg1.ShowModal()
            dlg1.Destroy()
        
    def read_magic_file(self,path,ignore_lines_n,sort_by_this_name):
        '''
        read magic file and store the data in dictionary:
        Data={}
        Data[sort_by_this_name]={}
        '''

        DATA={}
        fin=open(path,'rU')
        #ignore first lines
        for i in range(ignore_lines_n):
            fin.readline()
        #header
        line=fin.readline()
        header=line.strip('\n').split('\t')
        #print header
        for line in fin.readlines():
            if line[0]=="#":
                continue
            tmp_data={}
            tmp_line=line.strip('\n').split('\t')
            #print tmp_line
            for i in range(len(tmp_line)):
                if i>= len(header):
                    continue
                tmp_data[header[i]]=tmp_line[i]
            DATA[tmp_data[sort_by_this_name]]=tmp_data
        fin.close()        
        return(DATA)
                

    def on_m_calc_orient(self,event):    
        '''
        This fucntion does exactly what the 'import orientation' fuction does in MagIC.py 
        after some dialog boxes the fucntio calls orientation_magic.py 
        '''
        
        # first see if demag_orient.txt
        self.on_m_save_file(None)
        orient_convention_dia=orient_convention(None)
        orient_convention_dia.Center()
        #orient_convention_dia.ShowModal()
        if orient_convention_dia.ShowModal() == wx.ID_OK:
            ocn_flag=orient_convention_dia.ocn_flag
            dcn_flag=orient_convention_dia.dcn_flag
            gmt_flags=orient_convention_dia.gmt_flags
            orient_convention_dia.Destroy()
        
        method_code_dia=method_code_dialog(None)
        method_code_dia.Center()
        if method_code_dia.ShowModal()== wx.ID_OK:
            bedding_codes_flags=method_code_dia.bedding_codes_flags
            methodcodes_flags=method_code_dia.methodcodes_flags
            method_code_dia.Destroy()
        #logfile=open(self.WD+"/orientation_magic.log",'w')
        command_args=['orientation_magic.py']
        command_args.append("-WD %s"%self.WD)
        command_args.append("-Fsa er_samples_orient.txt")
        command_args.append("-Fsi er_sites_orient.txt ")
        command_args.append("-f %s"%"demag_orient.txt")
        command_args.append(ocn_flag)
        command_args.append(dcn_flag)
        command_args.append(gmt_flags)
        command_args.append(bedding_codes_flags)
        command_args.append(methodcodes_flags) 
        commandline=" ".join(command_args)
        
                 
        #command= "orientation_magic.py -WD %s -Fsa er_samples_orient.txt -Fsi er_sites_orient.txt -f  %s %s %s %s %s %s > ./orientation_magic.log " \
        #%(self.WD,\
        #"demag_orient.txt",\
        #ocn_flag,\
        #dcn_flag,\
        #gmt_flags,\
        #bedding_codes_flags,\
        #methodcodes_flags)
        
        #orient_convention_dia.Destroy()
        #method_code_dia.Destroy()  
        
        fail_comamnd=False
        
        print "-I- executing command: %s" %commandline
        os.chdir(self.WD)
        try:
             os.system(commandline)
             #subprocess.call(command_args,shell=True,stdout=logfile)
             #logfile.close()
        except:
            fail_comamnd=True
        
        if fail_comamnd:
            print "-E- ERROR: Error in running orientation_magic.py"
            return
 
        # check if orientation_magic.py finished sucsessfuly
        data_saved=False
        if os.path.isfile(self.WD+"/er_samples_orient.txt"):
            data_saved=True
            #fin=open(self.WD+"/orientation_magic.log",'r')
            #for line in fin.readlines():
            #    if "Data saved in" in line:
            #        data_saved=True
            #        break 
        
        if not data_saved:
            return
        
        # check if er_samples.txt exists. 
        # If yes add/change the following columns:
        # 1) sample_azimuth,sample_dip
        # 2) sample_bed_dip, sample_bed_dip_direction
        # 3) sample_date,
        # 4) sample_declination_correction
        # 5) add magic_method_codes
        
        er_samples_data={}
        er_samples_orient_data={}
        if os.path.isfile(self.WD+"/er_samples.txt"):
            er_samples_file=self.WD+"/er_samples.txt"
            er_samples_data=self.read_magic_file(er_samples_file,1,"er_sample_name")
        
        if os.path.isfile(self.WD+"/er_samples_orient.txt"):             
            er_samples_orient_file=self.WD+"/er_samples_orient.txt"
            er_samples_orient_data=self.read_magic_file(er_samples_orient_file,1,"er_sample_name")
        new_samples_added=[]
        for sample in er_samples_orient_data.keys():
            if sample not in er_samples_data.keys():
                new_samples_added.append(sample)
                er_samples_data[sample]={}
                er_samples_data[sample]['er_sample_name']=sample
              #er_samples_data[sample]['er_citation_names']=
                #continue
                #er_samples_data[sample]={}
                #er_samples_data[sample]["er_sample_name"]=sample
            for key in ["sample_orientation_flag","sample_azimuth","sample_dip","sample_bed_dip","sample_bed_dip_direction","sample_date","sample_declination_correction"]:
                if key in er_samples_orient_data[sample].keys():
                    er_samples_data[sample][key]=er_samples_orient_data[sample][key]
            if "magic_method_codes" in er_samples_orient_data[sample].keys():
                if "magic_method_codes" in er_samples_data[sample].keys():
                    codes=er_samples_data[sample]["magic_method_codes"].strip("\n").replace(" ","").replace("::",":").split(":")
                else:
                    codes=[]
                new_codes=er_samples_orient_data[sample]["magic_method_codes"].strip("\n").replace(" ","").replace("::",":").split(":")
                all_codes=codes+new_codes
                all_codes=list(set(all_codes)) # remove duplicates
                er_samples_data[sample]["magic_method_codes"]=":".join(all_codes)
        samples=er_samples_data.keys()
        samples.sort()
        er_recs=[]
        for sample in samples:
            er_recs.append(er_samples_data[sample])
            pmag.magic_write(self.WD+"/er_samples.txt",er_recs,"er_samples")
       
        dlg1 = wx.MessageDialog(None,caption="Message:", message="orientation data is saved/appended to er_samples.txt" ,style=wx.OK|wx.ICON_INFORMATION)
        dlg1.ShowModal()
        dlg1.Destroy()
        
        if len(new_samples_added)>0:
            dlg1 = wx.MessageDialog(None,caption="Warning:", message="The following samples were added to er_samples.txt:\n %s "%(" , ".join(new_samples_added)) ,style=wx.OK|wx.ICON_INFORMATION)
            dlg1.ShowModal()
            dlg1.Destroy()
            
        self.Destroy()    
                    
        
    def OnCloseWindow(self,event):   
        dlg1 = wx.MessageDialog(self,caption="Message:", message="Save changes to demag_orient.txt?\n " ,style=wx.OK|wx.CANCEL)
        result = dlg1.ShowModal()
        if result == wx.ID_OK:
            self.on_m_save_file(None)
            dlg1.Destroy()    
            self.Destroy()
        if result == wx.ID_CANCEL:
            dlg1.Destroy()    
            self.Destroy()

                     

                


class orient_convention(wx.Dialog):
    
    def __init__(self, *args, **kw):
        super(orient_convention, self).__init__(*args, **kw) 
            
        self.InitUI()
        #self.SetSize((250, 200))
        self.SetTitle("set orientation convention")
        
    def InitUI(self):


        pnl = wx.Panel(self)        
        vbox=wx.BoxSizer(wx.VERTICAL)

        #-----------------------
        # orientation convention
        #-----------------------

        sbs = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'orientation convention' ), wx.VERTICAL )

        sbs.AddSpacer(5)
        self.oc_rb1 = wx.RadioButton(pnl, -1,label='Pomeroy: Lab arrow azimuth = mag_azimuth; Lab arrow dip=-field_dip (field_dip is hade)',name='1', style=wx.RB_GROUP)
        sbs.Add(self.oc_rb1)             
        sbs.AddSpacer(5)
        self.oc_rb2 = wx.RadioButton(pnl, -1, label='Lab arrow azimuth = mag_azimuth-90 (mag_azimuth is strike); Lab arrow dip = -field_dip', name='2')
        sbs.Add(self.oc_rb2)             
        sbs.AddSpacer(5)
        self.oc_rb3 = wx.RadioButton(pnl, -1, label='Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip (field_dip is inclination of lab arrow)', name='3')        
        sbs.Add(self.oc_rb3)             
        sbs.AddSpacer(5)
        self.oc_rb4 = wx.RadioButton(pnl, -1, label='Lab arrow azimuth and dip are same as mag_azimuth, field_dip',  name='4')        
        sbs.Add(self.oc_rb4)             
        sbs.AddSpacer(5)
        self.oc_rb5 = wx.RadioButton(pnl, -1, label='ASC: Lab arrow azimuth and dip are mag_azimuth, field_dip-90 (field arrow is inclination of specimen Z direction)',name='5')        
        sbs.Add(self.oc_rb5)             
        sbs.AddSpacer(5)
        self.oc_rb6 = wx.RadioButton(pnl, -1, label='Lab arrow azimuth = mag_azimuth-90 (mag_azimuth is strike); Lab arrow dip = 90-field_dip', name='6')        
        sbs.Add(self.oc_rb6)             
        sbs.AddSpacer(5)        
        
         
        #-----------------------
        # declination correction
        #-----------------------                
        sbs2 = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'declination correction' ), wx.VERTICAL )
        hbox_dc1 = wx.BoxSizer(wx.HORIZONTAL)

        sbs2.AddSpacer(5)
        self.dc_rb1 = wx.RadioButton(pnl, -1, 'Use the IGRF DEC value at the lat/long and date supplied', (10, 50), style=wx.RB_GROUP)        
        self.dc_rb2 = wx.RadioButton(pnl, -1, 'Use this DEC:', (10, 50))        
        self.dc_tb2 = wx.TextCtrl(pnl,style=wx.CENTER)
        self.dc_rb3 = wx.RadioButton(pnl, -1, 'DEC=0, mag_az is already corrected in file', (10, 50))        
        
        sbs2.Add(self.dc_rb1)
        sbs2.AddSpacer(5)
        hbox_dc1.Add(self.dc_rb2)
        hbox_dc1.AddSpacer(5)
        hbox_dc1.Add(self.dc_tb2)
        sbs2.Add(hbox_dc1)
        
        sbs2.AddSpacer(5)
        sbs2.Add(self.dc_rb3)
        sbs2.AddSpacer(5)
        
        
        #-----------------------
        # orienation priority
        #-----------------------                
        sbs3 = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'orientation priority' ), wx.VERTICAL )

        sbs3.AddSpacer(5)
        self.op_rb1 = wx.RadioButton(pnl, -1, label='1) differential GPS 2) sun compass 3) magnetic compass',name='1', style=wx.RB_GROUP)
        sbs3.Add(self.op_rb1)             
        sbs3.AddSpacer(5)
        self.op_rb2 = wx.RadioButton(pnl, -1, label='1) differential GPS 2) magnetic compass 3) sun compass ', name='2')
        sbs3.Add(self.op_rb2)             
        sbs3.AddSpacer(5)


        #-----------------------
        #  add local time for GMT
        #-----------------------                

        sbs4 = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'add local time' ), wx.HORIZONTAL )
        #hbox_alt = wx.BoxSizer(wx.HORIZONTAL)
        
        sbs4.AddSpacer(5)
        self.dc_alt = wx.TextCtrl(pnl,style=wx.CENTER)
        #alt_txt = wx.StaticText(pnl,label="Hours to ADD local time for GMT, default is 0",style=wx.TE_CENTER)
        alt_txt = wx.StaticText(pnl,label="Hours to SUBTRACT from local time for GMT, default is 0",style=wx.TE_CENTER)        
        sbs4.Add(alt_txt)
        sbs4.AddSpacer(5)
        sbs4.Add(self.dc_alt)

        #-----------------------
        # OK button
        #-----------------------                
              
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(pnl, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.OnOK, self.okButton)
        hbox2.Add(self.okButton)
        
        #-----------------------
        # design the frame
        #-----------------------                
        
        vbox.AddSpacer(10)
        vbox.Add(sbs)
        vbox.AddSpacer(10)
        vbox.Add(sbs2)
        vbox.AddSpacer(10)
        vbox.Add(sbs3)
        vbox.AddSpacer(10)
        vbox.Add(sbs4)
        vbox.AddSpacer(10)
        vbox.Add(hbox2)
        vbox.AddSpacer(10)

        hbox1=wx.BoxSizer(wx.HORIZONTAL)        
        hbox1.AddSpacer(10)
        hbox1.Add(vbox)
        hbox1.AddSpacer(10)

        pnl.SetSizer(hbox1)
        hbox1.Fit(self)


        #-----------------------                
        # intialize defalut value
        #-----------------------                
        
        self.oc_rb4.SetValue(True)
        self.dc_rb1.SetValue(True)        
        self.op_rb1.SetValue(True)   
        
    def OnOK(self, e):
        self.ocn=""
        if self.oc_rb1.GetValue()==True:self.ocn="1"
        if self.oc_rb2.GetValue()==True:self.ocn="2"
        if self.oc_rb3.GetValue()==True:self.ocn="3"
        if self.oc_rb4.GetValue()==True:self.ocn="4"
        if self.oc_rb5.GetValue()==True:self.ocn="5"
        if self.oc_rb6.GetValue()==True:self.ocn="6"

        self.dcn=""
        if self.dc_rb1.GetValue()==True:self.dcn="1"
        if self.dc_rb2.GetValue()==True:
            self.dcn="2"
            try:
                float(self.dc_tb2.GetValue())
            except:
                dlg1 = wx.MessageDialog(None,caption="Error:", message="Add declination" ,style=wx.OK|wx.ICON_INFORMATION)
                dlg1.ShowModal()
                dlg1.Destroy()
                
        if self.dc_rb3.GetValue()==True:self.dcn="3"
        
        if self.op_rb1.GetValue()==True:self.op="1"
        if self.op_rb2.GetValue()==True:self.op="2"
        
        if self.dc_alt.GetValue()!="":
            try:
                float(self.dc_alt.GetValue())
                gmt_flags="-gmt " + self.dc_alt.GetValue()
            except:
                gmt_flags=""
        else:
            gmt_flags=""        
        #-------------
        self.ocn_flag="-ocn "+ self.ocn
        self.dcn_flag="-dcn "+ self.dcn
        self.gmt_flags=gmt_flags
        self.EndModal(wx.ID_OK)
        #self.Close()


class method_code_dialog(wx.Dialog):
    
    def __init__(self, *args, **kw):
        super(method_code_dialog, self).__init__(*args, **kw) 
            
        self.InitUI()
        self.SetTitle("additional required information")
        
    def InitUI(self):

        pnl = wx.Panel(self)        
        vbox=wx.BoxSizer(wx.VERTICAL)

        #-----------------------
        # MagIC codes
        #-----------------------
        
        sbs1 = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'MagIC codes' ), wx.VERTICAL )
        self.cb1 = wx.CheckBox(pnl, -1, 'FS-FD: field sampling done with a drill')
        self.cb2 = wx.CheckBox(pnl, -1, 'FS-H: field sampling done with hand sample')
        self.cb3 = wx.CheckBox(pnl, -1, 'FS-LOC-GPS: field location done with GPS')
        self.cb4 = wx.CheckBox(pnl, -1, 'FS-LOC-MAP:  field location done with map')
        self.cb5 = wx.CheckBox(pnl, -1, 'SO-POM:  a Pomeroy orientation device was used')
        self.cb6 = wx.CheckBox(pnl, -1, 'SO-ASC:  an ASC orientation device was used')
        self.cb7 = wx.CheckBox(pnl, -1, 'SO-MAG: magnetic compass used for all orientations')
        self.cb8 = wx.CheckBox(pnl, -1, 'SO-SUN: sun compass used for all orientations')
        self.cb9 = wx.CheckBox(pnl, -1, 'SO-SM: either magnetic or sun used on all orientations    ')
        self.cb10 = wx.CheckBox(pnl, -1, 'SO-SIGHT: orientation from sighting')

        sbs1.Add(self.cb1);sbs1.AddSpacer(5)
        sbs1.Add(self.cb2);sbs1.AddSpacer(5)
        sbs1.Add(self.cb3);sbs1.AddSpacer(5)
        sbs1.Add(self.cb4);sbs1.AddSpacer(5)
        sbs1.Add(self.cb5);sbs1.AddSpacer(5)
        sbs1.Add(self.cb6);sbs1.AddSpacer(5)
        sbs1.Add(self.cb7);sbs1.AddSpacer(5)
        sbs1.Add(self.cb8);sbs1.AddSpacer(5)
        sbs1.Add(self.cb9);sbs1.AddSpacer(5)
        sbs1.Add(self.cb10);sbs1.AddSpacer(5)

        #-----------------------
        # Bedding convention
        #-----------------------
        
        sbs2 = wx.StaticBoxSizer( wx.StaticBox( pnl, wx.ID_ANY, 'bedding convention' ), wx.VERTICAL )
        self.bed_con1 = wx.CheckBox(pnl, -1, 'Take fisher mean of bedding poles?')
        self.bed_con2 = wx.CheckBox(pnl, -1, "Don't correct bedding dip direction with declination - already correct")

        sbs2.Add(self.bed_con1);sbs1.AddSpacer(5)
        sbs2.Add(self.bed_con2);sbs1.AddSpacer(5)

        #-----------------------
        # OK button
        #-----------------------                
              
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button(pnl, wx.ID_OK, "&OK")
        self.Bind(wx.EVT_BUTTON, self.OnOK, self.okButton)
        hbox2.Add(self.okButton)

        #-----------------------
        # design the frame
        #-----------------------                
        vbox.Add(sbs1)
        vbox.AddSpacer(5)
        vbox.Add(sbs2)
        vbox.AddSpacer(5)
        vbox.Add(hbox2)
        vbox.AddSpacer(10)
        
        hbox1=wx.BoxSizer(wx.HORIZONTAL)        
        hbox1.AddSpacer(10)
        hbox1.Add(vbox)
        hbox1.AddSpacer(10)

        pnl.SetSizer(hbox1)
        hbox1.Fit(self)

    def OnOK(self, e):
        methodcodes=[]
        if self.cb1.GetValue() ==True:
            methodcodes.append('FS-FD')
        if self.cb2.GetValue() ==True:
            methodcodes.append('FS-H')
        if self.cb3.GetValue() ==True:
            methodcodes.append('FS-LOC-GPS')
        if self.cb4.GetValue() ==True:
            methodcodes.append('FS-LOC-MAP')
        if self.cb5.GetValue() ==True:
            methodcodes.append('SO-POM')
        if self.cb6.GetValue() ==True:
            methodcodes.append('SO-ASC')
        if self.cb7.GetValue() ==True:
            methodcodes.append('SO-MAG')
        if self.cb8.GetValue() ==True:
            methodcodes.append('SO-SUN')
        if self.cb9.GetValue() ==True:
            methodcodes.append('SO-SM')
        if self.cb10.GetValue() ==True:
            methodcodes.append('SO-SIGHT')
        
        if methodcodes==[]:
            self.methodcodes_flags=""
        else:
            self.methodcodes_flags="-mcd "+":".join(methodcodes)
        
        bedding_codes=[]
        
        if self.bed_con1.GetValue() ==True:
            bedding_codes.append("-a")
        if self.bed_con2.GetValue() ==True:
            bedding_codes.append("-BCN")
        
        self.bedding_codes_flags=" ".join(bedding_codes)   
        self.EndModal(wx.ID_OK) 
        #self.Close()


class check(wx.Frame):

    def __init__(self, parent, id, title, WD, ErMagic):
        wx.Frame.__init__(self, parent, -1, title)
        self.WD = WD
        self.ErMagic = ErMagic
        self.temp_data = {}
        self.InitSpecCheck()
        self.sample_window = 0 # sample window must be displayed (differently) twice, so it is useful to keep track



    def InitSpecCheck(self):
        """make an interactive grid in which users can edit specimen names
        as well as which sample a specimen belongs to"""

        # ADD A BUTTON to add an additional sample.  maybe will have a popup window to select what site/location etc. this sample belongs to 
        self.panel = wx.ScrolledWindow(self, style=wx.SIMPLE_BORDER)
        TEXT = """
        Step 1:
        Check that all specimens belong to the correct sample
        (if sample name is simply wrong, that will be fixed in step 2)
        note: if you need to do a comprehensive edit,
        consider opening your documents with Excel or Open Office"""
        label = wx.StaticText(self.panel,label=TEXT)
        self.Data, self.Data_hierarchy = self.ErMagic.Data, self.ErMagic.Data_hierarchy
        self.specimens = self.Data.keys()
        samples = self.Data_hierarchy['samples'].keys()
        # create the grid and also a record of the initial values for specimens/samples as a reference
        # to tell if we've had any changes
        self.spec_grid, self.temp_data['specimens'], self.temp_data['samples'] = self.make_table(['specimens', '', 'samples'], self.specimens, self.Data_hierarchy, 'sample_of_specimen')
        self.changes = False

        self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN, self.on_edit_grid, self.spec_grid) # if user begins to edit, self.changes will be set to True
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, lambda event: self.on_left_click(event, self.spec_grid, samples), self.spec_grid) 

        #### Create Buttons ####
        hbox_one = wx.BoxSizer(wx.HORIZONTAL)
        self.addSampleButton = wx.Button(self.panel, label="Add a new sample")
        self.Bind(wx.EVT_BUTTON, self.on_addSampleButton, self.addSampleButton)
        hbox_one.Add(self.addSampleButton)
        #
        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.saveButton =  wx.Button(self.panel, id=-1, label='Save')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_saveButton(event, self.spec_grid), self.saveButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.continueButton = wx.Button(self.panel, id=-1, label='Save and continue')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_continueButton(event, self.spec_grid, next_dia=self.InitSampCheck), self.continueButton)
        hboxok.Add(self.saveButton, flag=wx.ALIGN_LEFT|wx.RIGHT, border=20)
        hboxok.Add(self.cancelButton, flag=wx.ALIGN_LEFT|wx.RIGHT, border=20) 
        hboxok.Add(self.continueButton, flag=wx.ALIGN_LEFT )

        ### Create Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(label, flag=wx.ALIGN_LEFT|wx.BOTTOM, border=20)
        vbox.Add(self.spec_grid, flag=wx.BOTTOM|wx.EXPAND, border=20)
        vbox.Add(hbox_one, flag=wx.BOTTOM, border=20)
        vbox.Add(hboxok, flag=wx.BOTTOM, border=20)
        
        #for child in vbox.Children:
        #    print "child", type(child.GetWindow())

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)  
        self.Show()
        self.Centre()
            

    def InitSampCheck(self):
        """make an interactive grid in which users can edit sample names
        as well as which site a sample belongs to"""
        self.sample_window += 1 
        #print "init-ing Sample Check for the {}th time".format(self.sample_window)
        self.panel = wx.ScrolledWindow(self, style=wx.SIMPLE_BORDER)
        if self.sample_window == 1:
            TEXT = """
            Step 2:
            Check that all samples are correctly named,
            and that they belong to the correct site
            (if site name is simply wrong, that will be fixed in step 3)"""
        else:
            TEXT = """
            Step 4:
            Some of the data from the er_sites table has propogated into er_samples.
            Check that this data is correct, and fill in missing cells using controlled vocabularies.
            (see Help button for more details)"""
        label = wx.StaticText(self.panel,label=TEXT)
        self.Data, self.Data_hierarchy = self.ErMagic.Data, self.ErMagic.Data_hierarchy
        self.samples = self.Data_hierarchy['samples'].keys()
        sites = self.Data_hierarchy['sites'].keys()
        if self.sample_window == 1:
            self.samp_grid, self.temp_data['samples'], self.temp_data['sites'] = self.make_table(['samples', '', 'sites'], self.samples, self.Data_hierarchy, 'site_of_sample')
        if self.sample_window > 1:
            print "ADD DATA THIS TIME"
            col_labels = ['samples', '', 'sites', 'sample_class', 'sample_lithology', 'sample_type']
            self.samp_grid, self.temp_data['samples'], self.temp_data['sites'] = self.make_table(col_labels, self.samples, self.Data_hierarchy, 'site_of_sample')
            self.add_extra_grid_data(self.samp_grid, self.samples, col_labels, self.ErMagic.data_er_samples)

        self.changes = False

        self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN, self.on_edit_grid, self.samp_grid) 
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, lambda event: self.on_left_click(event, self.samp_grid, sites), self.samp_grid) 


        ### Create Buttons ###
        hbox_one = wx.BoxSizer(wx.HORIZONTAL)
        self.addSiteButton = wx.Button(self.panel, label="Add a new site")
        self.Bind(wx.EVT_BUTTON, self.on_addSiteButton, self.addSiteButton)
        hbox_one.Add(self.addSiteButton)
        if self.sample_window > 1:
            self.helpButton = wx.Button(self.panel, label="Help")
            self.Bind(wx.EVT_BUTTON, lambda event: self.on_helpButton(event, "/Users/nebula/Python/PmagPy/ErMagicSampleHelp.html"), self.helpButton)
            hbox_one.Add(self.helpButton)


        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.saveButton =  wx.Button(self.panel, id=-1, label='Save')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_saveButton(event, self.samp_grid), self.saveButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.continueButton = wx.Button(self.panel, id=-1, label='Save and continue')
        next_dia = self.InitSiteCheck if self.sample_window < 2 else self.InitLocCheck #None # 
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_continueButton(event, self.samp_grid, next_dia=next_dia), self.continueButton)

        hboxok.Add(self.saveButton, flag=wx.BOTTOM, border=20)
        hboxok.Add(self.cancelButton, flag=wx.BOTTOM, border=20 )
        hboxok.Add(self.continueButton, flag=wx.BOTTOM, border=20 )

        ### Make Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(label, flag=wx.ALIGN_LEFT|wx.BOTTOM, border=20)
        vbox.Add(self.samp_grid, flag=wx.BOTTOM|wx.EXPAND, border=20) # EXPAND ??
        vbox.Add(hbox_one, flag=wx.BOTTOM, border=20)
        vbox.Add(hboxok, flag=wx.BOTTOM, border=20)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()


    def InitSiteCheck(self):
        """make an interactive grid in which users can edit site names
        as well as which location a site belongs to"""
        self.panel = wx.ScrolledWindow(self, style=wx.SIMPLE_BORDER)
        TEXT = """
        Step 3:
        Check that all sites are correctly named,
        and that they belong to the correct location.
        Fill in the additional columns with controlled vocabularies (see Help button for details)"""
        label = wx.StaticText(self.panel,label=TEXT)
        self.Data, self.Data_hierarchy = self.ErMagic.Data, self.ErMagic.Data_hierarchy
        self.sites = self.Data_hierarchy['sites'].keys()
        # if you wanted to have all the headers show up as editable fields
        #args = self.ErMagic.data_er_sites[self.ErMagic.data_er_sites.keys()[0]].keys()
        #col_labels = ['sites', '', 'locations']
        #col_labels.extend(args)
        # end that thing
        col_labels = ['sites', '', 'locations', 'site_class', 'site_lithology', 'site_type', 'site_definition', 'site_lon', 'site_lat']
        self.site_grid, self.temp_data['sites'], self.temp_data['locations'] = self.make_table(col_labels, self.sites, self.Data_hierarchy, 'location_of_site')

        # get data_er_* dictionaries into the ErMagic object, if they didn't already exist
        if not self.ErMagic.data_er_sites:
            self.ErMagic.read_MagIC_info()

        self.add_extra_grid_data(self.site_grid, self.sites, col_labels, self.ErMagic.data_er_sites)

        locations = self.temp_data['locations']
        self.changes = False

        self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN, self.on_edit_grid, self.site_grid) 
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, lambda event: self.on_left_click(event, self.site_grid, locations), self.site_grid) 


        ### Create Buttons ###
        hbox_one = wx.BoxSizer(wx.HORIZONTAL)
        self.helpButton = wx.Button(self.panel, label="Help")
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_helpButton(event, "/Users/nebula/Python/PmagPy/ErMagicSiteHelp.html"), self.helpButton)
        hbox_one.Add(self.helpButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.saveButton =  wx.Button(self.panel, id=-1, label='Save')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_saveButton(event, self.site_grid), self.saveButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.continueButton = wx.Button(self.panel, id=-1, label='Save and continue')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_continueButton(event, self.site_grid, next_dia=self.InitSampCheck), self.continueButton)

        hboxok.Add(self.saveButton, flag=wx.BOTTOM, border=20)
        hboxok.Add(self.cancelButton, flag=wx.BOTTOM, border=20 )
        hboxok.Add(self.continueButton, flag=wx.BOTTOM, border=20 )

        ### Make Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(label, flag=wx.ALIGN_LEFT|wx.BOTTOM)#, flag=wx.ALIGN_LEFT|wx.BOTTOM, border=20)
        vbox.Add(self.site_grid, flag=wx.BOTTOM|wx.EXPAND, border=20) # EXPAND ??
        vbox.Add(hbox_one, flag=wx.BOTTOM, border=20)
        vbox.Add(hboxok, flag=wx.BOTTOM, border=20)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()


    def InitLocCheck(self):
        """make an interactive grid in which users can edit specimen names
        as well as which sample a specimen belongs to"""
        self.panel = wx.ScrolledWindow(self, style=wx.SIMPLE_BORDER)
        TEXT = """
        Step 5:
        Check that locations are correctly named.
        Fill in any blank cells using controlled vocabuliaries.
        (See Help button for details)"""
        label = wx.StaticText(self.panel,label=TEXT)
        self.Data, self.Data_hierarchy = self.ErMagic.Data, self.ErMagic.Data_hierarchy
        self.locations = self.Data_hierarchy['locations']
        #
        col_labels = ['locations', 'location_type']
        self.loc_grid = self.make_simple_table(col_labels, self.ErMagic.data_er_locations)
        self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN, self.on_edit_grid, self.loc_grid) 

        ### Create Buttons ###
        hbox_one = wx.BoxSizer(wx.HORIZONTAL)
        self.helpButton = wx.Button(self.panel, label="Help")
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_helpButton(event, "/Users/nebula/Python/PmagPy/ErMagicLocationHelp.html"), self.helpButton)
        hbox_one.Add(self.helpButton)

        hboxok = wx.BoxSizer(wx.HORIZONTAL)
        self.saveButton =  wx.Button(self.panel, id=-1, label='Save')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_saveButton(event, self.loc_grid), self.saveButton)
        self.cancelButton = wx.Button(self.panel, wx.ID_CANCEL, '&Cancel')
        self.Bind(wx.EVT_BUTTON, self.on_cancelButton, self.cancelButton)
        self.continueButton = wx.Button(self.panel, id=-1, label='Save and continue')
        self.Bind(wx.EVT_BUTTON, lambda event: self.on_continueButton(event, self.loc_grid, next_dia=None), self.continueButton)

        hboxok.Add(self.saveButton, flag=wx.BOTTOM, border=20)
        hboxok.Add(self.cancelButton, flag=wx.BOTTOM, border=20 )
        hboxok.Add(self.continueButton, flag=wx.BOTTOM, border=20 )

        ### Make Containers ###
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(label, flag=wx.ALIGN_LEFT|wx.BOTTOM)#, flag=wx.ALIGN_LEFT|wx.BOTTOM, border=20)
        vbox.Add(self.loc_grid, flag=wx.BOTTOM|wx.EXPAND, border=20) # EXPAND ??
        vbox.Add(hbox_one, flag=wx.BOTTOM, border=20)
        vbox.Add(hboxok, flag=wx.BOTTOM, border=20)

        hbox_all= wx.BoxSizer(wx.HORIZONTAL)
        hbox_all.AddSpacer(20)
        hbox_all.AddSpacer(vbox)
        hbox_all.AddSpacer(20)

        self.panel.SetSizer(hbox_all)
        self.panel.SetScrollbars(20, 20, 50, 50)
        hbox_all.Fit(self)
        self.Show()
        self.Centre()



    ### Grid methods ###
    def make_simple_table(self, column_labels, data_dict):
        grid = wx.grid.Grid(self.panel, -1, name=column_labels[0])
        grid.ClearGrid()
        row_labels = data_dict.keys()
        grid.CreateGrid(len(row_labels), len(column_labels))
        self.temp_data[column_labels[0]] = []
        # set row labels
        for n, row in enumerate(row_labels):
            grid.SetRowLabelValue(n, str(n+1))
            grid.SetCellValue(n, 0, row)
            self.temp_data[column_labels[0]].append(row)
        # set column labels
        for n, col in enumerate(column_labels):
            grid.SetColLabelValue(n, col)
        # set values in each cell (other than 1st column)
        for num, row in enumerate(row_labels):
            for n, col in enumerate(column_labels[1:]):
                value = data_dict[row][col]
                if value:
                    grid.SetCellValue(num, n+1, value)
                #else:
                #    grid.SetCellValue(num, n+1, 'hi {}'.format((num, n+1)))

        return grid
        

    def make_table(self, column_labels, row_values, column_indexing, ind, *args):
        """ takes a list of row values (i.e., specimens, samples, locations, etc.) 
        and a data structure (column_indexing) to index them against.  for example, 
        to show the sample to specimen relationship, you would have:
        column_labels: ["specimen", " ", "samples""]
        row_values: list of specimens
        column_indexing: Data_hierarchy object containing various data mappings
        ind: ['sample_of_specimen'], indicating which data mapping to use """
        grid = wx.grid.Grid(self.panel, -1, name=column_labels[0])
        grid.ClearGrid()
        grid.CreateGrid(len(row_values), len(column_labels))

        list_values = []
        original_1 = [] # specs (in first dia)
        original_2 = [] # samps (in first dia)

        col1_editable = True
        if column_labels[0] == 'specimens':
            col1_editable = False

        # comment this so it is understandable to you
        for n, row in enumerate(row_values):
            grid.SetRowLabelValue(n, str(n+1))
            original_1.append(row)
            grid.SetCellValue(n, 0, row)
            if not col1_editable:
                grid.SetReadOnly(n, 0, True)
            grid.SetCellValue(n, 1, "belongs to")
            grid.SetReadOnly(n, 1, True) 
            col = column_indexing[ind][row]
            original_2.append(col)
            grid.SetCellValue(n, 2, col)

        #grid.AppendRows(1) # prevents site_grid from looking really stupid when editing bottom row.  not a good permanent solution, thoug
        #grid.SetRowLabelValue(len(row_values), " ")
        
        for n, label in enumerate(column_labels):
            grid.SetColLabelValue(n, label)

        grid.AutoSize()

        for n, col in enumerate(column_labels):
            # adjust column widths to be a little larger then auto for nicer editing
            if n != 1:
            #if True:
                size = grid.GetColSize(n) * 1.75
                grid.SetColSize(n, size)

        return grid, original_1, original_2
    
    def add_extra_grid_data(self, grid, row_labels, col_labels, data_dict):
        print "running add_extra_grid_data"
        #print "grid", grid
        #print "data_dict", data_dict
        for num, row in enumerate(row_labels):
            for n, col in enumerate(col_labels[3:]):
                if data_dict[row][col]:
                    grid.SetCellValue(num, n+3, data_dict[row][col])
            
        
    def on_edit_grid(self, event):
        """sets self.changes to true when user edits the grid"""
        self.changes = True

    def on_left_click(self, event, grid, choices):
        """creates popup menu when user clicks on the third column
        allows user to edit third column, but only from available values"""
        row, col = event.GetRow(), event.GetCol()
        if col == 2:
            menu = wx.Menu()
            for choice in set(choices):
                if not choice: choice = " " # prevents error if choice is an empty string
                menuitem = menu.Append(wx.ID_ANY, choice)
                self.Bind(wx.EVT_MENU, lambda event: self.on_select_menuitem(event, grid, row), menuitem)
            self.PopupMenu(menu)
            menu.Destroy()

    def on_select_menuitem(self, event, grid, row):
        """sets value of selected cell to value selected from menu
        (doesn't require column info because only third column works this way"""
        self.changes = True # if user selects a menuitem, that is an edit
        item_id =  event.GetId()
        item = event.EventObject.FindItemById(item_id)
        label= item.Label
        grid.SetCellValue(row, 2, label)


    ### Button methods ###

    def on_addSampleButton(self, event):
        print "add sample"

    def on_addSiteButton(self, event):
        print "add site"

    def on_helpButton(self, event, page=None):
        """shows html help page"""
        html_frame = pw.HtmlFrame(self, page=page)
        html_frame.Show()


    def on_continueButton(self, event, grid, next_dia=None):
        """pulls up next dialog, if there is one.
        gets any updated information from the current grid and runs ErMagicBuilder"""
        grid.SaveEditControlValue() # locks in value in cell currently edited
        simple_grids = {"locations": self.ErMagic.data_er_locations}
        grid_name = grid.GetName()

        if self.changes:
            if grid_name in simple_grids:
                self.update_simple_grid_data(grid, simple_grids[grid_name])
            else:
                self.update_orient_data(grid)
            self.ErMagic.on_okButton(None)
            self.changes = False # resets
        self.panel.Destroy()
        if next_dia:
            next_dia()
        else:
            self.Destroy()

    def on_saveButton(self, event, grid):
        """saves any editing of the grid but does not continue to the next window"""
        print "SAVE!"
        grid.SaveEditControlValue() # locks in value in cell currently edited
        simple_grids = {"locations": self.ErMagic.data_er_locations}
        grid_name = grid.GetName()

        if self.changes:
            print "there were changes, so we are updating the data"
            if grid_name in simple_grids:
                self.update_simple_grid_data(grid, simple_grids[grid_name])
            else:
                self.update_orient_data(grid)

            self.ErMagic.on_okButton(None) # add this back in, it was messing up testing
            self.changes = False



    def on_cancelButton(self, event):
        self.Destroy()

        
    ### Manage data methods ###

    def update_simple_grid_data(self, grid, data=None):
        # method that 
        print "doing update_simple_grid_data"
        print "data before", data
        grid_name = grid.GetName()
        #if grid_name == "locations":
        #    self.update_locations()
        rows = range(grid.GetNumberRows())
        cols = range(grid.GetNumberCols())
        updated_items = []
        for row in rows:
            item = grid.GetCellValue(row, 0)
            updated_items.append(str(item))
        if grid_name == "locations":
            self.update_locations(updated_items)
        for row in rows: 
            item = grid.GetCellValue(row, 0)
            #updated_items.append(str(item))
            for col in cols[1:]:
                category = grid.GetColLabelValue(col)
                value = str(grid.GetCellValue(row, col))
                data[item][category] = value
        #print "data after", data
        #print "temp_data", self.temp_data['locations']
        #print "updated_items", updated_items
        #for k, v in self.Data_hierarchy.items():
        #    if 'location' in k:
        #        print k
        #        print v


    def update_orient_data(self, grid):
        """ """
        col1_updated, col2_updated, col1_old, col2_old, type1, type2 = self.get_old_and_new_data(grid, 0, 2)
        if len(set(col1_updated)) != len(col1_updated):
            print "Duplicate {} detected.  Please ensure that all {} names are unique".format(type1, type1[:-1])
            return 0
        if type1 == 'specimens':
            self.update_specimens(col1_updated, col1_old, col2_updated, col2_old, type1, type2)
        if type1 == 'samples':
            cols = range(3, grid.GetNumberCols())
            col_labels = []
            for col in cols:
                col_labels.append(grid.GetColLabelValue(col))
            self.update_samples(grid, col1_updated, col1_old, col2_updated, col2_old, *col_labels)
        if type1 == 'sites':
            cols = range(3, grid.GetNumberCols())
            col_labels = []
            for col in cols:
                col_labels.append(grid.GetColLabelValue(col))
            self.update_sites(grid, col1_updated, col1_old, col2_updated, col2_old, *col_labels)

        # updates the holder data so that when we save again, we will only update what is new as of the last save
        self.temp_data[type1] = col1_updated 
        self.temp_data[type2] = col2_updated


    def update_locations(self, updated_locations):
        print "calling update_locations"
        print self.ErMagic.data_er_specimens
        print self.ErMagic.data_er_samples
        print self.ErMagic.data_er_sites
        original_locations = self.temp_data['locations']
        changed = [(original_locations[num], new_loc) for (num, new_loc) in enumerate(updated_locations) if new_loc != original_locations[num]]
        for change in changed:
            print "change", change
            old_loc, new_loc = change
            sites = self.Data_hierarchy['locations'].pop(old_loc)
            self.Data_hierarchy['locations'][new_loc] = sites
            #
            data = self.ErMagic.data_er_locations.pop(old_loc)
            self.ErMagic.data_er_locations[new_loc] = data
            self.ErMagic.data_er_locations[new_loc]['er_location_name'] = new_loc
            #
            for site in sites:
                self.Data_hierarchy['location_of_site'][site] = new_loc
                self.ErMagic.data_er_sites[site]['er_location_name'] = new_loc
                samples = self.Data_hierarchy['sites'][site]
                for sample in samples:
                    self.Data_hierarchy['location_of_sample'][sample] = new_loc
                    self.ErMagic.data_er_samples[sample]['er_location_name'] = new_loc
                    specimens = self.Data_hierarchy['samples'][sample]
                    for spec in specimens:
                        self.Data_hierarchy['location_of_specimen'][spec] = new_loc
                        self.ErMagic.data_er_specimens[spec]['er_location_name'] = new_loc

            #
            #location_of_specimen ( {'sc12b1': 'Xanadu', 'ag1-6b': 'HERE', 'ag1-6a': 'HERE'} )
            #location_of_sample
            #location_of_site
            #locations ( {'Xanadu': ['sc12'], 'HERE': ['ag1-']} )
            
        



    def update_sites(self, grid, col1_updated, col1_old, col2_updated, col2_old, *args):
        print "updating sites"
        changed = [(old_value, col1_updated[num]) for (num, old_value) in enumerate(col1_old) if old_value != col1_updated[num]]
        for change in changed:
            old_site, new_site = change
            samples = self.Data_hierarchy['sites'].pop(old_site)
            location = self.Data_hierarchy['location_of_site'].pop(old_site)
            if location == " ": # prevents error
                location = ""
            self.Data_hierarchy['sites'][new_site] = samples
            ind = self.Data_hierarchy['locations'][location].index(old_site)
            self.Data_hierarchy['locations'][location][ind] = new_site
            self.Data_hierarchy['location_of_site'][new_site] = location
            for samp in samples:
                specimens = self.Data_hierarchy['samples'][samp]
                self.Data_hierarchy['site_of_sample'][samp] = new_site
                self.ErMagic.data_er_samples[samp]['er_site_name'] = new_site
                for spec in specimens:
                    self.Data_hierarchy['site_of_specimen'][spec] = new_site
                    self.ErMagic.data_er_specimens[spec]['er_site_name'] = new_site
            data = self.ErMagic.data_er_sites.pop(old_site)
            self.ErMagic.data_er_sites[new_site] = data
            self.ErMagic.data_er_sites[new_site]['er_site_name'] = new_site

        # now do the "which site belongs to which location" part
        for num, value in enumerate(col2_updated):
            # find where changes have occurred
            if value != col2_old[num]:
                print "CHANGE!", "new", value, "old", col2_old[num]
                print "len(value)", len(value)
                old_loc = col2_old[num]
                new_loc = col2_updated[num]
                if old_loc == " ": 
                    old_loc = ""
                if new_loc == " ":
                    new_loc = ""
                site = col1_updated[num]
                #
                self.Data_hierarchy['location_of_site'][site] = new_loc
                #
                self.Data_hierarchy['locations'][old_loc].remove(site)
                self.Data_hierarchy['locations'][new_loc].append(site)
                #
                for samp in self.Data_hierarchy['sites'][site]:
                    self.Data_hierarchy['location_of_sample'][samp] = new_loc
                    self.ErMagic.data_er_samples[samp]['er_location_name'] = new_loc
                    for spec in self.Data_hierarchy['samples'][samp]:
                        self.Data_hierarchy['location_of_specimen'][spec] = new_loc
                        self.ErMagic.data_er_specimens[spec]['er_location_name'] = new_loc
                #
                self.ErMagic.data_er_sites[site]['er_location_name'] = new_loc
                #
        
        # now fill in all the other columns
        for num_site, site in enumerate(col1_updated):
            for num, arg in enumerate(args):
                num += 3
                value = str(grid.GetCellValue(num_site, num))
                self.ErMagic.data_er_sites[site][arg] = value

        print "self.ErMagic.data_er_sites", self.ErMagic.data_er_sites




    def update_samples(self, grid, col1_updated, col1_old, col2_updated, col2_old, *args):
        changed = [(old_value, col1_updated[num]) for (num, old_value) in enumerate(col1_old) if old_value != col1_updated[num]]  
        for change in changed:
            #print "change!!!!!!", change
            old_sample, new_sample = change
            specimens = self.Data_hierarchy['samples'].pop(old_sample)
            site = self.Data_hierarchy['site_of_sample'].pop(old_sample)
            location = self.Data_hierarchy['location_of_sample'].pop(old_sample)
            
            self.Data_hierarchy['samples'][new_sample] = specimens
            
            for spec in specimens:
                self.Data_hierarchy['sample_of_specimen'][spec] = new_sample
                self.Data_hierarchy['specimens'][spec] = new_sample
            #
            self.Data_hierarchy['site_of_sample'][new_sample] = site
            #
            self.Data_hierarchy['location_of_sample'][new_sample] = location
            #
            ind = self.Data_hierarchy['sites'][site].index(old_sample)
            self.Data_hierarchy['sites'][site][ind] = new_sample
            # updating self.ErMagic.data_er_samples
            #print "in update_samples, self.ErMagic.data_er_specimens", self.ErMagic.data_er_specimens
            #print "in update_samples, self.ErMagic.data_er_samples.keys()", self.ErMagic.data_er_samples
            #print "-"
            sample_data = self.ErMagic.data_er_samples.pop(old_sample)
            self.ErMagic.data_er_samples[new_sample] = sample_data
            self.ErMagic.data_er_samples[new_sample]['er_sample_name'] = new_sample
            for spec in self.ErMagic.data_er_specimens:
                if self.ErMagic.data_er_specimens[spec]['er_sample_name'] == old_sample:
                    self.ErMagic.data_er_specimens[spec]['er_sample_name'] = new_sample
        
        # now do the site changes
        for num, value in enumerate(col2_updated):
            # find where changes have occurred
            if value != col2_old[num]:
                #print "CHANGE!", "new", value, "old", col2_old[num]
                sample = col1_updated[num]
                specimens = self.Data_hierarchy['samples'][sample]
                old_site = col2_old[num]
                new_site = value
                loc = self.Data_hierarchy['location_of_site'][new_site]
                samples = self.Data_hierarchy['sites'][old_site]
                #
                self.Data_hierarchy['site_of_sample'][sample] = new_site
                #
                self.Data_hierarchy['location_of_sample'][sample] = loc
                #
                self.Data_hierarchy['sites'][new_site].append(sample)
                self.Data_hierarchy['sites'][old_site].remove(sample)
                for spec in specimens:
                    # specimens belonging to a sample which has been reassigned to a different site correspondingly must change site and location
                    self.Data_hierarchy['site_of_specimen'][spec] = new_site
                    self.Data_hierarchy['location_of_specimen'][spec] = loc
                # insert here: updating ErMagic.data_er_samples or whatever based on site change
                self.ErMagic.data_er_samples[sample]['er_site_name'] = new_site
                self.ErMagic.data_er_samples[sample]['er_location_name'] = loc

        # now fill in all the other columns
        for num_sample, sample in enumerate(col1_updated):
            for num, arg in enumerate(args):
                num += 3
                value = str(grid.GetCellValue(num_sample, num))
                self.ErMagic.data_er_samples[sample][arg] = value
                print "sample: {}, arg: {}, value {}".format(sample, arg, value)

      

    def update_specimens(self, col1_updated, col1_old, col2_updated, col2_old, type1, type2):

        print "UPDATE SAMPLES"
        #  ALSO should check for whether or not a sample still "exists"  
        # maybe
        for num, value in enumerate(col2_updated):
            # find where changes have occurred
            if value != col2_old[num]:
                old_samp = col2_old[num]
                samp = value
                spec = col1_updated[num]
                # find the site and location of the sample and apply it to the specimen (which now belongs to that sample
                site = self.Data_hierarchy['site_of_sample'][samp] 
                location = self.Data_hierarchy['location_of_sample'][samp] 
                self.Data_hierarchy['specimens'][spec] = samp
                self.Data_hierarchy['sample_of_specimen'][spec] = samp
                self.Data_hierarchy['site_of_specimen'][spec] = site
                self.Data_hierarchy['location_of_specimen'][spec] = location
                #
                self.Data_hierarchy['samples'][samp].append(spec)
                self.Data_hierarchy['samples'][old_samp].remove(spec)
                # do the ErMagic.data_er_samples part
                #????
                self.ErMagic.data_er_specimens[spec]['er_sample_name'] = samp
                self.ErMagic.data_er_specimens[spec]['er_site_name'] = site
                self.ErMagic.data_er_specimens[spec]['er_locations_name'] = location




        #keys = ['sample_of_specimen', 'site_of_sample', 'location_of_specimen', 'locations', 'sites', 'site_of_specimen', 'samples', 'location_of_sample', 'location_of_site', 'specimens']


    def get_old_and_new_data(self, grid, col1_num, col2_num):
        cols = grid.GetNumberCols()
        rows = grid.GetNumberRows()
        type1 = grid.GetColLabelValue(col1_num)
        type2 = grid.GetColLabelValue(col2_num)
        old_1 = self.temp_data[type1]
        old_2 = self.temp_data[type2]
        update_1 = []
        update_2 = []
        for r in range(rows):
            # gets edited values from grid
            one = grid.GetCellValue(r, 0)
            update_1.append(str(one))
            two = grid.GetCellValue(r, 2)
            update_2.append(str(two))
        return update_1, update_2, old_1, old_2, type1, type2


    """
    def get_orient_data(self):
        try:
            self.Data, self.Data_hierarchy = self.Parent.Data
        except:
            self.Data, self.Data_hierarchy = self.Parent.get_data()
        self.samples_list=self.Data_hierarchy['samples']         
        self.orient_data={}
        try:
            self.orient_data=self.read_magic_file(self.WD+"/demag_orient.txt",1,"sample_name")  
        except:
            pass
        for sample in self.samples_list:
            if sample not in self.orient_data.keys():
               self.orient_data[sample]={} 
               self.orient_data[sample]["sample_name"]=sample
               
            if sample in self.Data_hierarchy['site_of_sample'].keys():
                self.orient_data[sample]["site_name"]=self.Data_hierarchy['site_of_sample'][sample]
            else:
                self.orient_data[sample]["site_name"]=""

        #print "self.orient_data", self.orient_data


    def update_orient_data(self):
        # check each value in the specimen column for changes
        # check each value in the samples column for changes
        for row in range(self.grid.GetNumberRows()):
            pass
            #print self.grid.GetCellValue(row, 0)
            #print self.specimens[row]

    def get_data(self):
      # get_data from ErMagicBuilder.  Returns a more comprehensive Data hierarchy than the get_data in QuickMagic.  oy.
      Data={}
      Data_hierarchy={}
      Data_hierarchy['locations']={}
      Data_hierarchy['sites']={}
      Data_hierarchy['samples']={}
      Data_hierarchy['specimens']={}
      Data_hierarchy['sample_of_specimen']={} 
      Data_hierarchy['site_of_specimen']={}   
      Data_hierarchy['site_of_sample']={}   
      Data_hierarchy['location_of_specimen']={}   
      Data_hierarchy['location_of_sample']={}   
      Data_hierarchy['location_of_site']={}   
      try:
          meas_data,file_type=pmag.magic_read(self.WD+"/magic_measurements.txt")
      except:
          print "-E- ERROR: Cant read magic_measurement.txt file. File is corrupted."
          return {},{}
         
      sids=pmag.get_specs(meas_data) # samples ID's
      
      for s in sids:
          if s not in Data.keys():
              Data[s]={}
      for rec in meas_data:
          s=rec["er_specimen_name"]
          sample=rec["er_sample_name"]
          site=rec["er_site_name"]
          location=rec["er_location_name"]
          if sample not in Data_hierarchy['samples'].keys():
              Data_hierarchy['samples'][sample]=[]

          if site not in Data_hierarchy['sites'].keys():
              Data_hierarchy['sites'][site]=[]         

          if location not in Data_hierarchy['locations'].keys():
              Data_hierarchy['locations'][location]=[]         
          
          if s not in Data_hierarchy['samples'][sample]:
              Data_hierarchy['samples'][sample].append(s)

          if sample not in Data_hierarchy['sites'][site]:
              Data_hierarchy['sites'][site].append(sample)

          if site not in Data_hierarchy['locations'][location]:
              Data_hierarchy['locations'][location].append(site)

          Data_hierarchy['specimens'][s]=sample
          Data_hierarchy['sample_of_specimen'][s]=sample  
          Data_hierarchy['site_of_specimen'][s]=site  
          Data_hierarchy['site_of_sample'][sample]=site
          Data_hierarchy['location_of_specimen'][s]=location 
          Data_hierarchy['location_of_sample'][sample]=location 
          Data_hierarchy['location_of_site'][site]=location 
          
      return(Data,Data_hierarchy)
"""


"""
        # code that would update specimens in update_specimens
        changed = [(i, col1_updated[num]) for (num, i) in enumerate(col1_old) if i != col1_updated[num]]  
        
        
        for change in changed:
            #print "change", change
            old_spec, new_spec = change
            sample = self.Data_hierarchy[type1].pop(old_spec)
            #
            self.Data_hierarchy[type1][new_spec] = sample
            #
            sample = self.Data_hierarchy['sample_of_specimen'].pop(old_spec)
            self.Data_hierarchy['sample_of_specimen'][new_spec] = sample
            #
            site = self.Data_hierarchy['site_of_specimen'].pop(old_spec)
            self.Data_hierarchy['site_of_specimen'][new_spec] = site
            #
            loc = self.Data_hierarchy['location_of_specimen'].pop(old_spec)
            self.Data_hierarchy['location_of_specimen'][new_spec] = loc
            #
            #print "self.Data_hierarchy['samples']", self.Data_hierarchy['samples']
            #print "self.Data_hierarchy['samples'][sample]", self.Data_hierarchy['samples'][sample]
            ind = self.Data_hierarchy['samples'][sample].index(old_spec)
            #print "ind:", ind
            #self.Data_hierarchy['samples'][sample].pop(ind)
            self.Data_hierarchy['samples'][sample][ind] = new_spec
            # doing data_er_specimens thing
            print "self.ErMagic.data_er_specimens.keys()", self.ErMagic.data_er_specimens.keys()
            spec_data = self.ErMagic.data_er_specimens.pop(old_spec)
            self.ErMagic.data_er_specimens[new_spec] = spec_data
            self.ErMagic.data_er_specimens[new_spec]['er_specimen_name'] = new_spec
            #self.ErMagic.data_er_specimens[new_spec]['er_sample_name'] = sample
            #self.ErMagic.data_er_specimens[new_spec]['er_site_name'] = site
            #self.ErMagic.data_er_specimens[new_spec]['er_locations_name'] = loc

            # there are some other things in the dictionary that might need to be updated, but I'm not sure
            # done data_er_specimens thing


        # update self.ErMagic.data_er_specimens as below:
        #'mgf10a1': {'er_citation_names': 'This study', 'er_location_name': '', 'er_site_name': 'm', 'er_sample_name': 'm', 'specimen_class': '', 'er_specimen_name': 'mgf10a1', 'specimen_lithology': '', 'er_citation_name': '', 'specimen_type': ''}
        # also update data_er_samples and so on all the way up as needed
        #self.ErMagic.data_er_samples[new_sample] {'sample_bed_dip_direction': '', 'er_citation_names': 'This study', 'sample_lithology': '', 'sample_azimuth': '', 'er_site_name': 'm', 'er_sample_name': 'MARTHS', 'specimen_weight': '', 'sample_type': '', 'sample_bed_dip': '', 'er_location_name': '', 'sample_height': '', 'sample_declination_correction': '', 'sample_lat': '', 'magic_method_codes': '', 'specimen_volume': '', 'er_citation_name': '', 'sample_dip': '', 'sample_lon': '', 'sample_class': ''}
"""
