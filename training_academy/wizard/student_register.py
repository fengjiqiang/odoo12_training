# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StudentRegiester(models.TransientModel):
    _name = 'academy.student.regiester'
    _description = "学生注册向导"

    # def _default_session(self):
    #     return self.env['academy.session'].browse(self._context.get('active_id'))

    student_ids = fields.Many2many('res.partner', string="学生")

    @api.multi
    def subscribe(self):
        session_id = self.env['academy.session'].browse(self._context.get('active_id'))
        for wizard in self:
            for session in session_id:
                session.write({
                    'student_ids': [(4, id) for id in wizard.student_ids.ids]
                })
        # self.session_id.student_ids |= self.student_ids
        return {'type': 'ir.actions.act_window_close'}
