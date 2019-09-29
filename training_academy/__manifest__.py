# -*- coding: utf-8 -*-
{
    'name': "课程管理",
    'summary': "academy",
    'description': "课程管理",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base'],
    # 菜单放在最后面
    'data': [
        'security/ir.model.access.csv',
        'wizard/student_register_views.xml',
        'views/partner_views.xml',
        'views/subject_views.xml',
        'views/session_views.xml',
        'views/lesson_views.xml',
        'views/academy_menu_views.xml',
    ],
    'qweb': [],
    'js': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}