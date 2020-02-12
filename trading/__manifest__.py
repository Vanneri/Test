# -*- coding: utf-8 -*-
{
    'name': "Trading Module",

    'summary': """
        Introduces diffrent types of trading concepts 
        """,
    'author': "Vanneri",
    'website': "https://github.com/Vanneri/Test/tree/12.0",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Extra Tools',
    'version': '2.0',

    # any module necessary for this one to work correctly
    'depends': ['sale','purchase','account'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/trading.xml',
        'views/sale.xml',
        'views/purchase.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}