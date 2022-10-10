import maya.cmds as cmds
import nmrig.simpleLimbClass as nmLimb
reload(nmLimb)


class LimbUI():
    def __init__(self):
        if cmds.window('LimbCreatorUI', exists=True):
            cmds.deleteUI('LimbCreatorUI')

        # create our window
        self.window = cmds.window('LimbCreatorUI', title='Limb Creator',
                                  width=503, height=543)

        # create main layout
        self.main_layout = cmds.columnLayout(width=503, height=543)

        # add frame layouts
        self.build_data_frame()
        self.build_arguments_frame()
        self.color_settings_frame()
        self.button_grid()

        # show window
        cmds.showWindow(self.window)

    def build_data_frame(self):
        data_frame = cmds.frameLayout(label='Build Data', width=500, height=230,
                                      collapsable=True, parent=self.main_layout,
                                      collapseCommand=lambda: self.collapse_cmd(
                                          data_frame, 230),
                                      expandCommand=lambda: self.expand_cmd(
                                          data_frame, 230))

        rcl = cmds.rowColumnLayout(numberOfColumns=3,
                                   columnWidth=[(1, 200), (2, 200), (3, 100)],
                                   columnOffset=[(1, 'both', 5), (2, 'both', 0),
                                                 (3, 'both', 5)],
                                   parent=data_frame)
        # text labels
        cmds.text(label='Alias', align='left', fn='boldLabelFont',
                  height=30, parent=rcl)
        cmds.text(label='Guide', align='left', fn='boldLabelFont',
                  height=30, parent=rcl)
        cmds.text(label='Load', align='left', fn='boldLabelFont',
                  height=30, parent=rcl)

        limb01_alias = cmds.textField(height=30, text='shoulder', parent=rcl)
        limb01_guide = cmds.textField(height=30, parent=rcl)
        limb01_load = cmds.button(label='load selected', height=30, parent=rcl,
                                  command=lambda x: self.load_sel(limb01_guide))

        limb02_alias = cmds.textField(height=30, text='elbow', parent=rcl)
        limb02_guide = cmds.textField(height=30, parent=rcl)
        limb02_load = cmds.button(label='load selected', height=30, parent=rcl,
                                  command=lambda x: self.load_sel(limb02_guide))

        limb03_alias = cmds.textField(height=30, text='wrist', parent=rcl)
        limb03_guide = cmds.textField(height=30, parent=rcl)
        limb03_load = cmds.button(label='load selected', height=30, parent=rcl,
                                  command=lambda x: self.load_sel(limb03_guide))

        pv_alias = cmds.textField(height=30, text='pole vector', enable=False,
                                  parent=rcl)
        self.pv_guide = cmds.textField(height=30, parent=rcl)
        pv_load = cmds.button(label='load selected', height=30, parent=rcl,
                              command=lambda x: self.load_sel(self.pv_guide))

        # text labels
        cmds.text(label='Side', align='left', fn='obliqueLabelFont',
                  height=20, parent=rcl)
        cmds.text(label='Part', align='left', fn='obliqueLabelFont',
                  height=20, parent=rcl)
        cmds.text(label='Base Name', align='left', fn='obliqueLabelFont',
                  height=20, parent=rcl)

        self.side_txt = cmds.textField(height=30, text='L', parent=rcl)
        self.part_txt = cmds.textField(height=30, text='arm', parent=rcl)
        self.base_txt = cmds.textField(height=30, text='L_arm', enable=False,
                                       parent=rcl)
        cmds.textField(self.side_txt, edit=True, changeCommand = lambda x:
                       self.change_base_name())
        cmds.textField(self.part_txt, edit=True, changeCommand=lambda x:
                       self.change_base_name())
        self.joint_list = [limb01_guide, limb02_guide, limb03_guide]
        self.alias_list = [limb01_alias, limb02_alias, limb03_alias]

    def build_arguments_frame(self):
        arg_frame = cmds.frameLayout(label='Build Arguments', width=500, height=180,
                                     collapsable=True, parent=self.main_layout,
                                     collapseCommand=lambda: self.collapse_cmd(
                                         arg_frame, 180),
                                     expandCommand=lambda: self.expand_cmd(
                                         arg_frame, 180))

        baf_col = cmds.rowColumnLayout(numberOfColumns=1,
                                       columnWidth=[(1, 500)],
                                       columnOffset=[(1, 'both', 0)],
                                       parent=arg_frame)

        prcl = cmds.rowColumnLayout(numberOfColumns=4, height=60,
                                    columnWidth=[(1, 150), (2, 110),
                                                 (3, 110), (4, 110)],
                                    columnOffset=[(1, 'both', 5),
                                                  (2, 'both', 5),
                                                  (3, 'both', 5),
                                                  (4, 'both', 5)],
                                    parent=baf_col)

        cmds.text(label='Primary Axis:', align='left', fn='boldLabelFont',
                  height=30, parent=prcl)
        self.pa_col = cmds.radioCollection(numberOfCollectionItems=6,
                                           parent=prcl)
        px = cmds.radioButton(label='X', parent=prcl)
        py = cmds.radioButton(label='Y', parent=prcl)
        pz = cmds.radioButton(label='Z', parent=prcl)
        cmds.separator(style='none', parent=prcl)
        pnx = cmds.radioButton(label='-X', parent=prcl)
        pny = cmds.radioButton(label='-Y', parent=prcl)
        pnz = cmds.radioButton(label='-Z', parent=prcl)
        cmds.radioCollection(self.pa_col, edit=True, select=px)
        cmds.separator(style='in', p=baf_col)

        urcl = cmds.rowColumnLayout(numberOfColumns=4, height=60,
                                    columnWidth=[(1, 150), (2, 110),
                                                 (3, 110), (4, 110)],
                                    columnOffset=[(1, 'both', 5),
                                                  (2, 'both', 5),
                                                  (3, 'both', 5),
                                                  (4, 'both', 5)],
                                    parent=baf_col)

        cmds.text(label='Up Axis:', align='left', fn='boldLabelFont',
                  height=30, parent=urcl)
        self.ua_col = cmds.radioCollection()
        ux = cmds.radioButton(label='X', parent=urcl)
        uy = cmds.radioButton(label='Y', parent=urcl)
        uz = cmds.radioButton(label='Z', parent=urcl)
        cmds.separator(style='none', parent=urcl)
        unx = cmds.radioButton(label='-X', parent=urcl)
        uny = cmds.radioButton(label='-Y', parent=urcl)
        unz = cmds.radioButton(label='-Z', parent=urcl)
        cmds.radioCollection(self.ua_col, edit=True, select=uy)
        cmds.separator(style='in', p=baf_col)

        cb_grid = cmds.gridLayout(numberOfColumns=2,
                                  cellWidthHeight=(250, 30),
                                  parent=baf_col)
        self.stretch_cb = cmds.checkBox(label=' -  Is Stretchy', value=True,
                                        parent=cb_grid)
        self.remove_cb = cmds.checkBox(label=' -  Remove Guides', value=True,
                                       parent=cb_grid)

    def color_settings_frame(self):
        color_frame = cmds.frameLayout(label='Color Settings',
                                       width=500, height=90,
                                       collapsable=True,
                                       parent=self.main_layout,
                                       collapseCommand=lambda: self.collapse_cmd(
                                           color_frame, 90),
                                       expandCommand=lambda: self.expand_cmd(
                                           color_frame, 90))
        rcl = cmds.rowColumnLayout(numberOfColumns=2, height=60,
                                   columnWidth=[(1, 250), (2, 250)],
                                   columnOffset=[(1, 'both', 5),
                                                 (2, 'both', 5)],
                                   parent=color_frame)

        self.pr_color = cmds.colorSliderGrp(label='Primary: ', adj=3,
                                            height=30, columnWidth3=[60,40,150],
                                            columnAlign3=['right',
                                                          'left', 'left'],
                                            rgb=(1, 1, 0), parent=rcl)
        self.fk_color = cmds.colorSliderGrp(label='FK: ', adj=3, height=30,
                                            columnWidth3=[60,40,150],
                                            columnAlign3=['right',
                                                          'left', 'left'],
                                            rgb=(0, 0, 1), parent=rcl)
        self.sc_color = cmds.colorSliderGrp(label='Secondary: ',
                                            adj=3, height=30,
                                            columnWidth3=[60,40,150],
                                            columnAlign3=['right',
                                                          'left', 'left'],
                                            rgb=(0, .2, 1), parent=rcl)
        self.pv_color = cmds.colorSliderGrp(label='PV: ', adj=3, height=30,
                                            columnWidth3=[60,40,150],
                                            columnAlign3=['right',
                                                          'left', 'left'],
                                            rgb=(0, 1, 1), parent=rcl)

    def button_grid(self):
        btn_col = cmds.rowColumnLayout(numberOfColumns=1,
                                       columnWidth=[(1, 500)],
                                       columnOffset=[(1, 'both', 0)],
                                       parent=self.main_layout)
        grid_layout = cmds.gridLayout(numberOfColumns=2,
                                      cellWidthHeight=(250, 40), parent=btn_col)
        build_btn = cmds.button(label='Build Limb', height=40,
                                parent=grid_layout,
                                command=lambda x: self.build_limb_cmd())
        close_btn = cmds.button(label='Close', height=40, parent=grid_layout,
                                command=lambda x: cmds.deleteUI(self.window))

    def collapse_cmd(self, frame_layout, height):
        window_height = cmds.window(self.window, query=True, height=True)
        frame_height = cmds.frameLayout(frame_layout, query=True, height=True)
        cmds.window(self.window, e=True, height=window_height - height + 25)
        cmds.frameLayout(frame_layout, e=True,
                         height=frame_height - height + 25)

    def expand_cmd(self, frame_layout, height):
        window_height = cmds.window(self.window, query=True, height=True)
        frame_height = cmds.frameLayout(frame_layout, query=True, height=True)
        cmds.window(self.window, e=True, height=window_height + height - 25)
        cmds.frameLayout(frame_layout, e=True,
                         height=frame_height + height - 25)

    def change_base_name(self):
        side = cmds.textField(self.side_txt, query=True, text=True)
        part = cmds.textField(self.part_txt, query=True, text=True)
        cmds.textField(self.base_txt, edit=True, text=side + '_' + part)

    def load_sel(self, text_field):
        sel = cmds.ls(selection=True)
        if len(sel):
            cmds.textField(text_field, e=True, tx=sel[0])

    def build_limb_cmd(self):
        # side, part, joint_list, alias_list, pole_vector,
        # remove_guides, add_stretch, primary_axis, up_axis
        side = cmds.textField(self.side_txt, query=True, text=True)
        part = cmds.textField(self.part_txt, query=True, text=True)
        pole_vector = cmds.textField(self.pv_guide, query=True,
                                     text=True)
        alias_list = []
        for a in self.alias_list:
            alias_list.append(cmds.textField(a, query=True, text=True))

        joint_list = []
        for j in self.joint_list:
            joint_list.append(cmds.textField(j, query=True, text=True))

        remove_guides = cmds.checkBox(self.remove_cb, query=True, value=True)
        add_stretch = cmds.checkBox(self.stretch_cb, query=True, value=True)
        pa_active = cmds.radioCollection(self.pa_col, query=True, select=True)
        up_active = cmds.radioCollection(self.ua_col, query=True, select=True)
        primary_axis = cmds.radioButton(pa_active, query=True, label=True)
        up_axis = cmds.radioButton(up_active, query=True, label=True)

        pr_color = cmds.colorSliderGrp(self.pr_color, query=True, rgb=True)
        sc_color = cmds.colorSliderGrp(self.sc_color, query=True, rgb=True)
        fk_color = cmds.colorSliderGrp(self.fk_color, query=True, rgb=True)
        pv_color = cmds.colorSliderGrp(self.pv_color, query=True, rgb=True)

        color_dict = {side + '_' + part + '_primary': pr_color,
                      side + '_' + part + '_pv': pv_color,
                      side + '_' + part + '_fk': fk_color,
                      side + '_' + part + '_secondary': sc_color}

        limb = nmLimb.Limb(side=side, part=part, joint_list=joint_list,
                           alias_list=alias_list, pole_vector=pole_vector,
                           remove_guides=remove_guides, add_stretch=add_stretch,
                           color_dict=color_dict, primary_axis=primary_axis,
                           up_axis=up_axis)
        limb.build_limb()
