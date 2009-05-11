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
import datetime

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
        'number_request': fields.char('Number Request', size=64),
        'internal_comment': fields.text('Internal Comment'),
        'internal_note': fields.text('Internal Note'),
        'planned_end_date': fields.datetime('Planned end date'),
        'effective_start_date': fields.datetime('Effective start date'),
        'effective_end_date': fields.datetime('Effective end date'),
        'effective_duration': fields.float('Effective duration', help='Indicate real time to do the intervention.'),
        'history_line': fields.one2many('crm.case.history', 'case_id', 'Communication', readonly=1),
        'internal_history': fields.one2many('crm.case.history', 'case_id', 'Communication', readonly=1),
        'partner_id':fields.many2one('res.partner', 'Customer', change_default=True, select=True),
        'partner_invoice_id':fields.many2one('res.partner.address', 'Invoice Address'),
        'partner_order_id':fields.many2one('res.partner.address', 'Intervention Contact', help="The name and address of the contact that requested the intervention."),
        'partner_shipping_id':fields.many2one('res.partner.address', 'Intervention Address'),
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

    def onchange_planned_duration(self, cr, uid, ids, planned_duration, planned_start_date):
        if not planned_duration:
            return {'value':{'planned_end_date': False }}
        start_date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(planned_start_date , "%Y-%m-%d %H:%M:%S")))
        return {'value': {'planned_end_date' : (start_date + datetime.timedelta(hours=planned_duration)).strftime('%Y-%m-%d %H:%M:%S')}}

    def onchange_planned_end_date(self, cr, uid, ids, planned_end_date, planned_start_date):
        start_date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(planned_start_date, "%Y-%m-%d %H:%M:%S")))
        end_date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(planned_end_date, "%Y-%m-%d %H:%M:%S")))
        difference = end_date - start_date
        minutes, secondes = divmod(difference.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return {'value' : {'duration' : (float(difference.days*24) + float(hours) + float(minutes)/float(60))}}

    def onchange_effective_duration(self, cr, uid, ids, effective_duration, effective_start_date):
        if not effective_duration:
            return {'value':{'effective_end_date': False }}
        start_date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(effective_start_date , "%Y-%m-%d %H:%M:%S")))
        return {'value': {'effective_end_date' : (start_date + datetime.timedelta(hours=effective_duration)).strftime('%Y-%m-%d %H:%M:00')}}

    def onchange_effective_end_date(self, cr, uid, ids, effective_end_date, effective_start_date):
        start_date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(effective_start_date, "%Y-%m-%d %H:%M:%S")))
        end_date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(effective_end_date, "%Y-%m-%d %H:%M:%S")))
        difference = end_date - start_date
        minutes, secondes = divmod(difference.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return {'value' : {'effective_duration' : (float(difference.days*24) + float(hours) + float(minutes)/float(60))}}

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

