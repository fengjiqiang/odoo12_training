from odoo import fields, models


class Partner(models.Model):
    _name = 'library.partner'
    _inherit = ['res.partner', 'mail.thread', 'mail.activity.mixin']

    published_book_ids = fields.One2many('library.book', 'publisher_id', string='Published Books')
    # partner_id = fields.Many2one('res.partner')
    op_type = fields.Selection([('partner', '读者'), ('author', '作者'), ('publish', '出版社')], string='类型')
    commercial_partner_id = fields.Many2one('res.partner', compute=False,
                                            string='Commercial Entity', store=True, index=True)
