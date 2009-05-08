# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2009 SYLEAM
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
#   AIM :
#           ...
#
##############################################################################
# Date      Author      Description
# 20090502  SYLEAM/SL   ...
#
##############################################################################


from osv import fields, osv
from tools.translate import _
import time

class crm_intervention_history(osv.osv):
    _inherit = 'crm.case.history'

    _columns = {
        'types': fields.char('Type', size=12),
    }

crm_intervention_history()

class crm_intervention(osv.osv):
    _inherit = 'crm.case'

    _columns = {
        'customer_request': fields.text('Customer Request'),
        'number_request': fields.char('Number Request', size=64, required=True),
        'internal_comment': fields.text('Internal Comment'),
        'history_line': fields.one2many('crm.case.history', 'case_id', 'Communication', readonly=1),
        'internal_history': fields.one2many('crm.case.history', 'case_id', 'Communication', readonly=1),
        'partner_id':fields.many2one('res.partner', 'Customer', readonly=True, states={'open':[('readonly',False)]}, change_default=True, select=True),
        'partner_invoice_id':fields.many2one('res.partner.address', 'Invoice Address', readonly=True, required=True, states={'open':[('readonly',False)]}),
        'partner_order_id':fields.many2one('res.partner.address', 'Intervention Contact', readonly=True, required=True, states={'open':[('readonly',False)]}, help="The name and address of the contact that requested the intervention."),
        'partner_shipping_id':fields.many2one('res.partner.address', 'Intervention Address', readonly=True, required=True, states={'open':[('readonly',False)]}),
        'partner_phone': fields.char('Phone', size=32),
        'partner_mobile': fields.char('Mobile', size=32),

    }
    _defaults = {
        'partner_invoice_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['invoice'])['invoice'],
        'partner_order_id': lambda self, cr, uid, context: context.get('partner_id', False) and  self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['contact'])['contact'],
        'partner_shipping_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['delivery'])['delivery'],
        'number_request': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'crm_intervention.case'),
    }

    def onchange_partner_intervention_id(self, cr, uid, ids, part):
        if not part:
            return {'value':{'partner_invoice_id': False, 'partner_shipping_id':False, 'partner_order_id':False, 'email_from': False, 'partner_phone':False, 'partner_mobile':False }}
        addr = self.pool.get('res.partner').address_get(cr, uid, [part], ['default','delivery','invoice','contact'])
        part = self.pool.get('res.partner').browse(cr, uid, part)
        val = {'partner_invoice_id': addr['invoice'],
               'partner_order_id':addr['contact'],
               'partner_shipping_id':addr['delivery'],
              }
        val['email_from'] = self.pool.get('res.partner.address').browse(cr, uid, addr['delivery']).email
        val['partner_phone'] = self.pool.get('res.partner.address').browse(cr, uid, addr['delivery']).phone
        val['partner_mobile'] = self.pool.get('res.partner.address').browse(cr, uid, addr['delivery']).mobile
        return {'value':val}

    def case_log(self, cr, uid, ids,context={}, email=False, *args):
        cases = self.browse(cr, uid, ids)
        for case in cases:
            obj = self.pool.get('crm.case.log')
            data = {
                'name': _('Historize'),
                'som': case.som.id,
                'canal_id': case.canal_id.id,
                'user_id': uid,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'case_id': case.id,
                'section_id': case.section_id.id
            }
            obj.create(cr, uid, data, context)

            obj = self.pool.get('crm.case.history')
            data['description'] = case.description
            data['types'] = 'default'
            data['email'] = email or \
                (case.user_id and case.user_id.address_id and \
                case.user_id.address_id.email) or False
            obj.create(cr, uid, data, context)
        return self.write(cr, uid, ids, {'description': False, 'som': False, 'canal_id': False})

    def case_internal_log(self, cr, uid, ids,context={}, email=False, *args):
        cases = self.browse(cr, uid, ids)
        for case in cases:
            obj = self.pool.get('crm.case.log')
            data = {
                'name': _('Historize'),
                'som': case.som.id,
                'canal_id': case.canal_id.id,
                'user_id': uid,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'case_id': case.id,
                'section_id': case.section_id.id
            }
            obj.create(cr, uid, data, context)

            obj = self.pool.get('crm.case.history')
            data['description'] = case.internal_comment
            data['types'] = 'internal'
            data['email'] = email or \
                (case.user_id and case.user_id.address_id and \
                case.user_id.address_id.email) or False
            obj.create(cr, uid, data, context)
        return self.write(cr, uid, ids, {'internal_comment': False, 'som': False, 'canal_id': False})

crm_intervention()

