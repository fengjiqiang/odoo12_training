# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models


class Course(models.Model):
    _name = 'openacademy.course'
    _description = '科目'

    name = fields.Char(string='标题', required=True)
    description = fields.Text(string='描述')

    responsible_id = fields.Many2one('openacademy.partner', ondelete='set null', string="负责人")
    session_ids = fields.One2many('openacademy.session', 'course_id', string="课程")

    level = fields.Selection([(1, '简单'), (2, '中等'), (3, '困难')], string="难度等级")
    session_count = fields.Integer(compute="_compute_session_count")

    @api.depends('session_ids')
    def _compute_session_count(self):
        for course in self:
            course.session_count = len(course.session_ids)


class Session(models.Model):
    _name = 'openacademy.session'
    _description = '课程'

    name = fields.Char(string='课程', required=True)
    description = fields.Html()
    active = fields.Boolean(string='有效', default=True)
    state = fields.Selection([('draft', "草稿"), ('confirmed', "确认"), ('done', "完成")], default='draft')
    level = fields.Selection(related='course_id.level', readonly=True)
    responsible_id = fields.Many2one(related='course_id.responsible_id', readonly=True, store=True)

    start_date = fields.Date(default=fields.Date.context_today, string='开始日期')
    end_date = fields.Date(default=fields.Date.today, string='结束日期')
    duration = fields.Float(digits=(6, 2), string='持续时间（日）', help="持续时间（日）", default=1)

    instructor_id = fields.Many2one('openacademy.partner', string="讲师")
    course_id = fields.Many2one('openacademy.course', ondelete='cascade', string="科目", required=True)
    attendee_ids = fields.Many2many('openacademy.partner', string="出席者")
    attendees_count = fields.Integer(compute='_get_attendees_count', store=True, string='出席人数')
    seats = fields.Integer(string='座位')
    taken_seats = fields.Float(string='入座率', compute='_compute_taken_seats', store=True)

    @api.depends('seats', 'attendee_ids')
    def _compute_taken_seats(self):
        for session in self:
            if not session.seats:
                session.taken_seats = 0.0
            else:
                session.taken_seats = 100.0 * len(session.attendee_ids) / session.seats

    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for session in self:
            session.attendees_count = len(session.attendee_ids)

    @api.onchange('start_date', 'end_date')
    def _compute_duration(self):
        if not (self.start_date and self.end_date):
            return
        if self.end_date < self.start_date:
            return {'warning': {
                'title': "Incorrect date value",
                'message': "End date is earlier then start date",
            }}
        delta = fields.Date.from_string(self.end_date) - fields.Date.from_string(self.start_date)
        self.duration = delta.days + 1
