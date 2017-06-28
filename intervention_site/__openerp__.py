# -*- coding: utf-8 -*-
##############################################################################
#
#    intervention_site module for OpenERP, Managing intervention in CRM
#    Copyright (C) 2017 Christophe CHAUVET <christophe.chauvet@gmail.com>
#
#    This file is a part of intervention_site
#
#    intervention_site is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    intervention_site is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Intervention Site, Equipment',
    'version': '0.2',
    'category': 'Generic Modules/CRM & SRM',
    'description': """Intervention Site & Equipment""",
    'author': 'Mirounga',
    'website': 'http://www.mirounga.fr/',
    'depends': [
        'crm',
        'account',
        'stock',
        'crm_intervention',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/intervention_site.xml',
        'views/intervention_equipment.xml',
        'views/intervention.xml',
        'wizard/generate_intervention_view.xml',
    ],
    'demo': [
        'demo/site.xml',
        'demo/equipment.xml',
    ],
    'test': [
        'test/site.yml',
        'test/equipment.yml',
        'test/equipment_history.yml',
        'test/intervention.yml',
        'test/intervention_discount.yml',
    ],
    'installable': True,
    'active': False,
    'license': 'AGPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
