# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Volunteer(models.Model):
    _name = 'volunteer.person'
    _description = '志愿者'

    name = fields.Char(string="名字")
    address = fields.Char(string="地址")
    email = fields.Char(string="Email", widget='email')
    phone = fields.Char(string="联系方式", widget='phone')
    language = fields.Char(string="语言")
    type = fields.Selection([('term', '长期'), ('noterm', '临时')], string='类型')
    task_person_ids = fields.Many2many('volunteer.task', string="任务")