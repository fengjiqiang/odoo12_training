# -*- coding: utf-8 -*-
from decimal import Decimal

from odoo import models, fields, api
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


class UpPaymentLine(models.Model):
    _name = 'oa.interface.bank.line'
    _description = u"付款提交记录"

    payment_id = fields.Many2one('oa.interface.bank', string=u"待付款单")
    pay_per_money = fields.Float(string=u"支付金额")
    state = fields.Selection(
        [('submitted', u'已提交'), ('unsubmitted', u'未提交'),
         ('done', u'已过审'), ('undone', u'未过审'),
         ('paied', u'已支付')],
        string=u'提交状态', default=u'unsubmitted')
    pay_per_money_char = fields.Char(string=u"支付金额")

    @api.onchange('pay_per_money')
    def float2char(self):
        for line in self:
            line.pay_per_money_char = str(Decimal(line.pay_per_money).quantize(Decimal('0.00')))
