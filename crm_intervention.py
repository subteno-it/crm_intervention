# -*- coding: utf-8 -*-
##############################################################################
#
#    crm_intervention module for OpenERP, Managing intervention in CRM
#    Copyright (C) 2011 SYLEAM Info Services (<http://www.Syleam.fr/>)
#              Sebastien LANGE <sebastien.lange@syleam.fr>
#              Sylvain GARANCHER <sylvain.garancher@syleam.fr>
#
#    This file is a part of crm_intervention
#
#    crm_intervention is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    crm_intervention is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.addons.base_status.base_state import base_state
from openerp.addons.base_status.base_stage import base_stage
from openerp.addons.crm import crm
from openerp import Model, fields
import time
from datetime import datetime, timedelta
import binascii
import openerp.tools as tools

CRM_INTERVENTION_STATES = (
    ('cancel', 'Cancelled'),
    ('done', 'Held'),
    ('pending', 'Pending'),
)


class crm_intervention(base_state, base_stage, Model):
    _name = 'crm.intervention'
    _description = 'Intervention'
    _order = 'id desc'
    _inherit = ['mail.thread']

    name = fields.Char(size=128, required=True)
    active = fields.Boolean(default=True)
    date_action_last = fields.Datetime(string='Last Action', readonly=True)
    date_action_next = fields.Datetime(string='Next Action', readonly=True)
    description = fields.Text()
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self._get_default_user())
    section_id = fields.Many2one(
        'crm.case.section', string='Interventions Team',
        default=lambda self: self.env.ref('crm_intervention.section_interventions_department'),
        help='Interventions team to which Case belongs to. Define Responsible user and Email account for mail gateway.',
    )
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env['res.company']._company_default_get('crm.helpdesk'))
    date_closed = fields.Datetime(string='Closed', readonly=True)
    email_cc = fields.Text(
        string='Watchers Emails',
        default=lambda self: self.env.ref('crm_intervention.section_interventions_department').reply_to,
        help='These email addresses will be added to the CC field of all inbound and outbound emails for this record before being sent. Separate multiple email addresses with a comma',
    )
    email_from = fields.Char(string='Email', size=128, help='These people will receive email.')
    ref = fields.Reference(crm._links_get, string='Reference', size=128)
    ref2 = fields.Reference(crm._links_get, string='Reference 2', size=128)
    priority = fields.Selection(crm.AVAILABLE_PRIORITIES, default='pending')
    categ_id = fields.Many2one('crm.case.categ', string='Category', domain="[('section_id', '=', section_id), ('object_id.model', '=', 'crm.intervention')]")
    number_request = fields.Char(string='Number Request', size=64, default=lambda self: self.env['ir.sequence'].get('intervention'))
    customer_information = fields.Text(string='Customer_information')
    intervention_todo = fields.Text(string='Intervention to do', help='Indicate the description of this intervention to do')
    date_planned_start = fields.Datetime(string='Planned Start Date', help='Indicate the date of begin intervention planned')
    date_planned_end = fields.Datetime(string='Planned End Date', help='Indicate the date of end intervention planned')
    date_effective_start = fields.Datetime(string='Effective start date', help='Indicate the date of begin intervention')
    date_effective_end = fields.Datetime(string='Effective end date', help='Indicate the date of end intervention')
    duration_planned = fields.Float(string='Planned duration', help='Indicate estimated to do the intervention.')
    duration_effective = fields.Float(string='Effective duration', help='Indicate real time to do the intervention.')
    partner_id = fields.Many2one('res.partner', string='Customer', change_default=True, select=True)
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address', help='The name and address for the invoice')
    partner_order_id = fields.Many2one('res.partner', string='Intervention Contact', help='The name and address of the contact that requested the intervention.')
    partner_shipping_id = fields.Many2one('res.partner', string='Intervention Address')
    partner_address_phone = fields.Char(string='Phone', size=64)
    partner_address_mobile = fields.Char(string='Mobile', size=64)
    state = fields.Selection(
        crm.AVAILABLE_STATES, readonly=True, default='draft',
        help="""The state is set to 'Draft', when a case is created.
        If the case is in progress the state is set to 'Open'.
        When the case is over, the state is set to 'Done'.
        If the case needs to be reviewed then the state is set to 'Pending'.""",
    )
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages', domain=[('model', '=', _name)])

    #_defaults = {
        #'partner_invoice_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['invoice'])['invoice'],
        #'partner_order_id': lambda self, cr, uid, context: context.get('partner_id', False) and  self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['contact'])['contact'],
        #'partner_shipping_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['delivery'])['delivery'],
    #}

    def onchange_partner_intervention_id(self, cr, uid, ids, part):
        if not part:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False, 'partner_order_id': False, 'email_from': False, 'partner_address_phone': False, 'partner_address_mobile': False}}
        addr = self.pool.get('res.partner').address_get(cr, uid, [part], ['default', 'delivery', 'invoice', 'contact'])
        part = self.pool.get('res.partner').browse(cr, uid, part)
        val = {
            'partner_invoice_id': addr['invoice'],
            'partner_order_id': addr['contact'],
            'partner_shipping_id': addr['delivery'],
        }
        val['email_from'] = self.pool.get('res.partner').browse(cr, uid, addr['delivery']).email
        val['partner_address_phone'] = self.pool.get('res.partner').browse(cr, uid, addr['delivery']).phone
        val['partner_address_mobile'] = self.pool.get('res.partner').browse(cr, uid, addr['delivery']).mobile
        return {'value': val}

    def onchange_planned_duration(self, cr, uid, ids, planned_duration, planned_start_date):
        if not planned_duration:
            return {'value': {'date_planned_end': False}}
        start_date = datetime.fromtimestamp(time.mktime(time.strptime(planned_start_date, '%Y-%m-%d %H:%M:%S')))
        return {'value': {'date_planned_end': (start_date + timedelta(hours=planned_duration)).strftime('%Y-%m-%d %H:%M:%S')}}

    def onchange_planned_end_date(self, cr, uid, ids, planned_end_date, planned_start_date):
        start_date = datetime.fromtimestamp(time.mktime(time.strptime(planned_start_date, '%Y-%m-%d %H:%M:%S')))
        end_date = datetime.fromtimestamp(time.mktime(time.strptime(planned_end_date, '%Y-%m-%d %H:%M:%S')))
        difference = end_date - start_date
        minutes, secondes = divmod(difference.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return {'value': {'duration_planned': (float(difference.days * 24) + float(hours) + float(minutes) / float(60))}}

    def onchange_effective_duration(self, cr, uid, ids, effective_duration, effective_start_date):
        if not effective_duration:
            return {'value': {'date_effective_end': False}}
        start_date = datetime.fromtimestamp(time.mktime(time.strptime(effective_start_date, '%Y-%m-%d %H:%M:%S')))
        return {'value': {'date_effective_end': (start_date + timedelta(hours=effective_duration)).strftime('%Y-%m-%d %H:%M:00')}}

    def onchange_effective_end_date(self, cr, uid, ids, effective_end_date, effective_start_date):
        start_date = datetime.fromtimestamp(time.mktime(time.strptime(effective_start_date, '%Y-%m-%d %H:%M:%S')))
        end_date = datetime.fromtimestamp(time.mktime(time.strptime(effective_end_date, '%Y-%m-%d %H:%M:%S')))
        difference = end_date - start_date
        minutes, secondes = divmod(difference.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return {'value': {'duration_effective': (float(difference.days * 24) + float(hours) + float(minutes) / float(60))}}

    def message_new(self, cr, uid, msg, context=None):
        """
        Automatically calls when new email message arrives

        :param self: The object pointer
        :param cr: the current row, from the database cursor,
        :param uid: the current user’s ID for security checks
        """
        mailgate_pool = self.pool.get('email.server.tools')

        subject = msg.get('subject')
        body = msg.get('body')
        msg_from = msg.get('from')
        priority = msg.get('priority')

        vals = {
            'name': subject,
            'email_from': msg_from,
            'email_cc': msg.get('cc'),
            'description': body,
            'user_id': False,
        }
        if msg.get('priority', False):
            vals['priority'] = priority

        res = mailgate_pool.get_partner(cr, uid, msg.get('from') or msg.get_unixfrom())
        if res:
            vals.update(res)

        res = self.create(cr, uid, vals, context)
        attachents = msg.get('attachments', [])
        for attactment in attachents or []:
            # TODO: Add missing context information
            data_attach = {
                'name': attactment,
                'datas': binascii.b2a_base64(str(attachents.get(attactment))),
                'datas_fname': attactment,
                'description': 'Mail attachment',
                'res_model': self._name,
                'res_id': res,
            }
            self.pool.get('ir.attachment').create(cr, uid, data_attach)

        return res

    def message_update(self, cr, uid, ids, vals={}, msg="", default_act='pending', context=None):
        """
        :param self: The object pointer
        :param cr: the current row, from the database cursor,
        :param uid: the current user’s ID for security checks,
        :param ids: List of update mail’s IDs
        """
        if isinstance(ids, (str, int, long)):
            ids = [ids]

        if msg.get('priority') in dict(crm.AVAILABLE_PRIORITIES):
            vals['priority'] = msg.get('priority')

        maps = {
            'cost': 'planned_cost',
            'revenue': 'planned_revenue',
            'probability': 'probability'
        }
        vls = {}
        for line in msg['body'].split('\n'):
            line = line.strip()
            res = tools.misc.command_re.match(line)
            if res and maps.get(res.group(1).lower()):
                key = maps.get(res.group(1).lower())
                vls[key] = res.group(2).lower()
        vals.update(vls)

        # Unfortunately the API is based on lists
        # but we want to update the state based on the
        # previous state, so we have to loop:
        for case in self.browse(cr, uid, ids, context=context):
            values = dict(vals)
            if case.state in CRM_INTERVENTION_STATES:
                values.update(state=crm.AVAILABLE_STATES[1][0])  # re-open
            res = self.write(cr, uid, [case.id], values, context=context)
        return res

    def msg_send(self, cr, uid, id, *args, **argv):

        """ Send The Message
            :param self: The object pointer
            :param cr: the current row, from the database cursor,
            :param uid: the current user’s ID for security checks,
            :param ids: List of email’s IDs
            :param *args: Return Tuple Value
            :param **args: Return Dictionary of Keyword Value
        """
        return True

    def copy(self, cr, uid, id, default=None, context=None):
        """
        #TODO make doc string
        Comment this
        """
        if context is None:
            context = {}

        if default is None:
            default = {}

        default['number_request'] = self.pool.get('ir.sequence').get(cr, uid, 'intervention')
        default['date_effective_start'] = False
        default['date_effective_end'] = False
        default['duration_effective'] = 0.0
        default['categ_id'] = False
        default['description'] = False
        default['timesheet_ids'] = False

        return super(crm_intervention, self).copy(cr, uid, id, default, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
