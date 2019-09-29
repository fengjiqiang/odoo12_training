# -*- coding: utf-8 -*-
{
    'name': "志愿者任务",
    'summary': "volunteer",
    'description': "志愿者任务",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base'],
    # 菜单放在最后面
    'data': [
        'security/ir.model.access.csv',
        'views/task_views.xml',
        'views/person_views.xml',
        'views/plan_views.xml',
        'views/volunteer_menu_views.xml',
    ],
    'qweb': [],
    'js': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}