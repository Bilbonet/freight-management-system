# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Freight Expeditions Digitized Signature',
    'version': '12.0.1.0.0',
    'category': 'Transport',
    'license': 'AGPL-3',
    'author': 'Jesus Ramiro (Bilbonet.NET)',
    'website': 'https://www.bilbonet.net',
    'depends': [
        'fms',
        'web_widget_digitized_signature',
    ],
    'data': [
        'wizard/fms_digitized_signature_view.xml',
        'views/fms_views.xml',
    ],
    'installable': True,
}
