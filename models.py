#-*-coding:utf-8-*-
from openerp import fields,api
from openerp import models
from email.utils import formataddr
import email
from email.header import Header

class equipment_info(models.Model):
    _name ='asset_management.equipment_info'
    _rec_name = 'sn'

    sn = fields.Char(string=u"序列号",required=True)
    firms = fields.Char( string=u"设备厂商",required=True)
    device_type = fields.Char(string=u"设备类型",required=True)
    asset_number = fields.Char(string=u"资产编号",required=True)
    unit_type = fields.Char(string=u"设备型号",required=True)
    equipment_source = fields.Char(string=u"设备来源",required=True)
    equipment_status = fields.Selection([(u'库存', u"库存"),
                               (u'故障', u"故障"),
                               (u'专用', u"专用"),
                               (u'待报废', u"待报废"),
                               (u'暂存', u"暂存"),
                               ],string=u"设备状态",required=True)
    equipment_use = fields.Selection([
                               (u'公共备件', u"公共备件"),
                               (u'专用备件', u"专用备件"),
                               (u'故障件', u"故障件"),
                               (u'待报废', u"待报废"),
                               (u'暂存设备', u"暂存设备"),
                                ],string=u"设备用途",required=True)
    state = fields.Selection([
        (u'待入库',u'待入库'),
        (u'已入库',u'已入库'),
        (u'流程中',u'流程中'),
        (u'领用',u'领用'),
        (u'借用',u'借用'),
        (u'IT环境',u'IT环境'),
        (u'归还',u'归还'),
    ],string='状态',default=u'待入库')
    owner = fields.Many2one('res.users',string=u"归属人",required=True)
    company = fields.Boolean(string=u"公司资产",required=True)
    note = fields.Char(string=u"备注")
    floor = fields.Char(string=u"存放楼层")
    area = fields.Char(string=u"存放区域")
    seat = fields.Char(string=u"库存位置")
    machine_room = fields.Char(string=u"存放机房")
    cabinet_number = fields.Char(string=u"机柜编号")
    start_u_post = fields.Char(string=u"起始U位")
    storage_id = fields.Many2many('asset_management.equipment_storage',"storge_equipment_ref",)
    get_ids = fields.Many2many('asset_management.equipment_get',"get_equipment_ref",)
    lend_ids = fields.Many2many('asset_management.equipment_lend',"lend_equipment_ref",)
    apply_ids = fields.Many2many('asset_management.equipment_it_apply',"it_equipment_ref" ,)


    _sql_constraints = [
        ('SN UNIQUE',
         'UNIQUE(sn)',
         '该序列号已存在'),
    ]

    def send_email(self,cr, uid, users, data=[], context=None):
        # template_model = self.pool.get('email.template')
        # ids = template_model.search(cr, uid, [('name', '=', 'case邮件提醒')], context=None)
        # template = template_model.browse(cr, uid, ids, context=None)
        to_list = []
        for user in users:
            to_list.append(formataddr((Header(user.name, 'utf-8').encode(), user.email)))
        mail_mail = self.pool.get('mail.mail')
        for i in range(len(data)):
            if not data[i]:
                data[i] = ''
        mail_id = mail_mail.create(cr, uid, {
            'body_html': '<div><p>您好:</p>'
                         '<p>这个申请单需要您处理,您可登录：<a href="http://123.56.147.94:8000">http://123.56.147.94:8000</a></p></div>',
            # 'subject': 'Re: %s+%s+%s' %(str(data[0]).decode('utf-8').encode('gbk'),str(data[1]).decode('utf-8').encode('gbk'),str(data[2]).decode('utf-8').encode('gbk')),
            'subject': data[0] + u',' + data[1],
            'email_to': to_list,
            'auto_delete': True,
        }, context=context)
        mail_mail.send(cr, uid, [mail_id], context=context)


class equipment_storage(models.Model):
    _name = 'asset_management.equipment_storage'
    _rec_name = 'storage_id'

    @api.multi
    def _default_SN(self):
        return self.env['asset_management.equipment_info'].search([('state', '=', u'待入库')])

    storage_id = fields.Char(string=u"入库单号")
    user_id = fields.Many2one('res.users', string=u"申请人",default=lambda self: self.env.user, required=True)
    approver_id = fields.Many2one('res.users', string=u"审批人",default=lambda self: self.env.user,)
    # SN = fields.Char()
    SN = fields.Many2many('asset_management.equipment_info',"storge_equipment_ref",string=u"设备SN",required=True,default=_default_SN,domain=[('state','=',u'待入库')])
    state = fields.Selection([
        ('demander', u"需求方申请"),
        ('ass_admin', u"资产管理员"),
        ('ass_admin_manager', u"MA主管"),
        ('owner', u"资产归属人"),
        ('done',u'完成')
    ],string=u"状态",required=True,default='demander')
    owners = fields.Many2many('res.users', string=u'设备归属人', ondelete='set null')
    store_exam_ids = fields.One2many('asset_management.entry_store_examine', 'store_id', string='审批记录')

    def create(self, cr, uid, vals, context=None):
        template_model = self.pool.get('asset_management.equipment_info')
        devices = template_model.browse(cr, uid, vals['SN'][0][2], context=None)
        for device in devices:
            device.state = u'流程中'
        dates = fields.Date.today().split('-')
        date = ''.join(dates)
        template_model = self.pool.get('asset_management.equipment_storage')
        ids = template_model.search(cr, uid, [('storage_id', 'like', date)], context=None)
        stores = template_model.browse(cr, uid, ids, context=None).sorted(key=lambda r: r.storage_id)
        if len(stores):
            vals['storage_id'] = 'S' + str(int(stores[-1].storage_id[1:]) + 1)
        else:
            vals['storage_id'] = 'S' + date + '001'
        return super(equipment_storage, self).create(cr, uid, vals, context=context)

    @api.multi
    def action_to_confirm(self):
        for sn in self.SN:
            if sn.owner:
                self.owners |= sn.owner

        if len(self.owners) == 1:
            if (self.owners[0] == self.user_id or self.owners[0] == self.env['res.groups'].search(
                    [('name', '=', u'资产管理员')], limit=1).users[0]) and self.user_id != self.env['res.groups'].search(
                    ['name', '=', u'资产管理员'], limit=1):
                self.state = 'owner'
                approver_id =self.owners[0]
                self.owners[0] -= approver_id
                self.approver_id = self.owners[0]


            elif self.owners[0] == self.user_id == \
                    self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0] and self.user_id != self.env['res.groups'].search([('name', '=', u'资产管理部门主管')], limit=1).users[0]:
                self.state = 'ass_admin_manager'
                self.owners -= self.user_id
                self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理部门主管')], limit=1).users[0]


            elif self.user_id !=self.env['res.groups'].search(
                    [('name', '=', u'资产管理员')], limit=1).users[0]:
                self.state = 'ass_admin'
                self.approver_id = self.env['res.groups'].search(
                    [('name', '=', u'资产管理员')], limit=1).users[0]

            else:
                self.state = 'done'
                self.approver_id =None

        elif len(self.owners) > 1:

            if self.user_id in self.owners:
                self.owners -= self.user_id
            if self.env['res.groups'].search([('name', '=', '资产管理员')], limit=1).users[0] in self.owners:
                self.owners -= self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]
            self.state = 'ass_admin'
            self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]
        else:
            self.state = 'ass_admin'
            self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]
        if self.approver_id and self.approver_id != self.user_id:
            data=[u'入库申请',self.storage_id]
            device=self.env['asset_management.equipment_info'].search([('state', '=', u'待入库')],limit=1)
            device.send_email([self.approver_id],data)

    @api.multi
    def action_to_next(self):
        self.env['asset_management.entry_store_examine'].create(
            {'approver_id': self.approver_id.id, 'result': u'通过', 'store_id': self.id})
        if self.state == 'owner':
            if len(self.owners):

                approver_id = self.owners[0]
                self.state = 'owner'
                self.owners -= approver_id
                self.approver_id = approver_id
            else:
                self.state = 'ass_admin_manager'
                self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理部门主管')], limit=1).users[0]

        elif self.state == 'ass_admin':
            approver_id = self.owners[0]
            self.state = 'owner'
            self.owners -= approver_id
            self.approver_id = approver_id

        elif self.state == 'ass_admin_manager':
            self.state = 'done'
            for device in self.SN:
                device.state = u'已入库'
            self.approver_id = None
        if self.approver_id:
            data = [u'入库申请', self.storage_id]
            device = self.env['asset_management.equipment_info'].search([('state', '=', u'待入库')], limit=1)
            device.send_email([self.approver_id], data)

    @api.multi
    def action_to_demander(self):
        self.state = 'demander'
        self.env['asset_management.get_examine'].create(
            {'approver_id': self.approver_id.id, 'result': u'拒绝', 'store_id': self.id})
        self.approver_id = self.user_id
        data = [self.storage_id,u'入库申请被退回']
        device = self.env['asset_management.equipment_info'].search([('state', '=', u'待入库')], limit=1)
        device.send_email([self.approver_id], data)




class equipment_lend(models.Model):
    _name = 'asset_management.equipment_lend'
    _rec_name = 'lend_id'

    def _default_SN(self):
        return self.env['asset_management.equipment_info'].browse(self._context.get('active_ids'))

    @api.multi
    def subscribe(self):
        return {'aaaaaaaaaaaaaa'}

    lend_id = fields.Char(string=u"借用单号")
    user_id = fields.Many2one('res.users', string=u"申请人",default=lambda self: self.env.user,required=True)
    #user_id = fields.Many2one('res.users', string=u"申请人",required=True)
    approver_id = fields.Many2one('res.users',default=lambda self: self.env.user,string=u"审批人",)
    SN = fields.Many2many('asset_management.equipment_info',"lend_equipment_ref", string=u"设备SN",default=_default_SN,required=True)
    state = fields.Selection([
            ('demander', u"需求方申请"),
            ('ass_owner', u"资产归属人"),
            ('ass_admin', u"资产管理员"),
            ('dem_leader', u"需求方直属部门领导"),
            ('dem_leader_manager', u"需求方直属主管"),# 副总裁级
            ('ass_director', u"资产管理部门负责人"),
            ('ass_admin_manager', u"资产管理部门主管"),  # 副总裁级MA
        ('done', u'结束'),
        ('back', u'归还')
    ], string=u"状态", required=True,default='demander')
    lend_date = fields.Date(string=u"借用日期",required=True)
    promise_date = fields.Date(string=u"承诺归还日期",required=True)
    actual_date = fields.Date(string=u"实际归还日期")
    lend_purpose = fields.Char(string=u"借用目的",required=True)
    owners = fields.Many2many('res.users',string=u"归属人们")
    lend_exam_ids = fields.One2many('asset_management.lend_examine','lend_id',string='审批记录')

    def create(self, cr, uid, vals, context=None):
        template_model = self.pool.get('asset_management.equipment_info')
        devices = template_model.browse(cr, uid, vals['SN'][0][2], context=None)
        for device in devices:
            device.state = u'借用'
        dates = fields.Date.today().split('-')
        date = ''.join(dates)
        template_model = self.pool.get('asset_management.equipment_lend')
        ids = template_model.search(cr, uid, [('lend_id', 'like', date)], context=None)
        lends = template_model.browse(cr, uid, ids, context=None).sorted(key=lambda r: r.lend_id)
        if len(lends):
            vals['lend_id'] = 'L' + str(int(lends[-1].lend_id[1:]) + 1)
        else:
            vals['lend_id'] = 'L' + date + '001'
        return super(equipment_lend, self).create(cr, uid, vals, context=context)

    @api.multi
    def action_to_confirm(self):
        self.env['asset_management.lend_examine'].create(
            {'approver_id': self.user_id.id, 'result': u'借用', 'lend_id': self.id})
        for sn in self.SN:
            if sn.equipment_use == u"公共备件":
                continue
            elif sn.equipment_use == u"专用备件":
                self.owners |= sn.owner

        if len(self.owners) > 0:
            if self.user_id in self.owners:
                self.owners -= self.user_id

            if self.env['res.groups'].search([('name', '=', '资产管理员')], limit=1).users[0] in self.owners:
                self.owners -= self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]

            if self.user_id.employee_ids[0].department_id.manager_id.user_id in self.owners:
                self.owners -= self.user_id.employee_ids[0].department_id.manager_id.user_id

            if len(self.owners) > 0:
                self.state = 'ass_owner'
                approver_id = self.owners[0]
                self.owners -= approver_id
                self.approver_id = approver_id

            elif len(self.owners) == 0:
                self.state = 'ass_admin'
                self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]

        elif len(self.owners) == 0:
            self.state = 'ass_admin'
            self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]

        else:
            print '<1' * 80
        if self.approver_id:
            data = [u'借用申请', self.lend_id]
            device = self.env['asset_management.equipment_info'].search([('state', '=', u'待入库')], limit=1)
            device.send_email([self.approver_id], data)

    @api.multi
    def action_to_next(self):
        id = self.env['asset_management.lend_examine'].create(
            {'approver_id': self.approver_id.id, 'result': u'通过', 'lend_id': self.id})
        if self.state == 'ass_owner':
            if len(self.owners):
                # 先改变状态,再找到下一个处理人
                self.state = 'ass_owner'
                approver_id = self.owners[0]
                self.owners -= approver_id
                self.approver_id = approver_id
            else:
                if self.user_id != self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]:
                    self.state = 'ass_admin'
                    self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]
                else:
                    if self.user_id != self.user_id.employee_ids[0].department_id.manager_id.user_id:
                        self.state = 'dem_leader'
                        self.approver_id = self.user_id.employee_ids[0].department_id.manager_id.user_id
                    else:
                        self.state = 'dem_leader_manager'
                        # 归 = 申 = 管 =  部
                        self.approver_id = self.user_id.employee_ids[0].department_id.parent_id.manager_id.user_id

        elif self.state == 'ass_admin':
            if self.user_id != self.user_id.employee_ids[0].department_id.manager_id.user_id:
                self.state = 'dem_leader'
                self.approver_id = self.user_id.employee_ids[0].department_id.manager_id.user_id
            else:
                # 申请者是王涛时
                self.state = 'dem_leader_manager'
                self.approver_id = self.user_id.employee_ids[0].department_id.parent_id.manager_id.user_id


        elif self.state == 'dem_leader':  # 到哪个状态说明,哪个状态与申请人不重合
            self.state = 'dem_leader_manager'
            self.approver_id = self.user_id.employee_ids[0].department_id.parent_id.manager_id.user_id


        elif self.state == 'dem_leader_manager':
            self.state = 'ass_director'
            self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理部门负责人')], limit=1).users[0]

        elif self.state == 'ass_director':
            self.state = 'ass_admin_manager'
            self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理部门主管')], limit=1).users[0]

        elif self.state == 'ass_admin_manager':
            self.state = 'done'
            for device in self.SN:
                device.state = u'借用'
            self.approver_id = self.user_id

            # self.approver_id = self.user_id

        
        # data = [u'借用申请', self.lend_id]
        # device = self.env['asset_management.equipment_info'].search([('state', '=', u'待入库')], limit=1)
        # device.send_email([self.approver_id], data)

    @api.multi
    def action_to_demander(self):
        self.state = 'demander'
        self.approver_id = self.user_id
        self.env['asset_management.lend_examine'].create(
            {'approver_id': self.approver_id.id, 'result': u'拒绝', 'lend_id': self.id})
        data = [self.lend_id,u'借用申请被退回',]
        device = self.env['asset_management.equipment_info'].search([('state', '=', u'待入库')], limit=1)
        device.send_email([self.approver_id], data)

    @api.multi
    def action_to_renew(self):
        id = self.env['asset_management.lend_examine'].create(
            {'approver_id': self.user_id.id, 'result': u'续借', 'reason': u'发起续借', 'lend_id': self.id})
        self.state = 'ass_admin_manager'
        self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理部门主管')], limit=1).users[0]

    @api.multi
    def action_to_back(self):
        self.state = 'back'
        self.approver_id = None
        print
        self.env['asset_management.back_to_store'].create({'back_id': 'aaaaaaaa', 'state': 'ass_admin', 'approver_id':
            self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0].id})
        back = self.env['asset_management.back_to_store'].search([])[-1]
        for sn in self.SN:
            if sn.state == u'借用':
                back.SN |= sn

class equipment_get(models.Model):
    _name = 'asset_management.equipment_get'
    _rec_name = 'get_id'

    def _default_SN(self):
        return self.env['asset_management.equipment_info'].browse(self._context.get('active_ids'))
    get_id = fields.Char(string=u"领用单号")
    user_id = fields.Many2one('res.users', string=u"申请人", default=lambda self: self.env.user,required=True)
    approver_id = fields.Many2one('res.users', string=u"审批人",default=lambda self: self.env.user)
    SN = fields.Many2many('asset_management.equipment_info',"get_equipment_ref",string=u"设备SN", default=_default_SN,required=True)
    state = fields.Selection([
             ('demander', u"需求方申请"),
             ('ass_owner', u"资产归属人"),
             ('ass_admin', u"资产管理员"),
             ('dem_leader', u"需求方直属部门领导"),
             ('ass_director', u"资产管理部门负责人"),
             ('ass_admin_manager', u"资产管理部门主管"),  # 副总裁级MA
        ('done',u'结束'),
        ('back',u'归还')

    ], string=u"状态", required=True,default='demander')
    get_date = fields.Date(string=u"领用日期",)
    get_purpose = fields.Char(string=u"领用目的",required=True)
    owners = fields.Many2many('res.users',string=u'设备归属人',ondelete = 'set null')
    get_exam_ids = fields.One2many('asset_management.get_examine','get_id',string='审批记录')

    def create(self, cr, uid, vals, context=None):
        template_model = self.pool.get('asset_management.equipment_info')
        print vals['SN'][0][2]
        devices = template_model.browse(cr, uid, vals['SN'][0][2], context=None)
        for device in devices:
            device.state = u'领用'
        dates = fields.Date.today().split('-')
        date = ''.join(dates)
        template_model = self.pool.get('asset_management.equipment_get')
        ids = template_model.search(cr, uid, [('get_id', 'like', date)], context=None)
        gets = template_model.browse(cr, uid, ids, context=None).sorted(key=lambda r: r.get_id)
        if len(gets):
            vals['get_id'] = 'G' + str(int(gets[-1].get_id[1:]) + 1)
        else:
            vals['get_id'] = 'G' + date + '001'
        return super(equipment_get, self).create(cr, uid, vals, context=context)

    @api.multi
    def subscribe(self):
        # for sn in self.SN:
        #     sn.state = '领用'

        return {}

    @api.multi
    def action_to_confirm(self):
        owners = []
        for sn in self.SN:
            if sn.owner:
                self.owners |= sn.owner

        if len(self.owners) ==1:
            if  (self.owners[0] == self.user_id or self.owners[0] == self.env['res.groups'].search([('name','=',u'资产管理员')],limit=1).users[0]) and self.user_id != self.env['res.groups'].search(['name','=',u'资产管理员'],limit=1):
                self.state = 'ass_admin'
                self.approver_id = self.env['res.groups'].search([('name','=',u'资产管理员')],limit=1).users[0]

            elif self.owners[0] == self.user_id  == self.env['res.groups'].search([('name','=',u'资产管理员')],limit=1).users[0] and self.user_id != self.user_id.employee_ids[0].department_id.manager_id:
                self.state = 'dem_leader'
                self.approver_id = self.user_id.employee_ids[0].department_id.manager_id

            elif self.owners[0] == self.user_id.employee_ids[0].department_id.manager_id:
                self.owners -= self.user_id.employee_ids[0].department_id.manager_id

            elif self.user_id != self.owners[0]:
                approver_id = self.owners[0]
                self.state = 'ass_owner'
                self.owners -= approver_id
                self.approver_id = approver_id

        elif len(self.owners)>1:

            if self.user_id in self.owners:
                self.owners -= self.user_id
            if self.env['res.groups'].search([('name','=','资产管理员')],limit=1).users[0] in self.owners:
                self.owners -= self.env['res.groups'].search([('name','=',u'资产管理员')],limit=1).users[0]

            if self.user_id.employee_ids[0].department_id.manager_id.user_id in self.owners:
                self.owners -= self.user_id.employee_ids[0].department_id.manager_id.user_id
            if len(self.owners):
                approver_id = self.owners[0]
                self.state = 'ass_owner'
                self.owners -= approver_id
                self.approver_id = approver_id
            else:
                self.state = 'ass_admin'
                self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]
        else:
            if self.user_id != self.env['res.groups'].search([('name','=',u'资产管理员')],limit=1).users[0]:
                self.state = 'ass_admin'
                self.approver_id = self.env['res.groups'].search([('name','=',u'资产管理员')],limit=1).users[0]
            else:
                self.state = 'dem_leader'
                self.approver_id = self.user_id.employee_ids[0].department_id.manager_id.user_id
        if self.approver_id:
            data = [u'领用申请', self.get_id]
            device = self.env['asset_management.equipment_info'].search([('state', '=', u'待入库')], limit=1)
            device.send_email([self.approver_id], data)

    @api.multi
    def action_to_next(self):
        self.env['asset_management.get_examine'].create(
            {'approver_id': self.approver_id.id, 'result': u'通过', 'get_id': self.id})
        if self.state == 'ass_owner':
            if len(self.owners):

                approver_id = self.owners[0]
                self.state = 'ass_owner'
                self.owners -= approver_id
                self.approver_id = approver_id
            elif self.user_id == self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]:
                self.state = 'dem_leader'
                self.approver_id = self.user_id.employee_ids[0].department_id.manager_id.user_id
            else:
                self.state = 'ass_admin'
                self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]

        elif self.state == 'ass_admin':
            if self.user_id != self.user_id.employee_ids[0].department_id.manager_id.user_id:
                self.state = 'dem_leader'
                self.approver_id = self.user_id.employee_ids[0].department_id.manager_id.user_id
            else:
                self.state = 'ass_director'
                self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理部门负责人')], limit=1).users[0]
        elif self.state == 'dem_leader':

            self.state = 'ass_director'
            self.approver_id = self.env['res.groups'].search([('name','=',u'资产管理部门负责人')],limit=1).users[0]

        elif self.state == 'ass_director':
            self.state = 'ass_admin_manager'
            self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理部门主管')], limit=1).users[0]

        elif self.state == 'ass_admin_manager':
            self.state = 'done'
            for device in self.SN:
                device.state = u'领用'
            self.approver_id = self.user_id
        if self.approver_id:
            data = [u'领用申请', self.get_id]
            device = self.env['asset_management.equipment_info'].search([('state', '=', u'待入库')], limit=1)
            device.send_email([self.approver_id], data)


    @api.multi
    def action_to_demander(self):
        self.state = 'demander'
        self.env['asset_management.get_examine'].create(
            {'approver_id': self.approver_id.id, 'result': u'拒绝', 'get_id': self.id})
        self.approver_id = self.user_id
        if self.approver_id:
            data = [self.get_id,u'领用申请被退回']
            device = self.env['asset_management.equipment_info'].search([('state', '=', u'待入库')], limit=1)
            device.send_email([self.approver_id], data)

    @api.multi
    def action_to_back(self):
        self.state = 'back'
        self.approver_id = None
        print
        self.env['asset_management.back_to_store'].create({'back_id':'aaaaaaaa','state':'ass_admin','approver_id': self.env['res.groups'].search([('name','=',u'资产管理员')],limit=1).users[0].id})
        back = self.env['asset_management.back_to_store'].search([])[-1]
        for sn in self.SN:
            if sn.state == u'领用':
                back.SN |= sn

class equipment_it_apply(models.Model):
    _name = 'asset_management.equipment_it_apply'
    _rec_name = 'apply_id'

    def _default_SN(self):
        return self.env['asset_management.equipment_info'].browse(self._context.get('active_ids'))

    @api.multi
    def subscribe(self):
        return {'aaaaaaaaaaaaaa'}

    apply_id = fields.Char(string=u"申请IT环境单号")
    user_id = fields.Many2one('res.users', string=u"申请人",default=lambda self: self.env.user,required=True)
    approver_id = fields.Many2one('res.users', string=u"审批人",default=lambda self: self.env.user,)
    SN = fields.Many2many('asset_management.equipment_info',"it_equipment_ref" ,string=u"设备SN",default=_default_SN, required=True)
    state = fields.Selection([
        ('demander', u"需求方申请"),
        ('ass_owner', u"资产归属人"),
        ('ass_admin', u"资产管理员"),
        ('dem_leader', u"需求方直属部门领导"),
        ('dem_leader_manager', u"需求方直属部门总经理"),
        ('ass_director', u"资产管理部门负责人"),
        ('ass_admin_manager', u"资产管理部门主管"),  # 副总裁级MA
        ('done', u'结束'),
        ('back', u'归还')
    ], string=u"状态", required=True, default='demander')
    use_begin = fields.Date(string=u"使用开始时间",required=True)
    use_over = fields.Date(string=u"使用结束时间",required=True)
    up_date = fields.Date(string=u"设备上架时间",required=True)
    down_date = fields.Date(string=u"设备下架时间",required=True)
    tester = fields.Many2one('res.users',string=u"测试人员",required=True)
    # 这个需要邮件提醒
    application_purpose = fields.Char(string=u"申请目的",required=True)
    owners = fields.Many2many('res.users',string=u"归属人们")
    apply_exam_ids = fields.One2many('asset_management.it_examine','IT_id',string='审批记录')

    def create(self, cr, uid, vals, context=None):
        template_model = self.pool.get('asset_management.equipment_info')
        devices = template_model.browse(cr, uid, vals['SN'][0][2], context=None)
        for device in devices:
            device.state = u'IT环境'
        dates = fields.Date.today().split('-')
        date = ''.join(dates)
        template_model = self.pool.get('asset_management.equipment_it_apply')
        ids = template_model.search(cr, uid, [('apply_id', 'like', date)], context=None)
        applys = template_model.browse(cr, uid, ids, context=None).sorted(key=lambda r: r.apply_id)
        if len(applys):
            vals['apply_id'] = 'I' + str(int(applys[-1].apply_id[1:]) + 1)
        else:
            vals['apply_id'] = 'I' + date + '001'
        return super(equipment_it_apply, self).create(cr, uid, vals, context=context)

    @api.multi
    def action_to_confirm(self):
        for sn in self.SN:
            if sn.equipment_use == u"公共备件":
                continue
            elif sn.equipment_use == u"专用备件":
                self.owners |= sn.owner
        print self.owners

        if len(self.owners) > 0:
            if self.user_id in self.owners:
                self.owners -= self.user_id

            if self.env['res.groups'].search([('name', '=', '资产管理员')], limit=1).users[0] in self.owners:
                self.owners -= self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]

            if self.user_id.employee_ids[0].department_id.manager_id.user_id in self.owners:
                self.owners -= self.user_id.employee_ids[0].department_id.manager_id.user_id

            if len(self.owners) > 0:
                self.state = 'ass_owner'
                approver_id = self.owners[0]
                print self.owners
                self.owners -= approver_id
                self.approver_id = approver_id

            elif len(self.owners) == 0:
                self.state = 'ass_admin'
                self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]

        elif len(self.owners) == 0:
            self.state = 'ass_admin'
            self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]

        else:
            print '<1' * 80
        if self.approver_id:
            data = [u'IT环境申请', self.apply_id]
            device = self.env['asset_management.equipment_info'].search([('state', '=', u'待入库')], limit=1)
            device.send_email([self.approver_id], data)

    @api.multi
    def action_to_next(self):  #
        id = self.env['asset_management.it_examine'].create(
            {'approver_id': self.approver_id.id, 'result': u'通过', 'IT_id': self.id})
        if self.state == 'ass_owner':
            if len(self.owners):
                # 先改变状态,再找到下一个处理人
                self.state = 'ass_owner'
                approver_id = self.owners[0]
                self.owners -= approver_id
                self.approver_id = approver_id

            else:
                if self.user_id != self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]:
                    self.state = 'ass_admin'
                    self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]
                else:
                    if self.user_id != self.user_id.employee_ids[0].department_id.manager_id.user_id:
                        self.state = 'dem_leader'
                        self.approver_id = self.user_id.employee_ids[0].department_id.manager_id.user_id
                    else:
                        self.state = 'dem_leader_manager'
                        # 归 = 申 = 管 =  部
                        self.approver_id = self.user_id.employee_ids[0].department_id.parent_id.manager_id.user_id

        elif self.state == 'ass_admin':
            if self.user_id != self.user_id.employee_ids[0].department_id.manager_id.user_id:
                self.state = 'dem_leader'
                self.approver_id = self.user_id.employee_ids[0].department_id.manager_id.user_id
            else:
                # 申请者是王涛时
                self.state = 'dem_leader_manager'
                self.approver_id = self.user_id.employee_ids[0].department_id.parent_id.manager_id.user_id


        elif self.state == 'dem_leader':  # 到哪个状态说明,哪个状态与申请人不重合
            self.state = 'dem_leader_manager'
            self.approver_id = self.user_id.employee_ids[0].department_id.parent_id.manager_id.user_id


        elif self.state == 'dem_leader_manager':
            self.state = 'ass_director'
            self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理部门负责人')], limit=1).users[0]

        elif self.state == 'ass_director':
            self.state = 'ass_admin_manager'
            self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理部门主管')], limit=1).users[0]

        elif self.state == 'ass_admin_manager':
            self.state = 'done'

            for device in self.SN:
                device.state = u'IT环境'
            self.approver_id = self.user_id

        if self.approver_id:
            data = [u'IT环境申请', self.apply_id]
            device = self.env['asset_management.equipment_info'].search([('state', '=', u'待入库')], limit=1)
            device.send_email([self.approver_id], data)

    @api.multi
    def action_to_demander(self):
        self.state = 'demander'
        self.approver_id = self.user_id
        self.env['asset_management.it_examine'].create(
            {'approver_id': self.approver_id.id, 'result': u'拒绝', 'IT_id': self.id})
        if self.approver_id:
            data = [ self.storage_id,u'IT环境申请被退回']
            device = self.env['asset_management.equipment_info'].search([('state', '=', u'待入库')], limit=1)
            device.send_email([self.approver_id], data)

    @api.multi
    def action_to_back(self):
        self.state = 'back'
        self.approver_id = None
        print
        self.env['asset_management.back_to_store'].create({'back_id': 'aaaaaaaa', 'state': 'ass_admin', 'approver_id':
            self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0].id})
        back = self.env['asset_management.back_to_store'].search([])[-1]
        for sn in self.SN:
            if sn.state == u'IT环境':
                back.SN |= sn


class back_to_store(models.Model):
    _name = 'asset_management.back_to_store'
    _rec_name = 'back_id'

    def _default_SN(self):
        return self.env['asset_management.equipment_info'].browse(self._context.get('active_ids'))

    @api.multi
    def subscribe(self):
        return {'aaaaaaaaaaaaaa'}

    back_id = fields.Char(string=u"归还单号")
    user_id = fields.Many2one('res.users', string=u"申请人",default=lambda self: self.env.user, required=True)
    approver_id = fields.Many2one('res.users', string=u"审批人",default=lambda self: self.env.user)
    SN = fields.Many2many('asset_management.equipment_info', "back_equipment_ref", string=u"设备SN",default= _default_SN,
                          required=True,)
    state = fields.Selection([

        ('demander', u"归还方申请"),
        ('ass_admin', u"资产管理员"),
        ('done', u'结束')
    ], string=u"状态", required=True, default='demander')
    back_date = fields.Date(string=u"归还时间",)
    back_exam_ids = fields.One2many('asset_management.back_examine', 'back_id', string='审批记录')
    lend_id = fields.Many2one('asset_management.equipment_lend',string='借用单')
    get_id = fields.Many2one('asset_management.equipment_storage',string='领用单')
    it_apply_id = fields.Many2one('asset_management.equipment_it_apply',string='it申请单')

    def create(self, cr, uid, vals, context=None):
        template_model = self.pool.get('asset_management.equipment_info')
        devices = template_model.browse(cr, uid, vals['SN'][0][2], context=None)
        for device in devices:
            device.state = u'归还'
        dates = fields.Date.today().split('-')
        date = ''.join(dates)
        template_model = self.pool.get('asset_management.back_to_store')
        ids = template_model.search(cr, uid, [('back_id', 'like', date)], context=None)
        backs = template_model.browse(cr, uid, ids, context=None).sorted(key=lambda r: r.back_id)
        if len(backs):
            vals['back_id'] = 'B' + str(int(backs[-1].back_id[1:]) + 1)
        else:
            vals['back_id'] = 'B' + date + '001'
        return super(back_to_store, self).create(cr, uid, vals, context=context)

    @api.multi
    def action_to_confirm(self):
        self.state = 'ass_admin'
        self.approver_id = self.env['res.groups'].search([('name', '=', u'资产管理员')], limit=1).users[0]
        data = [u'设备归还', self.back_id]
        device = self.env['asset_management.equipment_info'].search([('state', '=', u'待入库')], limit=1)

        # print dir('equipment_info')
        # device = self.pool.get('asset_management.equipment_info')
        print device
        device.send_email([self.approver_id], data)

    @api.multi
    def action_to_next(self):
        self.env['asset_management.back_examine'].create(
            {'approver_id': self.approver_id.id, 'result': u'通过', 'back_id': self.id})
        self.state = 'done'
        for sn in self.SN:
            sn.state = u'已入库'
        self.approver_id = None

    @api.multi
    def action_to_demander(self):
        self.env['asset_management.back_examine'].create(
            {'approver_id': self.approver_id.id, 'result': u'拒绝', 'back': self.id})
        self.state = 'demander'
        data = [u'设备归还申请被退回', self.back_id]
        device = self.env['asset_management.equipment_info'].search([('state', '=', u'待入库')], limit=1)
        self.approver_id = self.user_id


class entry_store_examine(models.Model):
    _name='asset_management.entry_store_examine'
    # _rec_name = 'exam_num'

    # exam_num = fields.Char(sting='审批id')
    approver_id = fields.Many2one('res.users',required = 'True',string='审批人')
    date = fields.Date(string='审批时间')
    result=fields.Selection([
                               (u'通过', u"通过"),
                               (u'拒绝', u"拒绝"),

                                ],string=u"通过")
    store_id = fields.Many2one('asset_management.equipment_storage',string='入库单')
    reason = fields.Char(string='原因')

class lend_examine(models.Model):
    _name = 'asset_management.lend_examine'
    # _rec_name = 'exam_num'
    #
    # exam_num = fields.Char(sting='审批id')
    approver_id = fields.Many2one('res.users', required='True', string='审批人')
    date = fields.Date(string='审批时间',default=lambda self:fields.Date.today())
    result = fields.Selection([
        (u'通过', u"通过"),
        (u'拒绝', u"拒绝"),
        (u'借用', u"借用"),
        (u'续借', u"续借"),

    ], string=u"通过")
    lend_id = fields.Many2one('asset_management.equipment_lend', string='借用单')
    reason = fields.Char(string='原因')

class get_examine(models.Model):
    _name = 'asset_management.get_examine'
    # _rec_name = 'exam_num'
    #
    # exam_num = fields.Char(sting='审批id')
    approver_id = fields.Many2one('res.users', required='True', string='审批人')
    date = fields.Date(string='审批时间',default=lambda self:fields.Date.today())
    result = fields.Selection([
        (u'通过', u"通过"),
        (u'拒绝', u"拒绝"),

    ], string=u"通过")
    get_id = fields.Many2one('asset_management.equipment_get', string='领用')
    reason = fields.Char(string='原因')

class it_examine(models.Model):
    _name = 'asset_management.it_examine'
    # _rec_name = 'exam_num'
    #
    # exam_num = fields.Char(sting='审批id')
    approver_id = fields.Many2one('res.users', required='True', string='审批人')
    date = fields.Date(string='审批时间',default=lambda self:fields.Date.today())
    result = fields.Selection([
        (u'通过', u"通过"),
        (u'拒绝', u"拒绝"),

    ], string=u"通过")
    IT_id = fields.Many2one('asset_management.equipment_it_apply', string='IT环境申请单')
    reason = fields.Char(string='原因')

class back_examine(models.Model):
    _name = 'asset_management.back_examine'
    # _rec_name = 'exam_num'
    #
    # exam_num = fields.Char(sting='审批id')
    approver_id = fields.Many2one('res.users', required='True', string='审批人')
    date = fields.Date(string='审批时间',default=lambda self:fields.Date.today())
    result = fields.Selection([
        (u'通过', u"通过"),
        (u'拒绝', u"拒绝"),

    ], string=u"通过")
    back_id = fields.Many2one('asset_management.back_to_store', string='设备归还单')
    reason = fields.Char(string='原因')
