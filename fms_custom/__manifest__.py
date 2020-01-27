# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Freight Management System Custom',
    'version': '12.0.0.1.0',
    'category': 'Transport',
    'license': 'AGPL-3',
    'author': 'Jesus Ramiro (Bilbonet.NET)',
    'website': 'https://www.bilbonet.net',
    'depends': [
        'account',
        'fms',
    ],
    'data': [
        'report/layout_templates.xml',
        'report/account_invoice_report.xml',
        'data/invoice_mail_template_data.xml',
    ],
    'installable': True,
}
