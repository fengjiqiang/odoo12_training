# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Task(models.Model):
    _name = 'volunteer.task'
    _description = '任务模板'

    name = fields.Char(string="名称")
    # type = fields.Selection([('recurring', '周期性任务'), ('one-shot', '临时性任务')], string='类型')
    day_number = fields.Integer(string="星期", required=True)
    start_time = fields.Datetime(string='开始时间')
    end_time = fields.Datetime(string='结束时间')
    continue_time = fields.Char(string='时长', compute='_compute_time', store=True)
    state = fields.Selection([('done', '完工'), ('undone', '未完工')], string='状态', default='undone')
    active = fields.Boolean(string='有效', default=True)
    area = fields.Char(string="区域")
    person_ids = fields.Many2many('volunteer.person', string="志愿者")
    plan_id = fields.Many2one('volunteer.plan', string="计划")
    type = fields.Selection(related='plan_id.type', string="类型")
    is_floating = fields.Boolean(string="浮动", default=False)

    # is_floating = fields.Selection([(1, '浮动'), (2, '非浮动')], string="浮动")

    @api.depends('start_time', 'end_time')  # 后端改变 self是新值
    def _compute_time(self):
        for task in self:
            if task.start_time and task.end_time:
                task.continue_time = str(task.end_time - task.start_time)

    @api.multi
    def task_state_done(self):
        for task in self:
            if task.state == 'undone':
                task.write({'state': 'done'})
                task.write({'active': False})

    @api.multi
    def task_state_undone(self):
        for task in self:
            if task.state == 'done':
                task.write({'state': 'undone'})
                task.write({'active': True})

    @api.onchange('plan_id')
    def _type_constraint(self):
        for task in self:
            if not task.plan_id.type == 'recurring':
                # print(111111)
                task.type = 'one-shot'
                # task.write({'type': 'one-shot'})

    @api.constrains('day_number')
    # @api.onchange('day_number')  # type字段 readonly失效
    def _check_day_number(self):
        for task in self:
            if task.day_number not in range(1, 8):
                # print(3333333)
                raise ValidationError("星期字段输入数字1~7")
