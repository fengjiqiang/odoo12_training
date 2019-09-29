# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import exceptions


class CustomerRent(models.TransientModel):
    _name = 'training.customer.rent'
    _description = "客户借阅向导"

    customer_rent_ids = fields.Many2many('book.rent.return', string="借阅")

    # @api.onchange('customer_rent_ids')
    # def _default_book_rented(self):
    #     # return {'domain': {
    #     #     'customer_rent_ids': [('book_rented', '=', False)]
    #     # }}
    #     pass

    @api.multi
    def confirm_rent(self):
        self.ensure_one()
        customer_id = self.env['training.customer'].browse(self._context.get('active_id'))
        for wizard in self:
            for customer in customer_id:
                customer.write({
                    'customer_rent_ids': [(4, id) for id in wizard.customer_rent_ids.ids]
                })
        # book_rent = self.env['training.book.copy'].search([('id', '=', self.customer_rent_ids.copy_id.id)])
        # if book_rent:
        #     book_rent.write({'book_rented': True})
        book_state = self.env['book.rent.return'].search([('id', '=', self.customer_rent_ids.id)])
        if book_state:
            book_state.write({'state': 'confirm'})
            book_state.write({'book_rented': True})
        return {'type': 'ir.actions.act_window_close'}
