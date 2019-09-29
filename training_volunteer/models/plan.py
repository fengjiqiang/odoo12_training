# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Plan(models.Model):
    _name = 'volunteer.plan'
    _description = '计划模板'

    name = fields.Char(string="名称")
    # type = fields.Char(string='类型')
    type = fields.Selection([('recurring', '长期'), ('one-shot', '临时')], string='类型')
    task_plan_ids = fields.One2many('volunteer.task', 'plan_id', string="任务")