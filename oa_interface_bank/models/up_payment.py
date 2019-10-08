# -*- coding: utf-8 -*-
import datetime
import json
import time
import requests
from odoo import models, api, fields
import logging
import sys
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

reload(sys)
sys.setdefaultencoding('utf-8')

_logger = logging.getLogger(__name__)


class UpPayment(models.Model):
    _name = 'oa.interface.bank'
    _inherit = ['mail.thread']
    _rec_name = 'name'
    _description = u"上传付款单"

    @api.model
    def select_objects(self):
        model_ids = self.env["ir.model"].sudo().search([
            ('model', 'in', ['oa.financial.daily', 'oa.financial.other.daily',
                             'oa.financial.fixed.assets', 'oa.financial.meet.training', 'oa.financial.travel',
                             'oa.financial.entertain', 'oa.financial.vehicle.reimb', 'oa.financial.transport',
                             'oa.financial.info.sys', 'oa.financial.car.maintain', 'oa.financial.car.out',
                             'oa.financial.taxation', 'oa.financial.borrowing', 'oa.financial.refund.bank',
                             'oa.financial.fund.account', 'oa.financial.intermediary', 'oa.financial.approval',
                             'oa.financial.payment.approval'])
        ])
        return [(model.model, model.name) for model in model_ids]

    CURRENCY = [
        ('CNY', u'人民币'),
        ('USD', u'美元'),
        ('EUR', u'欧元'),
        ('HKD', u'港元'),
        ('JPY', u'日元'),
        ('GBP', u'英镑'),
    ]
    PAYMENTSTATE = [
        ('10', u'草稿'),
        # 增加分期付款状态
        # author: fengjiqiang@inspur.com
        ('05', u'分期付款'),
        # end
        ('00', u'ERP系统确认'),
        ('01', u'银行确认'),
        ('02', u'交易成功'),
        ('03', u'交易失败'),
        ('04', u'无需支付'),
        ('approval', u'待审核'),
    ]
    name = fields.Char(cstring=u"主题")
    company_id = fields.Many2one('res.company', string=u'公司', default=lambda self: self.env.user.company_id.id)
    source_number = fields.Char(string=u"单据编号")
    source_model = fields.Reference(selection=select_objects, string=u'待付款单')
    source_model_name = fields.Char(string=u'模型名称')
    public_signs = fields.Selection(selection=[('00', u'对公'), ('01', u'对私')], string=u"公私标识", default='00')
    payment_model = fields.Selection(string=u"付款模式", selection=[('01', u'普通'), ('02', u'加快'), ], default='01')
    cross_row_identi = fields.Selection(string=u"跨行标识", selection=[('0', u'本行'), ('1', u'跨行'), ], default='0')
    off_site_identi = fields.Selection(string=u"异地标识", selection=[('0', u'异地'), ('1', u'同城'), ], default='0')
    payee_identi = fields.Selection(string=u"收款标识", selection=[('01', u'对外付款'), ('02', u'对内转账'), ], default='01')
    debit_identi = fields.Selection(string=u"借贷标识", selection=[('D', u'借'), ('C', u'贷'), ], default='D')
    pay_bank = fields.Many2one(comodel_name='oa.financial.bank.number', string=u"选择开户行", compute='_compute_partner_id',
                               store=True)
    currency_type = fields.Selection(string=u'币种', selection=CURRENCY, default='CNY', required=True)
    partner_id = fields.Char(string=u"实际收款户名", readonly=True, compute='_compute_partner_id', store=True)
    partner_two = fields.Char(string=u"补充收款户名")
    partner_state = fields.Selection(string=u'partnerState', selection=[('y', 'y'), ('n', 'n'), ],
                                     compute='_compute_partner_state')
    partner_bank_number = fields.Char(string=u"收款账号", compute='_compute_partner_id', store=True)
    partner_number = fields.Char(string=u"客户编号", compute='_compute_partner_id', store=True)
    partner_contact = fields.Char(string=u"收款联系人")
    partner_contact_phone = fields.Char(string=u"联系人电话")
    partner_contact_add = fields.Char(string=u"联系人地址")
    pay_money = fields.Float(string=u"付款金额", digits=(12, 2), compute='_compute_partner_id', store=True)
    pay_summary = fields.Char(string=u"摘要")
    pay_use = fields.Char(string=u"付款用途")
    state = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'10')
    alter_id = fields.Many2one(comodel_name='oa.interface.payment.alter', string=u'变更单')
    alter_state = fields.Selection(string=u'变更状态', selection=[('0', u'未变更'), ('1', u'已变更'), ], default='0')
    # 增加待付款金额字段以及约束条件
    # author: fengjiqiang@inspur.com
    payment_line_ids = fields.One2many('oa.interface.bank.line', 'payment_id', string=u"付款明细")
    paied_money = fields.Float(string=u"已付款金额", default=0, compute='_compute_money', store=True)
    pay_remain_money = fields.Float(string=u"待付款金额", compute='_compute_remain_money', store=True)
    pay_per_money_sum = fields.Float(string=u"本次待提交金额", default=0, compute='_compute_money', store=True)

    @api.depends('payment_line_ids')
    def _compute_money(self):
        self.pay_per_money_sum = 0
        self.paied_money = 0
        for line in self.payment_line_ids:
            if line.state == 'unsubmitted':
                self.pay_per_money_sum += line.pay_per_money
            if line.state == 'paied':
                self.paied_money += line.pay_per_money
        self.pay_remain_money = self.pay_money - self.paied_money

    @api.depends('paied_money')
    def _compute_remain_money(self):
        self.pay_remain_money = self.pay_money - self.paied_money

    @api.constrains('payment_line_ids')
    def _constrains_payment(self):
        pay_money = 0
        for line in self.payment_line_ids:
            if line.pay_per_money <= 0:
                raise ValidationError('支付金额必须大于0！')
            if line.state in ['submitted', 'unsubmitted']:
                pay_money += line.pay_per_money
        if pay_money > self.pay_remain_money:
            raise ValidationError('提交金额不能超过待付款金额！')
        if self.pay_per_money_sum <= 0:
            raise ValidationError('本次待提交金额必须大于0！')
    # end

    # this_payment = fields.Float(string=u"本次支付", digits=(12, 2), store=True)
    # remaining_payable = fields.Float(string=u"剩余待付", digits=(12, 2), compute='_compute_remaining_payable',store=True)
    #
    # @api.depends('pay_money', 'this_payment')
    # def _compute_remaining_payable(self):
    #     """付款单剩余待支付计算
    #         剩余待支付 = 付款金额 - 本次支付
    #     """
    #     for res in self:
    #         res.remaining_payable = res.pay_money - res.this_payment

    @api.constrains('state')
    def _constrains_state(self):
        if self.state == '00':
            self.message_post(body=u"单据状态已变更为ERP系统确认。", message_type='notification')
        if self.state == '01':
            self.message_post(body=u"单据状态已变更为银行确认。", message_type='notification')
        if self.state == '02':
            self.message_post(body=u"单据状态已变更为交易成功。", message_type='notification')
        if self.state == '03':
            self.message_post(body=u"单据状态已变更为交易失败。", message_type='notification')
        if self.state == '04':
            self.message_post(body=u"单据状态已变更为无需支付。", message_type='notification')
        if self.state == 'approval':
            self.message_post(body=u"单据状态已变更为待审核。", message_type='notification')

    @api.depends('source_model')
    def _compute_partner_id(self):
        for res in self:
            if res.source_model:
                # 当前选择的单据模型名称
                model_name = res.source_model._name
                model = self.env['ir.model'].search([('model', '=', model_name)])
                config = self.find_model_config(model)
                # 收款人户名
                pay_name_id = self.get_model_value(config.pay_name.name, model_name, res.source_model.id)
                res.partner_id = pay_name_id[1] if pay_name_id else False
                res.partner_state = 'y' if pay_name_id else 'n'
                # 主题
                res.name = self.get_model_value(config.form_name.name, model_name, res.source_model.id)
                # 获取公司
                company = self.get_model_value(config.company.name, model_name, res.source_model.id)
                res.company_id = company[0] if company else False
                # 单据编号
                res.source_number = self.get_model_value(config.form_number.name, model_name, res.source_model.id)
                # 收款账号
                res.partner_bank_number = self.get_model_value(config.pay_number.name, model_name, self.source_model.id)
                # 客户编号
                res.partner_number = self.get_model_value(config.customer_code.name, model_name, self.source_model.id)
                # 开户行
                bank = self.get_model_value(config.pay_bank.name, model_name, self.source_model.id)
                res.pay_bank = bank[0] if bank else False
                # 金额
                res.pay_money = self.get_model_value(config.money.name, model_name, self.source_model.id)
                # 摘要
                res.pay_summary = self.get_model_value(config.summary.name, model_name, self.source_model.id)

    @api.onchange('source_model')
    def onchange_relation(self):
        return {'domain': {"source_model": [('submit_state', '=', '03'), ('bank_pay_type', '=', '00')]}}

    @api.constrains('source_model')
    def constrains_source_model(self):
        if self.source_model:
            self.source_model_name = self.source_model._name

    @api.constrains('state')
    def constrains_state(self):
        if self.state == '10':
            self.update_model_pay_state(self.source_model._name, '01', self.source_model.id)
        elif self.state == '00':
            self.update_model_pay_state(self.source_model._name, '02', self.source_model.id)
        elif self.state == '02':
            self.message_post(body=u"交易已成功", message_type='notification')
            self.update_model_pay_state(self.source_model._name, '03', self.source_model.id)
        elif self.state == '03':
            self.message_post(body=u"交易已失败", message_type='notification')
            self.update_model_pay_state(self.source_model._name, '04', self.source_model.id)
        elif self.state == '04':
            self.message_post(body=u"该笔交易为无需支付的单据", message_type='notification')
            self.update_model_pay_state(self.source_model._name, '05', self.source_model.id)

    @api.depends('source_model')
    def _compute_partner_state(self):
        for res in self:
            if res.partner_id:
                res.partner_state = 'y'

    @api.multi
    def unlink(self):
        for res in self:
            if res.state != '10':
                raise UserError(u"单据已在执行中,不允许删除!")
            self.update_model_pay_state(res.source_model._name, '00', res.source_model.id)
        return super(UpPayment, self).unlink()

    @api.model
    def update_model_pay_state(self, model_name, value, id):
        """更新模板的付款状态"""
        self._cr.execute(
            """UPDATE {} SET bank_pay_type = '{}' WHERE id = {}""".format(model_name.replace('.', '_'), value, id))

    @api.model
    def find_model_config(self, model):
        config = self.env['oa.interface.bank.config'].search([('model_id', '=', model.id)])
        return config

    @api.model
    def get_model_value(self, fie, model_name, model_id):
        if fie:
            new_model = self.env[model_name].search_read([('id', '=', model_id)], [fie])
            for model in new_model:
                return model.get(fie) if model.get(fie) else ''

    @api.multi
    def up_payment_to_erp(self):
        """上传付款请求"""
        if self.pay_bank:
            if not self.pay_bank.bank_name:
                raise UserError(u'开户行中-归属银行字段不能为空,请维护！')
            if not self.pay_bank.name_provincial:
                raise UserError(u'开户行中-省份字段不能为空,请维护！')
            if not self.pay_bank.name_area:
                raise UserError(u'开户行中-城市字段不能为空,请维护！')
        system_name = self.env['ir.values'].get_default('oa.financial.base.config', 'system_name')
        system_code = self.env['ir.values'].get_default('oa.financial.base.config', 'system_code')
        bank_erp_url = self.env['ir.values'].get_default('oa.financial.base.config', 'bank_erp_url')
        out_time = self.env['ir.values'].get_default('oa.financial.base.config', 'out_time')
        if not system_code or not system_name or not bank_erp_url:
            raise UserError(u"请先配置ERP相关接口信息！外部接口配置项!")
        # 上报时间
        for res in self:
            if not res.partner_id:
                if not res.partner_two:
                    raise UserError(u"付款户名不能为空!")
            if not res.partner_bank_number:
                raise UserError(u"付款账号不能为空!")
            # 增加付款明细
            # author: fengjiqiang@inspur.com
            payment_line_sets = []
            for line in res.payment_line_ids.filtered(lambda x: x.state == 'unsubmitted'):
                record = {
                    "pay_per_money": line.pay_per_money,
                }
                payment_line_sets.append([0, 0, record])
            if res.pay_per_money_sum <= 0:
                raise ValidationError("没有付款记录可传！")
            # end
            # 封装请求数据
            pay_data = {
                "system_name": system_name,
                "system_code": system_code,
                "create_date": res.create_date[:10],
                "create_time": "00:00:00",
                "payments": {
                    "source_number": res.source_number if res.source_number else '',
                    "source_model": res.source_model._name,
                    "company_code": res.company_id.code if res.company_id else '0',
                    "public_signs": res.public_signs,
                    "payment_model": res.payment_model,
                    "cross_row_identi": res.cross_row_identi,
                    "off_site_identi": res.off_site_identi,
                    "payee_identi": res.payee_identi,
                    "debit_identi": res.debit_identi,
                    "payee_bank": res.pay_bank.bank_name.address.replace(' ', '') if res.pay_bank.bank_name else '',
                    "payee_bank_code": res.pay_bank.bank_name.code.replace(' ', '') if res.pay_bank.bank_name else '',
                    "payee_opening_bank": res.pay_bank.bank_id.replace(' ', '') if res.pay_bank.bank_id else '',
                    "payee_opening_bank_code": res.pay_bank.bank_code.replace(' ', '') if res.pay_bank.bank_id else '',
                    "payee_opening_province": res.pay_bank.name_provincial.name.replace(' ',
                                                                                        '') if res.pay_bank.name_provincial else '',
                    "payee_opening_province_code": res.pay_bank.name_provincial.provincial_id.replace(' ',
                                                                                                      '') if res.pay_bank.name_provincial else '',
                    "abc_provincial_code": res.pay_bank.name_provincial.abc_provincial_code.replace(' ',
                                                                                                    '') if res.pay_bank.name_provincial else '',
                    "payee_opening_city": res.pay_bank.name_area.name.replace(' ',
                                                                              '') if res.pay_bank.name_area else '',
                    "payee_opening_city_code": res.pay_bank.name_area.provincial_id.replace(' ',
                                                                                            '') if res.pay_bank.name_area else '',
                    "abc_city_code": res.pay_bank.name_area.abc_provincial_code.replace(' ',
                                                                                        '') if res.pay_bank.name_area else '',
                    "currency_type": res.currency_type if res.currency_type else 'CNY',
                    "partner_id": res.partner_id.replace(' ', '') if res.partner_id else res.partner_two,
                    "partner_bank_number": res.partner_bank_number.replace(' ', '') if res.partner_bank_number else '',
                    "partner_number": res.partner_number if res.partner_number else '0000001',
                    "partner_contact": res.partner_contact if res.partner_contact else '',
                    "partner_contact_phone": res.partner_contact_phone if res.partner_contact_phone else '',
                    "partner_contact_add": res.partner_contact_add if res.partner_contact_add else '',
                    "pay_money": res.pay_money,
                    "pay_summary": res.pay_summary if res.pay_summary else '',
                    "pay_use": "《{}》".format(res.name if res.name else ''),
                    # 付款明细
                    # author: fengjiqiang@inspur.com
                    "payment_line_ids": payment_line_sets
                    # end
                },
            }
            # 发送数据至ERP系统
            try:
                logging.info(pay_data)
                headers = {'Content-Type': 'application/json'}
                result = requests.post(url=bank_erp_url, headers=headers, data=json.dumps(pay_data), timeout=out_time)
            except TypeError as e:
                raise UserError(u"TypeError异常错误,可能原因是上传付款地址不正确！返回信息：{}".format(e.message))
            except requests.exceptions.Timeout:
                raise UserError(u'上传付款单超时: 当前等待时间为{}秒！'.format(out_time))
            except Exception as e:
                raise UserError(u'上传失败: 失败原因：'.format(e.message))
            try:
                result = json.loads(result.text)
                result = json.loads(result.get('result'))
                logging.info("result:{}".format(result))
                if result.get('state') != '0000':
                    raise UserError(u"上传失败,错误详情：{}".format(result.get('message')))
                # 增加判断 如果多次付款，状态更新为05分期付款(新增状态)，否则状态更新为ERP系统确认
                # @author: fengjiqiang@inspur.com:
                for line in res.payment_line_ids:
                    if line.state == "unsubmitted":
                        res.payment_line_ids.write({'state': 'submitted'})
                if self.pay_per_money_sum > self.pay_remain_money:
                    raise ValidationError(u"本次待提交金额不能超过待付款金额！！！")
                if self.pay_remain_money > 0:
                    res.write({'state': '05'})
                else:
                    res.write({'state': '00'})
                self.pay_per_money_sum = 0
                # end
                # res.write({'state': '00'})
                res.message_post(body=result['message'], message_type='notification')
            except KeyError as e:
                raise UserError(u"KeyError异常错误：{}".format(e.message))
            except TypeError as e:
                raise UserError(u"TypeError财务系统返回了错误信息！返回信息：{}".format(e.message))

    # 再次付款请求按钮action
    # @author: fengjiqiang@inspur.com
    @api.multi
    def again_up_payment_to_erp(self):
        """再次请求付款"""
        bank_erp_url = self.env['ir.values'].get_default('oa.financial.base.config', 'bank_erp_url')
        out_time = self.env['ir.values'].get_default('oa.financial.base.config', 'out_time')
        for res in self:
            payment_line_sets = []
            record = {}
            for line in res.payment_line_ids.filtered(lambda x: x.state == 'unsubmitted'):
                record = {
                    "pay_per_money": line.pay_per_money,
                }
                payment_line_sets.append([0, 0, record])
            if not record:
                raise ValidationError("没有付款记录可传！")
            # 封装请求数据
            pay_data = {
                "create_date": res.create_date[:10],
                "create_time": "00:00:00",
                "payments": {
                    "source_number": res.source_number if res.source_number else '',
                    "source_model": res.source_model._name,
                    "company_code": res.company_id.code if res.company_id else '0',
                    "public_signs": res.public_signs,
                    "payment_model": res.payment_model,
                    "cross_row_identi": res.cross_row_identi,
                    "off_site_identi": res.off_site_identi,
                    "payee_identi": res.payee_identi,
                    "debit_identi": res.debit_identi,
                    "payee_bank": res.pay_bank.bank_name.address.replace(' ', '') if res.pay_bank.bank_name else '',
                    "payee_bank_code": res.pay_bank.bank_name.code.replace(' ',
                                                                           '') if res.pay_bank.bank_name else '',
                    "payee_opening_bank": res.pay_bank.bank_id.replace(' ', '') if res.pay_bank.bank_id else '',
                    "payee_opening_bank_code": res.pay_bank.bank_code.replace(' ',
                                                                              '') if res.pay_bank.bank_id else '',
                    "payee_opening_province": res.pay_bank.name_provincial.name.replace(' ',
                                                                                        '') if res.pay_bank.name_provincial else '',
                    "payee_opening_province_code": res.pay_bank.name_provincial.provincial_id.replace(' ',
                                                                                                      '') if res.pay_bank.name_provincial else '',
                    "abc_provincial_code": res.pay_bank.name_provincial.abc_provincial_code.replace(' ',
                                                                                                    '') if res.pay_bank.name_provincial else '',
                    "payee_opening_city": res.pay_bank.name_area.name.replace(' ',
                                                                              '') if res.pay_bank.name_area else '',
                    "payee_opening_city_code": res.pay_bank.name_area.provincial_id.replace(' ',
                                                                                            '') if res.pay_bank.name_area else '',
                    "abc_city_code": res.pay_bank.name_area.abc_provincial_code.replace(' ',
                                                                                        '') if res.pay_bank.name_area else '',
                    "currency_type": res.currency_type if res.currency_type else 'CNY',
                    "partner_id": res.partner_id.replace(' ', '') if res.partner_id else res.partner_two,
                    "partner_bank_number": res.partner_bank_number.replace(' ',
                                                                           '') if res.partner_bank_number else '',
                    "partner_number": res.partner_number if res.partner_number else '0000001',
                    "partner_contact": res.partner_contact if res.partner_contact else '',
                    "partner_contact_phone": res.partner_contact_phone if res.partner_contact_phone else '',
                    "partner_contact_add": res.partner_contact_add if res.partner_contact_add else '',
                    "pay_money": res.pay_money,
                    "pay_summary": res.pay_summary if res.pay_summary else '',
                    "pay_use": "《{}》".format(res.name if res.name else ''),
                    # 提交付款记录
                    # @author: fengjiqiang@inspur.com
                    "payment_line_ids": payment_line_sets,
                    # end
                },
            }
            # 发送数据至ERP系统
            try:
                logging.info(pay_data)
                headers = {'Content-Type': 'application/json'}
                result = requests.post(url=bank_erp_url, headers=headers, data=json.dumps(pay_data),
                                       timeout=out_time)
            except TypeError as e:
                raise UserError(u"TypeError异常错误,可能原因是上传付款地址不正确！返回信息：{}".format(e.message))
            except requests.exceptions.Timeout:
                raise UserError(u'上传付款单超时: 当前等待时间为{}秒！'.format(out_time))
            except Exception as e:
                raise UserError(u'上传失败: 失败原因：'.format(e.message))
            try:
                result = json.loads(result.text)
                result = json.loads(result.get('result'))
                logging.info("result:{}".format(result))
                if result.get('state') != '0000':
                    raise UserError(u"上传失败,错误详情：{}".format(result.get('message')))
                for line in res.payment_line_ids:
                    if line.state == "unsubmitted":
                        res.payment_line_ids.write({'state': 'submitted'})
                if self.pay_per_money_sum > self.pay_remain_money:
                    raise ValidationError(u"本次待提交金额不能超过待付款金额！！！")
                if self.pay_remain_money > 0:
                    res.write({'state': '05'})
                else:
                    res.write({'state': '00'})
                self.pay_per_money_sum = 0
                res.message_post(body=result['message'], message_type='notification')
            except KeyError as e:
                raise UserError(u"KeyError异常错误：{}".format(e.message))
            except TypeError as e:
                raise UserError(u"TypeError财务系统返回了错误信息！返回信息：{}".format(e.message))
    # end

    @api.multi
    def search_payment_state(self):
        system_name = self.env['ir.values'].get_default('oa.financial.base.config', 'system_name')
        system_code = self.env['ir.values'].get_default('oa.financial.base.config', 'system_code')
        search_state_url = self.env['ir.values'].get_default('oa.financial.base.config', 'search_state_url')
        out_time = self.env['ir.values'].get_default('oa.financial.base.config', 'out_time')
        if not system_code or not system_name or not search_state_url:
            return False
        payment_list = list()
        for payment in self:
            payment_list.append({
                'form_number': payment.source_number,
                'form_model': payment.source_model._name
            })
        search_data = {
            'system_name': system_name,
            'system_code': system_code,
            'payment': payment_list
        }
        logging.info(search_data)
        # 发送数据至ERP系统
        try:
            logging.info(search_data)
            headers = {'Content-Type': 'application/json'}
            result = requests.post(url=search_state_url, headers=headers, data=json.dumps(search_data),
                                   timeout=out_time)
            result = json.loads(result.text)
            result = json.loads(result.get('result'))
            logging.info(u">>>查询结果消息:{}".format(result.get('message')))
            for res in result.get('results'):
                logging.info(res)
                if res.get('payment_state') != 'F999':
                    self.sudo().write({'state': res.get('payment_state')})
                    state = {
                        '00': u'ERP系统确认',
                        '01': u'银行确认',
                        '02': u'交易成功',
                        '03': u'交易失败',
                        '04': u'无需支付',
                        'approval': u'待审核',
                    }
                    self.message_post(body=u"手动查询结果:{}".format(state[res.get('payment_state')]),
                                      message_type='notification')
        except requests.exceptions.Timeout:
            raise UserError(u'查询数据超时: 当前等待时间为{}秒！'.format(out_time))
        except KeyError as e:
            raise UserError(u"KeyError异常错误：{}".format(e.message))
        except TypeError as e:
            raise UserError(u"TypeError财务系统返回了错误信息！返回信息：{}".format(e.message))
        except ValueError as e:
            raise UserError(u"该单据在ERP中不存在！返回信息：{}".format(e.message))

    @api.multi
    def create_update_from(self):
        for res in self:
            model_str = "{},{}".format(res.source_model._name, res.source_model.id)
            if res.alter_id:
                raise UserError(u"已产生了变更单，只能进行一次变更操作!")
            alter_p = self.env['oa.interface.payment.alter'].create({
                'source_model': model_str,
                'name': res.name,
                'company_id': res.company_id.id,
                'source_number': res.source_number,
                'pay_bank': res.pay_bank.id,
                'user_id': res.source_model.user_id.id,
                'employee_id': res.source_model.employee_id.id,
                'partner_id': res.partner_id,
                'partner_bank_number': res.partner_bank_number,
                'partner_number': res.partner_number,
                'pay_money': res.pay_money,
                'new_partner_id': res.partner_id,
                'new_partner_bank_number': res.partner_bank_number,
                'new_partner_number': res.partner_number,
                'new_pay_bank': res.pay_bank.id,
                'payment_id': res.id,
            })
            res.write({'alter_id': alter_p.id, 'alter_state': '1'})
            self._cr.execute(
                """UPDATE oa_interface_payment_alter SET create_uid = {} WHERE id = {}""".format(
                    res.source_model.user_id.id, alter_p.id))
            # 发送消息至经办人
            payment_mail = self.env.ref('oa_interface_bank.payment_mail_message')
            self.env['mail.message'].sudo().create({
                'subject': 'oa.interface.payment.alter',
                'model': 'oa.interface.payment.alter',
                'res_id': alter_p.id,
                'record_name': u'付款变更单',
                'body': u'<p>你的付款申请存在基础信息不准确，需要你重新修改并进行审批！请立即查看处理</p>',
                'partner_ids': [(6, 0, [res.source_model.user_id.partner_id.id])],
                'channel_ids': [(6, 0, [payment_mail.id])],
                'message_type': 'notification',
                'author_id': self.env.user.partner_id.id
            })

    @api.multi
    def new_submit_payment_to_erp(self):
        for res in self:
            if res.sudo().alter_id:
                if not res.sudo().alter_id.state == '03':
                    raise UserError(u"请注意: 本单据生成的变更单暂未审批通过, 请等待审批结束！")
                res.sudo().write({
                    'state': '10',
                    'partner_id': res.sudo().alter_id.new_partner_id,
                    'partner_bank_number': res.sudo().alter_id.new_partner_bank_number,
                    'partner_number': res.sudo().alter_id.new_partner_number,
                    'pay_bank': res.sudo().alter_id.new_pay_bank.id,
                })
            else:
                res.sudo().write({
                    'state': '10'
                })

    @api.multi
    def not_payment(self):
        """
        修改状态为无需支付
        :return:
        """
        for res in self:
            res.sudo().write({'state': '04'})


class AlterPaymentInfo(models.Model):
    _description = u"付款变更单"
    _name = 'oa.interface.payment.alter'
    _rec_name = 'name'
    _inherit = ['mail.thread']

    @api.model
    def select_objects(self):
        model_ids = self.env["ir.model"].sudo().search([
            ('model', 'in', ['oa.financial.daily', 'oa.financial.other.daily',
                             'oa.financial.fixed.assets', 'oa.financial.meet.training', 'oa.financial.travel',
                             'oa.financial.entertain', 'oa.financial.vehicle.reimb', 'oa.financial.transport',
                             'oa.financial.info.sys', 'oa.financial.car.maintain', 'oa.financial.car.out',
                             'oa.financial.taxation', 'oa.financial.borrowing', 'oa.financial.refund.bank',
                             'oa.financial.fund.account', 'oa.financial.intermediary', 'oa.financial.approval',
                             'oa.financial.payment.approval'])
        ])
        return [(model.model, model.name) for model in model_ids]

    source_model = fields.Reference(selection=select_objects, string=u'原单据')
    name = fields.Char(cstring=u"主题")
    company_id = fields.Many2one(comodel_name='res.company', string=u'公司')
    source_number = fields.Char(string=u"单据编号")
    pay_bank = fields.Many2one(comodel_name='oa.financial.bank.number', string=u"开户行")
    employee_id = fields.Many2one(comodel_name='hr.employee', string=u'报销人')
    user_id = fields.Many2one(comodel_name='res.users', string=u'经办人')
    partner_id = fields.Char(string=u"收款户名")
    partner_bank_number = fields.Char(string=u"收款账号")
    partner_number = fields.Char(string=u"客户编号")
    pay_money = fields.Float(string=u"支付金额", digits=(12, 2))

    # 变更字段
    new_partner_id = fields.Char(string=u"收款户名", required=True)
    new_partner_bank_number = fields.Char(string=u"收款账号", required=True)
    new_partner_number = fields.Char(string=u"客户编号")
    new_pay_bank = fields.Many2one(comodel_name='oa.financial.bank.number', string=u"开户行", required=True)
    payment_id = fields.Many2one(comodel_name='oa.interface.bank', string=u"付款单")
    PAYMENTSTATE = [
        ('00', u'草稿'),
        ('02', u'审批中'),
        ('03', u'已审批')
    ]
    state = fields.Selection(string=u'单据状态', selection=PAYMENTSTATE, default=u'00')
    SUBMITBUTTON = [
        ('00', u'未生成'),
        ('01', u'已生成预制凭证'),
        ('02', u'已生成正式凭证'),
        ('03', u'凭证已过账'),
    ]
    move_state = fields.Selection(string=u'凭证状态', selection=SUBMITBUTTON, default=u'00', copy=False)

    @api.multi
    def update_state2(self):
        """修改审批状态为审批中，用于锁定表单字段"""
        for res in self:
            self._cr.execute(
                """UPDATE oa_interface_payment_alter SET state = '02' WHERE id = {}""".format(res.id))

    @api.multi
    def update_state3(self):
        """修改审批状态为审批完成"""
        for res in self:
            self._cr.execute(
                """UPDATE oa_interface_payment_alter SET state = '03' WHERE id = {}""".format(res.id))
            if res.payment_id:
                msg = u"提示: 变更付款单已审批通过!{}".format(datetime.datetime.now())
                res.payment_id.sudo().message_post(body=msg, message_type='notification')

    @api.multi
    def update_state1(self):
        """修改审批状态为草稿"""
        for res in self:
            self._cr.execute(
                """UPDATE oa_interface_payment_alter SET state = '00' WHERE id = {}""".format(res.id))


class SearchPaymentState(models.TransientModel):
    _name = 'oa.interface.search.payment.state'
    _description = u"查询付款单据付款在erp系统中的状态"

    @api.model
    def search_payment_state(self):
        payments = self.env['oa.interface.bank'].sudo().search([('state', 'in', ['00', '01', 'approval'])])
        system_name = self.env['ir.values'].get_default('oa.financial.base.config', 'system_name')
        system_code = self.env['ir.values'].get_default('oa.financial.base.config', 'system_code')
        search_state_url = self.env['ir.values'].get_default('oa.financial.base.config', 'search_state_url')
        out_time = self.env['ir.values'].get_default('oa.financial.base.config', 'out_time')
        if not system_code or not system_name or not search_state_url:
            return False
        data_head = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        payment_list = list()
        for payment in payments:
            payment_list.append({
                'form_number': payment.source_number,
                'form_model': payment.source_model._name
            })
        search_data = {
            'system_name': system_name,
            'system_code': system_code,
            'payment': payment_list
        }
        logging.info(search_data)
        # 发送数据至ERP系统
        try:
            logging.info(search_data)
            headers = {'Content-Type': 'application/json'}
            result = requests.post(url=search_state_url, headers=headers, data=json.dumps(search_data),
                                   timeout=out_time)
            result = json.loads(result.text)
            result = json.loads(result.get('result'))
            logging.info(u">>>查询结果消息:{}".format(result.get('message')))
            for res in result.get('results'):
                logging.info(res)
                if res.get('payment_state') != 'F001':
                    oa_panyment = self.env['oa.interface.bank'].sudo().search(
                        [('source_number', '=', res.get('form_number')),
                         ('source_model_name', '=', res.get('form_model'))])
                    if res.get('payment_state') != oa_panyment.state:
                        oa_panyment.sudo().write({'state': res.get('payment_state')})
        except requests.exceptions.Timeout:
            logging.info(u'>>>查询数据超时: 当前等待时间为{}秒！'.format(out_time))
        except KeyError as e:
            logging.info(u">>>KeyError异常错误：{}".format(e.message))
        except Exception as e:
            logging.info(u'>>>查询失败！原因:{}'.format(e.message))


class CreatePaymentS(models.TransientModel):
    _description = u"付款单批量操作功能模型"
    _name = 'oa.interface.payments'

    @api.multi
    def create_payments(self):
        """批量生成付款单"""
        logging.info(u"批量生成付款单")
        configs = self.env['oa.interface.bank.config'].sudo().search([('state', '=', 'y')])
        for config in configs:
            # 获取每个模型
            models = self.env[config.model_id.model].search([('submit_state', '=', '03'), ('bank_pay_type', '=', '00')])
            for model in models:
                # 公司
                company = self.get_model_value(config.company.name, model._name, model.id)
                # 收款户名
                pay_name_id = self.get_model_value(config.pay_name.name, model._name, model.id)
                # 收款账号
                bank_number = self.get_model_value(config.pay_number.name, model._name, model.id)
                # 收款银行
                bank = self.get_model_value(config.pay_bank.name, model._name, model.id)
                self.env['oa.interface.bank'].sudo().create({
                    'source_model': "{},{}".format(model._name, model.id),
                    'name': self.get_model_value(config.form_name.name, model._name, model.id),
                    'company_id': company[0] if company else False,
                    'source_number': self.get_model_value(config.form_number.name, model._name, model.id),
                    'partner_id': pay_name_id[1] if pay_name_id else False,
                    'partner_bank_number': bank_number if bank_number else False,
                    'partner_number': self.get_model_value(config.customer_code.name, model._name, model.id),
                    'pay_bank': bank[0] if bank else False,
                    'pay_summary': self.get_model_value(config.summary.name, model._name, model.id),
                    'pay_money': self.get_model_value(config.money.name, model._name, model.id),
                })
        # 跳转到汇总tree
        action = self.env.ref('oa_interface_bank.oa_interface_bank_action')
        action_dict = action.read()[0]
        return action_dict

    @api.model
    def get_model_value(self, fie, model_name, model_id):
        if fie:
            new_model = self.env[model_name].search_read([('id', '=', model_id)], [fie])
            for model in new_model:
                return model[fie]

    @api.multi
    def up_payment_to_erp(self):
        u"""批量上传付款请求"""
        system_name = self.env['ir.values'].get_default('oa.financial.base.config', 'system_name')
        system_code = self.env['ir.values'].get_default('oa.financial.base.config', 'system_code')
        bank_erp_url = self.env['ir.values'].get_default('oa.financial.base.config', 'bank_erp_url')
        out_time = self.env['ir.values'].get_default('oa.financial.base.config', 'out_time')
        if not system_code or not system_name or not bank_erp_url:
            raise UserError(u"请先配置ERP相关接口信息！外部接口配置项!")
        for bank in self._context.get('active_ids'):
            res = self.env['oa.interface.bank'].browse(bank)
            # 封装请求数据
            pay_data = {
                "system_name": system_name,
                "system_code": system_code,
                "create_date": res.create_date[:10],
                "create_time": "00:00:00",
                "payments": {
                    "source_number": res.source_number if res.source_number else '',
                    "source_model": res.source_model._name,
                    "company_code": res.company_id.code if res.company_id else '0',
                    "public_signs": res.public_signs,
                    "payment_model": res.payment_model,
                    "cross_row_identi": res.cross_row_identi,
                    "off_site_identi": res.off_site_identi,
                    "payee_identi": res.payee_identi,
                    "debit_identi": res.debit_identi,
                    "payee_bank": res.pay_bank.bank_name.address.replace(' ', '') if res.pay_bank.bank_name else '',
                    "payee_bank_code": res.pay_bank.bank_name.code.replace(' ', '') if res.pay_bank.bank_name else '',
                    "payee_opening_bank": res.pay_bank.bank_id.replace(' ', '') if res.pay_bank.bank_id else '',
                    "payee_opening_bank_code": res.pay_bank.bank_code.replace(' ', '') if res.pay_bank.bank_id else '',
                    "payee_opening_province": res.pay_bank.name_provincial.name.replace(' ',
                                                                                        '') if res.pay_bank.name_provincial else '',
                    "payee_opening_province_code": res.pay_bank.name_provincial.provincial_id.replace(' ',
                                                                                                      '') if res.pay_bank.name_provincial else '',
                    "abc_provincial_code": res.pay_bank.name_provincial.abc_provincial_code.replace(' ',
                                                                                                    '') if res.pay_bank.name_provincial else '',
                    "payee_opening_city": res.pay_bank.name_area.name if res.pay_bank.name_area.replace(' ',
                                                                                                        '') else '',
                    "payee_opening_city_code": res.pay_bank.name_area.provincial_id.replace(' ',
                                                                                            '') if res.pay_bank.name_area else '',
                    "abc_city_code": res.pay_bank.name_area.abc_provincial_code.replace(' ',
                                                                                        '') if res.pay_bank.name_area else '',
                    "currency_type": res.currency_type if res.currency_type else 'CNY',
                    "partner_id": res.partner_id if res.partner_id.replace(' ', '') else '',
                    "partner_bank_number": res.partner_bank_number.replace(' ', '') if res.partner_bank_number else '',
                    "partner_number": res.partner_number if res.partner_number else '0000001',
                    "partner_contact": res.partner_contact if res.partner_contact else '',
                    "partner_contact_phone": res.partner_contact_phone if res.partner_contact_phone else '',
                    "partner_contact_add": res.partner_contact_add if res.partner_contact_add else '',
                    "pay_money": res.pay_money,
                    "pay_summary": res.pay_summary if res.pay_summary else '',
                    "pay_use": "",
                },
            }
            # 发送数据至ERP系统
            try:
                logging.info(pay_data)
                headers = {'Content-Type': 'application/json'}
                result = requests.post(url=bank_erp_url, headers=headers, data=json.dumps(pay_data),
                                       timeout=out_time)
            except TypeError as e:
                raise UserError(u"TypeError异常错误,可能原因是上传付款地址不正确！返回信息：{}".format(e.message))
            except requests.exceptions.Timeout:
                raise UserError(u'上传付款单超时: 当前等待时间为{}秒！'.format(out_time))
            except Exception as e:
                raise UserError(u'上传失败: 失败原因：'.format(e.message))
            try:
                result = json.loads(result.text)
                result = json.loads(result.get('result'))
                logging.info("result:{}".format(result))
                if result.get('state') == '0000':
                    res.sudo().write({'state': '00'})
                    res.sudo().message_post(body=result['message'], message_type='notification')
                else:
                    res.message_post(body=u"上传失败,错误详情：{}".format(result.get('message')), message_type='notification')
            except KeyError as e:
                res.sudo().message_post(body=u"KeyError异常错误：{}".format(e.message), message_type='notification')
            except TypeError as e:
                res.sudo().message_post(body=u"TypeError财务系统返回了错误信息！返回信息：{}".format(e.message),
                                        message_type='notification')
