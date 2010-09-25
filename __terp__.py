# -*- encoding: utf-8 -*-
##############################################################################
#
#    Crm_intervention module for OpenERP, for managing intervention in the CRM
#    Copyright (C) 2009 SYLEAM (<http://www.Syleam.fr>) Sebastien LANGE
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Customer Relationship Management',
    'version': '1.0',
    'category': 'Generic Modules/CRM & SRM',
    'description': """
    Managing intervention with crm case
""",
    'author': 'Syleam',
    'website': 'http://www.Syleam.fr',
    'depends': ['crm','crm_api'],
    'init_xml': [
        'data/crm_intervention_data.xml',
        'view/crm_intervention_view.xml',
        'view/crm_intervention_menu.xml',
        'view/crm_intervention_sequence.xml',
    ],
    'update_xml': [],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'license': 'GPL-3',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
