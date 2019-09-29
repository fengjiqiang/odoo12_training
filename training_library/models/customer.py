# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Customer(models.Model):
    _name = 'training.customer'
    _description = "客户"

    name = fields.Char(string='名字')
    address = fields.Char(string='地址')
    email = fields.Char(string='Email', widget='phone')
    phone = fields.Char(string='联系方式', widget='email')
    money = fields.Integer(string="欠款金额")
    customer_rent_ids = fields.One2many('book.rent.return', 'customer_id', string="借阅")
