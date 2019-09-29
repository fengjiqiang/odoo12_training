# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Partner(models.Model):
    # _name = 'academy.partner'
    _inherit = 'res.partner'

    # name = fields.Char(string='名字')
    op_type = fields.Selection([(1, '老师'), (2, '学生'), (3, '负责人')], string='类型')
    instructor = fields.Boolean(string="讲师")
    subject_ids = fields.One2many('academy.subject', 'partner_id', string="科目")
    tea_session_ids = fields.One2many('academy.session', 'teacher_id', string="教授课程")
    stu_session_ids = fields.Many2many('academy.session', string="参加课程")
