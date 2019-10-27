# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Freight Management System',
    'version': '12.0.1.0.0',
    'category': 'Transport',
    'license': 'AGPL-3',
    'author': 'Jesus Ramiro (Bilbonet.NET)',
    'website': 'https://www.bilbonet.net',
    'depends': [
        'mail',
        'base_address_city',
        'contacts',
        'hr',
        'product',
        'mail_activity_board',
    ],
    'data': [
        'security/fms_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/fms_freight_email_template.xml',
        'views/fms_views.xml',
        'views/product_template_view.xml',
        'report/fms_freight_report.xml',
    ],
    'installable': True,
}
