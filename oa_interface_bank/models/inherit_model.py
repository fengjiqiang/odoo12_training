# -*- coding: utf-8 -*-
from odoo import models, fields
import logging
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

_logger = logging.getLogger(__name__)

PAYMENTSTATE = [
    ('00', u'待生成付款单'),
    ('01', u'已生成付款单'),
    ('02', u'已发送'),
    ('03', u'已支付'),
    ('04', u'支付失败')
]


class InheritFinancialPaymentApproval(models.Model):
    _inherit = 'oa.financial.payment.approval'
    u"""预付款审批"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialApproval(models.Model):
    _inherit = 'oa.financial.approval'
    u"""转款款项申请审批"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialIntermediary(models.Model):
    _inherit = 'oa.financial.intermediary'
    u"""中介机构款项审批"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialFundAccount(models.Model):
    _inherit = 'oa.financial.fund.account'
    u"""资金账户管理"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialRefundbANK(models.Model):
    _inherit = 'oa.financial.refund.bank'
    u"""归还银行借款审批"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialBorrowing(models.Model):
    _inherit = 'oa.financial.borrowing'
    u"""员工借款审批"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialTaxation(models.Model):
    _inherit = 'oa.financial.taxation'
    u"""缴纳税款审批"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialCatOut(models.Model):
    _inherit = 'oa.financial.car.out'
    u"""出车费用费用报销"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialCatMaintain(models.Model):
    _inherit = 'oa.financial.car.maintain'
    u"""车辆维修保养费用报销"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialInfoSys(models.Model):
    _inherit = 'oa.financial.info.sys'
    u"""信息系统购买和租赁"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialTransport(models.Model):
    _inherit = 'oa.financial.transport'
    u"""外部运输仓储劳务租赁"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialEntertain(models.Model):
    _inherit = 'oa.financial.entertain'
    u"""招待费用报销审批"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialTravel(models.Model):
    _inherit = 'oa.financial.travel'
    u"""差旅费用报销审批"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialMeetTraining(models.Model):
    _inherit = 'oa.financial.meet.training'
    u"""会议及培训报销审批"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialDaily(models.Model):
    _inherit = 'oa.financial.daily'
    u"""日常费用报销申请"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialOtherDaily(models.Model):
    _inherit = 'oa.financial.other.daily'
    u"""其它日常费用报销"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')


class InheritFinancialFixedAssets(models.Model):
    _inherit = 'oa.financial.fixed.assets'
    u"""固定资产采购报销"""

    bank_pay_type = fields.Selection(string=u'支付状态', selection=PAYMENTSTATE, default=u'00')
