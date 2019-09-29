# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Session(models.Model):
    _name = 'academy.session'
    _description = '课程'

    name = fields.Char(string='课程')
    lesson_id = fields.Many2one('academy.lesson', string='学科', ondelete='cascade')
    subject_id = fields.Many2one('academy.subject', string='科目')
    partner_id = fields.Many2one(related='subject_id.partner_id')
    # teacher_id = fields.Many2one('academy.partner', string='讲师')
    teacher_id = fields.Many2one('res.partner', string='讲师')
    # student_ids = fields.Many2many('academy.partner', string='学生', domain="[('type', '=', '2')]")
    student_ids = fields.Many2many('res.partner', string='学生', domain="[('op_type', '=', '2')]")

    start_time = fields.Datetime(string='开始时间')
    end_time = fields.Datetime(string='结束时间')
    continue_time = fields.Char(string='课程时长')
    seat_num = fields.Integer(string='座位数')
    student_num = fields.Integer(string='学生数')
    taken_seats = fields.Float(string='入座率', compute='_compute_taken_seats', store=True)
    state = fields.Selection([
        ('draft', '草稿'),
        ('confirm', '确认'),
    ], string='状态', readonly=True, copy=False, index=True, default='draft')
    # is_paid = fields.Boolean("支付状态", default=False)

    @api.multi
    def action_confirm(self):
        return self.write({'state': 'confirm'})

    @api.multi
    def action_draft(self):
        return self.write({'state': 'draft'})

    @api.onchange('start_time', 'end_time')  # 前端显示 self是原来的值
    # @api.depends('start_time', 'end_time')  # 后端改变 self是新值
    def _compute_time(self):
        for session in self:
            if not (session.start_time and session.end_time):
                return
            if session.end_time < session.start_time:
                raise ValidationError('结束时间不能小于开始时间')
            session.continue_time = str(session.end_time - session.start_time)

    @api.depends('seat_num', 'student_num')
    def _compute_taken_seats(self):
        for session in self:
            if session.seat_num < session.student_num:
                raise ValidationError("学生数超出教室容量限制")
            else:
                if not session.student_num:
                    session.taken_seats = 0.0
                else:
                    session.taken_seats = 100.0 * session.student_num / session.seat_num

    # @api.constrains('seat_num', 'student_num')
    # def _check_student_num(self):
    #     if self.seat_num < self.student_num:
    #         raise ValidationError("学生数超出教室容量限制")

    # @api.onchange('seat_num', 'student_num')
    # def _check_student_num(self):
    #     if self.seat_num < self.student_num:
    #         raise ValidationError("学生数超出教室容量限制")

    @api.onchange('student_ids')
    def _compute_student_num(self):
        for stu in self:
            stu.student_num = len(stu.student_ids)
            # stu.write({'seat_num': 12})
            # print(stu.student_ids)

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', '课程名称必须唯一')
    ]

    @api.constrains('seat_num')
    def _check_seat_num(self):
        if not self.seat_num > 0:
            raise ValidationError("座位数不能为零和负数")

