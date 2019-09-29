# -*- coding: utf-8 -*-, api
from odoo import fields, models


class Partner(models.Model):
    _name = 'openacademy.partner'
    _description = '伙伴'

    name = fields.Char(string='名称')

    instructor = fields.Boolean(default=False)
    session_ids = fields.Many2many('openacademy.session', string="参与的课程", readonly=True)
