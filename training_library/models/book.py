# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Book(models.Model):
	_name = 'training.book'
	_description = "书籍"

	name = fields.Char(string="书籍")
	author = fields.Char(string='作者')
	editor = fields.Char(string='编辑')
	year = fields.Char(string='出版年份')
	ISBN = fields.Char(string='ISBN号')
	book_copy_ids = fields.One2many('training.book.copy', 'book_id', string="副本")
