# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


class Lesson(models.Model):
    _name = 'academy.lesson'
    _description = '学科'

    name = fields.Char(string='学科')
    subject_id = fields.Many2one('academy.subject', string='科目')
    partner_id = fields.Many2one(related='subject_id.partner_id')
    level = fields.Selection([(1, '困难'), (2, '中等'), (3, '容易')], string='难度等级')
    session_ids = fields.One2many('academy.session', 'lesson_id', string='课程')
    state = fields.Selection([
        ('draft', '草稿'),
        ('confirm', '确认'),
    ], string='状态', readonly=True, copy=False, index=True, default='draft')

    @api.multi
    def action_confirm(self):
        return self.write({'state': 'confirm'})

    @api.multi
    def action_draft(self):
        return self.write({'state': 'draft'})
