import maya.cmds as cmds
import math

import nmrig.shelfUtils as nmUtil
reload(nmUtil)

class Limb():
    def __init__(self, side='L', part='arm',
                 joint_list=None,
                 alias_list=None,
                 pole_vector=None,
                 remove_guides=False,
                 add_stretch=False,
                 color_dict=False,
                 primary_axis='X',
                 up_axis='Y'):

        # define variables
        self.side = side
        self.part = part
        self.joint_list = joint_list
        self.alias_list = alias_list
        self.pole_vector = pole_vector
        self.remove_guides = remove_guides
        self.add_stretch = add_stretch
        self.color_dict = color_dict
        self.primary_axis = primary_axis
        self.up_axis = up_axis
        self.base_name = self.side + '_' + self.part

        # check to make sure proper arguments were passed
        if len(joint_list) != 3:
            cmds.error('Must provide three guides to build three joint limb.')

        if len(alias_list) != 3:
            cmds.error('Must provide three aliases, one for each joint.')

        if not pole_vector:
            cmds.error('Must provide a pole vector guide.')

        self.pa = self.define_axis(self.primary_axis)
        self.ua = self.define_axis(self.up_axis)

    def build_limb(self):
        # create fk, ik, and bind chain
        self.ik_chain = self.create_chain('IK')
        self.fk_chain = self.create_chain('FK')
        self.bind_chain = self.create_chain('bind')

        # optimize control size by using a fraction of the start-to-end length
        self.r = self.distance_between(self.fk_chain[0],
                                       self.fk_chain[-1]) / float(5)

        # create ik/fk & settings controls
        self.create_fk_controls()
        self.create_ik_controls()
        self.create_settings_control()

        # blend fk and ik chains into bind chain
        self.blend_chains()

        # create IKH
        ikh = cmds.ikHandle(name=self.base_name + '_IKH',
                            startJoint=self.ik_chain[0],
                            endEffector=self.ik_chain[-1], sticky='sticky',
                            solver='ikRPsolver', setupForRPsolver=True)[0]
        cmds.parentConstraint(self.local_ctrl, ikh, mo=True)
        cmds.poleVectorConstraint(self.pv_ctrl, ikh)

        # add stretch
        self.no_xform_list = [ikh]
        if self.add_stretch:
            self.add_ik_stretch()
            self.add_fk_stretch()

        # clean up and finalize rig
        self.organize_hierarchy()
        self.add_global_scale()
        self.finalize()

    def create_fk_controls(self):
        # create FK controls and connect to fk joint chain
        self.fk_ctrls = []
        for i, alias in enumerate(self.alias_list):
            # create FK controls
            ctrl = cmds.circle(radius=self.r, normal=self.pa, degree=3,
                               name='{}_{}_FK_CTRL'.format(self.side, alias))[0]
            self.tag_control(ctrl, self.base_name + '_fk')
            if i != 0:
                # parent to previous control
                cmds.parent(ctrl, par)

            # align control to joint
            ctrl_off = nmUtil.align_lras(snap_align=True,
                                         sel=[ctrl, self.fk_chain[i]])
            if i == 0:
                self.fk_top_grp = ctrl_off

            # define parent control to be used in iterations after the first one
            par = ctrl
            # connect control to joint
            cmds.pointConstraint(ctrl, self.fk_chain[i])
            cmds.connectAttr(ctrl + '.rotate', self.fk_chain[i] + '.rotate')
            self.fk_ctrls.append(ctrl)

    def create_ik_controls(self):
        # world control
        self.world_ctrl = cmds.circle(radius=self.r * 1.2, normal=self.pa,
                                      degree=1, sections=4,
                                      constructionHistory=False,
                                      name=self.base_name + '_IK_CTRL')[0]
        cmds.setAttr(self.world_ctrl + '.rotate' + self.primary_axis[-1], 45)
        nmUtil.a_to_b(is_trans=True, is_rot=False,
                      sel=[self.world_ctrl, self.ik_chain[-1]], freeze=True)
        self.tag_control(self.world_ctrl, self.base_name + '_primary')

        # local control
        self.local_ctrl = cmds.circle(radius=self.r, normal=self.pa,
                                      degree=1, sections=4,
                                      name=self.base_name + '_local_IK_CTRL')[0]
        cmds.setAttr(self.local_ctrl + '.rotate' + self.primary_axis[-1], 45)
        cmds.makeIdentity(self.local_ctrl, apply=True, rotate=True)
        local_off = nmUtil.align_lras(snap_align=True,
                                      sel=[self.local_ctrl, self.ik_chain[-1]])
        cmds.parent(local_off, self.world_ctrl)
        self.tag_control(self.local_ctrl, self.base_name + '_secondary')

        # pole vector control
        loc_points = [[0.0, 1.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 0.0],
                      [-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 0.0],
                      [0.0, 0.0, -1.0], [0.0, 0.0, 1.0]]
        self.pv_ctrl = self.curve_control(loc_points,
                                          name=self.base_name + '_PV_CTRL')
        cmds.setAttr(self.pv_ctrl + '.scale',
                     self.r * 0.25, self.r * 0.25, self.r * 0.25)
        nmUtil.a_to_b(is_trans=True, is_rot=False,
                      sel=[self.pv_ctrl, self.pole_vector], freeze=True)
        self.tag_control(self.pv_ctrl, self.base_name + '_pv')

        # base control
        self.base_ctrl = cmds.circle(radius=self.r * 1.2, normal=self.pa,
                                     degree=1, sections=4,
                                     constructionHistory=False,
                                     name='{}_{}_IK_CTRL'.format(
                                         self.side, self.alias_list[0]))[0]
        cmds.setAttr(self.base_ctrl + '.rotate' + self.primary_axis[-1], 45)
        nmUtil.a_to_b(is_trans=True, is_rot=False,
                      sel=[self.base_ctrl, self.ik_chain[0]], freeze=True)
        cmds.parentConstraint(self.base_ctrl, self.ik_chain[0], mo=True)
        self.tag_control(self.base_ctrl, self.base_name + '_primary')

    def create_settings_control(self):
        plus_points = [[-0.333, 0.333, 0.0], [-0.333, 1.0, 0.0],
                       [0.333, 1.0, 0.0], [0.333, 0.333, 0.0],
                       [1.0, 0.333, 0.0], [1.0, -0.333, 0.0],
                       [0.333, -0.333, 0.0], [0.333, -1.0, 0.0],
                       [-0.333, -1.0, 0.0], [-0.333, -0.333, 0.0],
                       [-1.0, -0.333, 0.0], [-1.0, 0.333, 0.0],
                       [-0.333, 0.333, 0.0]]
        self.settings_ctrl = self.curve_control(
            point_list=plus_points, name=self.base_name + '_settings_CTRL')
        self.tag_control(self.settings_ctrl, self.base_name + '_primary')
        self.settings_off = nmUtil.align_lras(
            snap_align=True, sel=[self.settings_ctrl, self.ik_chain[-1]])
        cmds.setAttr(self.settings_ctrl + '.scale',
                     self.r * 0.25, self.r * 0.25, self.r * 0.25)
        if self.up_axis[0] == '-':
            cmds.setAttr(self.settings_ctrl + '.translate' + self.up_axis[-1],
                         self.r * -1.5)
        else:
            cmds.setAttr(self.settings_ctrl + '.translate' + self.up_axis[-1],
                         self.r * 1.5)
        cmds.makeIdentity(self.settings_ctrl, apply=True, translate=True,
                          rotate=True, scale=True, normal=False)
        cmds.parentConstraint(self.bind_chain[-1], self.settings_ctrl, mo=True)
        cmds.addAttr(self.settings_ctrl, attributeType='double', min=0, max=1,
                     defaultValue=1, keyable=True, longName='fkIk')

    def create_chain(self, suffix):
        chain = []
        for j, a in zip(self.joint_list, self.alias_list):
            if j == self.joint_list[0]:
                par = None
            else:
                par = jnt
            jnt = cmds.joint(par, n='{}_{}_{}_JNT'.format(self.side, a, suffix))
            nmUtil.a_to_b(sel=[jnt, j], freeze=True)
            chain.append(jnt)
        return chain

    def blend_chains(self):
        # hook up switching
        for ik, fk, bind in zip(self.ik_chain, self.fk_chain, self.bind_chain):
            for attr in ['translate', 'rotate', 'scale']:
                bcn = cmds.createNode('blendColors',
                                      n=bind.replace('bind_JNT', attr + '_BCN'))
                cmds.connectAttr(ik + '.' + attr, bcn + '.color1')
                cmds.connectAttr(fk + '.' + attr, bcn + '.color2')
                cmds.connectAttr(self.base_name + '_settings_CTRL.fkIk',
                                 bcn + '.blender')
                cmds.connectAttr(bcn + '.output', bind + '.' + attr)

    def distance_between(self, node_a, node_b):
        point_a = cmds.xform(node_a, query=True, worldSpace=True,
                             rotatePivot=True)
        point_b = cmds.xform(node_b, query=True, worldSpace=True,
                             rotatePivot=True)
        dist = math.sqrt(
            sum([pow((b - a), 2) for b, a in zip(point_b, point_a)]))
        return dist

    def define_axis(self, axis):
        if axis[-1] == 'X':
            vector_axis = (1, 0, 0)
        elif axis[-1] == 'Y':
            vector_axis = (0, 1, 0)
        elif axis[-1] == 'Z':
            vector_axis = (0, 0, 1)
        else:
            cmds.error('Must provide either X, Y, or Z for the axis.')

        if '-' in axis:
            vector_axis = tuple(va * -1 for va in vector_axis)
        return vector_axis

    def tag_control(self, ctrl, tag_name):
        cmds.addAttr(ctrl, ln='controlType', dataType='string')
        cmds.setAttr(ctrl + '.controlType', tag_name, type='string')

    def curve_control(self, point_list, name, degree=1):
        crv = cmds.curve(degree=degree, p=point_list, name=name)
        shp = cmds.listRelatives(crv, shapes=True)[0]
        cmds.rename(shp, crv + 'Shape')
        return crv

    def add_ik_stretch(self):
        # create measure nodes for stretch
        limb_dist = cmds.createNode('distanceBetween',
                                    name=self.base_name + '_DST')
        self.limb_cnd = cmds.createNode('condition',
                                        name=self.base_name + '_CND')
        start_loc = cmds.spaceLocator(name=self.base_name + '_start_LOC')[0]
        end_loc = cmds.spaceLocator(name=self.base_name + '_end_LOC')[0]
        self.stretch_mdn = cmds.createNode('multiplyDivide',
                                      name=self.base_name + '_stretch_MDN')
        self.no_xform_list += [start_loc, end_loc]

        # calculate length
        length_a = self.distance_between(self.ik_chain[0], self.ik_chain[1])
        length_b = self.distance_between(self.ik_chain[1], self.ik_chain[2])
        self.length_total = length_a + length_b

        # measure limb length
        cmds.pointConstraint(self.base_ctrl, start_loc, maintainOffset=False)
        cmds.pointConstraint(self.local_ctrl, end_loc, maintainOffset=False)
        cmds.connectAttr(start_loc + '.worldMatrix[0]',
                         limb_dist + '.inMatrix1')
        cmds.connectAttr(end_loc + '.worldMatrix[0]', limb_dist + '.inMatrix2')

        # calculate length ratio
        cmds.connectAttr(limb_dist + '.distance', self.stretch_mdn + '.input1X')
        cmds.setAttr(self.stretch_mdn + '.input2X', self.length_total)
        cmds.setAttr(self.stretch_mdn + '.operation', 2)

        cmds.connectAttr(limb_dist + '.distance', self.limb_cnd + '.firstTerm')
        cmds.connectAttr(self.stretch_mdn + '.outputX',
                         self.limb_cnd + '.colorIfTrueR')
        cmds.setAttr(self.limb_cnd + '.secondTerm', self.length_total)
        cmds.setAttr(self.limb_cnd + '.operation', 3)

        # add on/off for stretch
        cmds.addAttr(self.world_ctrl, attributeType='double', min=0, max=1,
                     defaultValue=1, keyable=True, longName='stretch')
        up_name = 'up' + self.part.title()
        lo_name = 'lo' + self.part.title()
        cmds.addAttr(self.world_ctrl, attributeType='double', min=0.001,
                     defaultValue=1, keyable=True, longName=up_name)
        cmds.addAttr(self.world_ctrl, attributeType='double', min=0.001,
                     defaultValue=1, keyable=True, longName=lo_name)
        stretch_bta = cmds.createNode('blendTwoAttr', 
                                      name=self.base_name + '_stretch_BTA')
        cmds.setAttr(stretch_bta + '.input[0]', 1)
        cmds.connectAttr(self.limb_cnd + '.outColorR',
                         stretch_bta + '.input[1]')
        cmds.connectAttr(self.world_ctrl + '.stretch',
                         stretch_bta + '.attributesBlender')
        up_pma = cmds.createNode('plusMinusAverage', name=up_name + '_PMA')
        lo_pma = cmds.createNode('plusMinusAverage', name=lo_name + '_PMA')
        cmds.connectAttr(self.world_ctrl + '.' + up_name,
                         up_pma + '.input1D[0]')
        cmds.connectAttr(self.world_ctrl + '.' + lo_name,
                         lo_pma + '.input1D[0]')
        cmds.connectAttr(stretch_bta + '.output', up_pma + '.input1D[1]')
        cmds.connectAttr(stretch_bta + '.output', lo_pma + '.input1D[1]')
        cmds.setAttr(up_pma + '.input1D[2]', -1)
        cmds.setAttr(lo_pma + '.input1D[2]', -1)

        cmds.connectAttr(up_pma + '.output1D',
                         self.ik_chain[0] + '.scale' + self.primary_axis[-1])
        cmds.connectAttr(lo_pma + '.output1D',
                         self.ik_chain[1] + '.scale' + self.primary_axis[-1])

    def add_fk_stretch(self):
        for i, ctrl in enumerate(self.fk_ctrls):
            if not ctrl == self.fk_ctrls[-1]:
                cmds.addAttr(ctrl, attributeType='double', min=0.001,
                             defaultValue=1, keyable=True, longName='stretch')
                mdl = cmds.createNode('multDoubleLinear',
                                      name=ctrl.replace('CTRL', '_stretch_MDL'))
                loc = cmds.spaceLocator(name=self.fk_chain[i + 1].replace(
                    'JNT', 'OFF_LOC'))[0]
                cmds.parent(loc, self.fk_chain[i])
                nmUtil.a_to_b(sel=[loc, self.fk_chain[i + 1]])
                offset_val = cmds.getAttr(
                    loc + '.translate' + self.primary_axis[-1])
                cmds.setAttr(mdl + '.input1', offset_val)
                cmds.connectAttr(ctrl + '.stretch', mdl + '.input2')
                cmds.connectAttr(mdl + '.output',
                                 loc + '.translate' + self.primary_axis[-1])
                cmds.connectAttr(ctrl + '.stretch',
                                 self.fk_chain[i] + '.scale' +
                                 self.primary_axis[-1])
                if cmds.objExists(self.fk_ctrls[i + 1] + '.offsetParentMatrix'):
                    cmds.connectAttr(loc + '.matrix',
                                     self.fk_ctrls[
                                         i + 1] + '.offsetParentMatrix')
                else:
                    dcm = cmds.createNode('decomposeMatrix', name=loc + '_DCM')
                    cmds.connectAttr(loc + '.matrix', dcm + '.inputMatrix')
                    for attr in ['translate', 'rotate', 'scale']:
                        cmds.connectAttr(dcm + '.output' + attr.title(),
                                         self.fk_ctrls[
                                             i + 1] + '_OFF_GRP.' + attr)

    def organize_hierarchy(self):
        # organize
        self.fk_ctrl_grp = cmds.group(em=True,
                                      name=self.base_name + '_FK_CTRL_GRP')
        self.ik_ctrl_grp = cmds.group(em=True,
                                      name=self.base_name + '_IK_CTRL_GRP')
        self.skeleton_grp = cmds.group(em=True,
                                       name=self.base_name + '_skeleton_GRP')
        self.no_xform_grp = cmds.group(em=True,
                                       name=self.base_name + '_noXform_GRP')
        self.limb_rig_grp = cmds.group(em=True,
                                       name=self.base_name + '_rig_GRP')
        self.all_grp = cmds.group(em=True, name=self.base_name.upper())
    
        cmds.parent(self.world_ctrl, self.pv_ctrl, self.base_ctrl,
                    self.ik_ctrl_grp)
        cmds.parent(self.fk_top_grp, self.fk_ctrl_grp)
        cmds.parent(self.bind_chain[0], self.skeleton_grp)
        cmds.parent(self.no_xform_list, self.no_xform_grp)
        cmds.parent(self.fk_ctrl_grp, self.ik_ctrl_grp, self.no_xform_grp,
                    self.fk_chain[0], self.ik_chain[0], self.settings_off,
                    self.limb_rig_grp)
        cmds.parent(self.skeleton_grp, self.limb_rig_grp, self.all_grp)
        nmUtil.transfer_pivots(sel=[self.bind_chain[0], self.skeleton_grp,
                                    self.limb_rig_grp, self.fk_ctrl_grp,
                                    self.ik_ctrl_grp])
        cmds.hide(self.no_xform_grp, self.fk_chain[0], self.ik_chain[0],
                  self.bind_chain[0])

    def add_global_scale(self):
        # compensate for global scale
        cmds.addAttr(self.all_grp, attributeType='double', min=0.001,
                     defaultValue=1, keyable=True, longName='globalScale')
        [cmds.connectAttr(self.all_grp + '.globalScale',
                          self.all_grp + '.scale' + axis) for axis in 'XYZ']
        if self.add_stretch:
            gs_mdl = cmds.createNode('multDoubleLinear',
                                     name=self.base_name + '_globalScale_MDL')
            cmds.setAttr(gs_mdl + '.input1', self.length_total)
            cmds.connectAttr(self.all_grp + '.globalScale', gs_mdl + '.input2')
            cmds.connectAttr(gs_mdl + '.output', self.stretch_mdn + '.input2X')
            cmds.connectAttr(gs_mdl + '.output', self.limb_cnd + '.secondTerm')

    def finalize(self):
        # finalize
        if not self.color_dict:
            self.color_dict = {self.base_name + '_primary': [1, 1, 0],
                               self.base_name + '_pv': [0, 1, 1],
                               self.base_name + '_fk': [0, 0, 1],
                               self.base_name + '_secondary': [0, 0.2, 1]}

        for color_tag in cmds.ls(self.side + '*.controlType'):
            ctrl = color_tag.split('.')[0]
            ctrl_type = cmds.getAttr(color_tag)
            if self.base_name in ctrl_type:
                cmds.setAttr(ctrl + '.overrideEnabled', 1)
                cmds.setAttr(ctrl + '.overrideRGBColors', 1)
                cmds.setAttr(ctrl + '.overrideColorRGB',
                             self.color_dict[ctrl_type][0],
                             self.color_dict[ctrl_type][1],
                             self.color_dict[ctrl_type][2])

        # Lock and hide attributes
        self.lock_and_hide(self.fk_ctrls,
                           attribute_list=['translate', 'scale', 'visibility'])
        self.lock_and_hide([self.world_ctrl, self.local_ctrl, self.base_ctrl],
                           attribute_list=['scale', 'visibility'])
        self.lock_and_hide(self.pv_ctrl,
                           attribute_list=['rotate', 'scale', 'visibility'])
        self.lock_and_hide(self.settings_ctrl)

        # toggle fk/ik visibility
        vis_rev = cmds.createNode('reverse',
                                  name=self.base_name + '_fkIk_vis_REV')
        cmds.connectAttr(self.settings_ctrl + '.fkIk', vis_rev + '.inputX')
        cmds.connectAttr(self.settings_ctrl + '.fkIk',
                         self.ik_ctrl_grp + '.visibility')
        cmds.connectAttr(vis_rev + '.outputX',
                         self.fk_ctrl_grp + '.visibility')

        pv_gde = self.add_guide(self.pv_ctrl, self.ik_chain[1])
        cmds.parent(pv_gde[0], self.no_xform_grp)
        cmds.parent(pv_gde[1], self.ik_ctrl_grp)

        # remove guide joints
        if self.remove_guides:
            cmds.delete(self.joint_list, self.pole_vector)

    def lock_and_hide(self, nodes, attribute_list=None):
        if not attribute_list:
            attribute_list = ['translate', 'rotate', 'scale', 'visibility']

        if not isinstance(nodes, list):
            nodes = [nodes]

        for node in nodes:
            for attr in attribute_list:
                if any(t == attr for t in ['translate', 'rotate', 'scale']):
                    [cmds.setAttr(node + '.' + attr + axis,
                                  lock=True, keyable=False) for axis in 'XYZ']
                else:
                    cmds.setAttr(node + '.' + attr, lock=True, keyable=False)

    def add_guide(self, start, end):
        start_pos = cmds.xform(start, query=True, worldSpace=True,
                              rotatePivot=True)
        end_pos = cmds.xform(end, query=True, worldSpace=True,
                             rotatePivot=True)

        gde = self.curve_control([start_pos, end_pos], name=start + '_GDE')
        start_cls = cmds.cluster(gde + '.cv[0]', name=start + '_CLS')[1]
        end_cls = cmds.cluster(gde + '.cv[1]', name=end + '_CLS')[1]
        cmds.pointConstraint(start, start_cls)
        cmds.pointConstraint(end, end_cls)
        cmds.setAttr(gde + '.template', True)
        cmds.setAttr(gde + '.inheritsTransform', False)

        return [[start_cls, end_cls], gde]
