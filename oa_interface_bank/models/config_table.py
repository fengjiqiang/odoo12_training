# -*- coding: utf-8 -*-
from odoo import models, api, fields
import logging
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

_logger = logging.getLogger(__name__)


class PaymentConfig(models.Model):
    _name = 'oa.interface.bank.config'
    _rec_name = 'name'
    _description = u"配置付款单模板"

    name = fields.Char(string=u'模板名称', required=True)
    model_id = fields.Many2one(comodel_name='ir.model', string=u'付款模型', required=True)
    form_number = fields.Many2one(comodel_name='ir.model.fields', string=u'单据编号', required=True)
    form_name = fields.Many2one(comodel_name='ir.model.fields', string=u'主题(名称)', required=True)
    company = fields.Many2one(comodel_name='ir.model.fields', string=u'公司', required=True)
    pay_name = fields.Many2one(comodel_name='ir.model.fields', string=u'收款户名(many2One)')
    pay_number = fields.Many2one(comodel_name='ir.model.fields', string=u'收款账号')
    customer_code = fields.Many2one(comodel_name='ir.model.fields', string=u'客户编号')
    contact_name = fields.Many2one(comodel_name='ir.model.fields', string=u'收款联系人')
    contact_tel = fields.Many2one(comodel_name='ir.model.fields', string=u'联系人电话')
    contact_add = fields.Many2one(comodel_name='ir.model.fields', string=u'联系人地址')
    money = fields.Many2one(comodel_name='ir.model.fields', string=u'支付金额')
    summary = fields.Many2one(comodel_name='ir.model.fields', string=u'摘要')
    use = fields.Many2one(comodel_name='ir.model.fields', string=u'付款用途')
    pay_bank = fields.Many2one(comodel_name='ir.model.fields', string=u'开户行信息')
    state = fields.Selection(string=u'是否启用', selection=[('y', u'启用'), ('n', u'停用'), ], default='y')

    @api.onchange('model_id')
    def _onchange_model_id(self):
        if self.model_id:
            model_id = self.model_id.id
            return {'domain': {
                'form_number': [('model_id', '=', model_id)],
                'form_name': [('model_id', '=', model_id)],
                'company': [('model_id', '=', model_id)],
                'pay_name': [('model_id', '=', model_id)],
                'pay_number': [('model_id', '=', model_id)],
                'customer_code': [('model_id', '=', model_id)],
                'contact_name': [('model_id', '=', model_id)],
                'contact_tel': [('model_id', '=', model_id)],
                'contact_add': [('model_id', '=', model_id)],
                'money': [('model_id', '=', model_id)],
                'summary': [('model_id', '=', model_id)],
                'use': [('model_id', '=', model_id)],
                'pay_bank': [('model_id', '=', model_id)]
            }}


class UpAccountMoveList(models.Model):
    _description = u"上传凭证模型列表"
    _name = 'oa.interface.account.move.list'

    name = fields.Char(string=u'模型名称')
    model_id = fields.Many2one(comodel_name='ir.model', string=u'模型', required=True)
    state = fields.Selection(string=u'是否有效', selection=[('y', u'是'), ('n', u'否'), ], default='y')
    
    @api.constrains('model_id')
    def constrains_model_id(self):
        if not self.name:
            self.name = self.model_id.name

    @api.onchange('model_id')
    def onchange_model(self):
        if self.model_id:
            self.name = self.model_id.name
