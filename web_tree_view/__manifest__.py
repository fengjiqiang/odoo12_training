# -*- coding: utf-8 -*-
{
    'name': "ZTree View",
    'summary': "tree view",
    'description':
        """
            tree view depends on ZTree
        """,
    'version': '12.2.0',
    'depends': ['base', 'web'],
    'auth': 'wangjuan04@inspur.com',
    'qweb': [
        "static/src/xml/treeview.xml",
    ],
    'data': [
        'views/template.xml',
    ],
    'auto_install': True
}
