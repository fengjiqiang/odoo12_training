# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Subject(models.Model):
    _name = 'academy.subject'
    _description = "科目"

    name = fields.Char(string='名称')
    # partner_id = fields.Many2one('academy.partner', string='负责人', ondelete='set null')
    partner_id = fields.Many2one('res.partner', string='负责人', ondelete='set null')
    lesson_ids = fields.One2many('academy.lesson', 'subject_id', string='学科')
    desc = fields.Text(string='描述')
