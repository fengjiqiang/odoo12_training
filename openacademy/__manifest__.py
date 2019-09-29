# -*- coding: utf-8 -*-
{
    'name':        "课程管理",

    'summary':
                   """
                   Openacademy""",

    'description': """
        管理科目，课程, 老师，学生 ...
    """,

    'author':      "Odoo",
    'website':     "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category':    'OpenAcademy',
    'version':     '0.3',

    # any module necessary for this one to work correctly
    'depends':     ['base'],

    # always loaded
    'data':        [
        "security/ir.model.access.csv",
        "views/course_views.xml",
        "views/session_views.xml",
        "views/menu_views.xml",
        "data/openacademy_data.xml",
    ],
    # only loaded in demonstration mode
    'demo':        [],
}
