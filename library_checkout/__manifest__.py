{
    'name': 'Library Book Borrowing',
    'description': 'Members can borrow books from the library.',
    'author': 'Ethan',
    'depends': ['library_app', 'mail'],
    'data':[
        'security/ir.model.access.csv',
        'views/library_menu.xml',
        'views/checkout_view.xml',
        'data/library_checkout_stage.xml',
        'wizard/checkout_mass_message_wizard.xml',
        'views/checkout_kanban_view.xml',
        'views/checkout_kanban_assets.xml',
    ],
}
