# -*- coding: utf-8 -*-
{
    'name': "OA银企直连模块",
    'summary': """通过本模块将系统中的付款单据传递至财务ERP系统中进行付款操作""",
    'description': """通过本模块将系统中的付款单据传递至财务ERP系统中进行付款操作""",
    'author': "SuXueFeng",
    'version': '1.0',
    'depends': ['base', 'mail', 'oa', 'oa_financial', 'base_coder'],
    'data': [
        'groups/oa_interface_groups.xml',
        'security/ir.model.access.csv',
        'security/up_payment_rule.xml',
        'data/mail_channel.xml',
        'views/menu.xml',
        'views/up_payment.xml',
        'views/config_table.xml',
    ],
}
