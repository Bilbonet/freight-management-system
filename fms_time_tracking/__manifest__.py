# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Freight Expeditions Time Tracking',
    'version': '12.0.1.0.0',
    'category': 'Transport',
    'license': 'AGPL-3',
    'author': 'Jesus Ramiro (Bilbonet.NET)',
    'website': 'https://www.bilbonet.net',
    'depends': ['fms',],
    'external_dependencies': {
        'python': [
            'httpagentparser',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_view.xml',
        'views/templates.xml',
        'views/fms_views.xml',
        'views/fms_time_tracking_views.xml',
    ],
    'installable': True,
}
