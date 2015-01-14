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

from openerp.addons.crm import crm
from openerp import models, api, fields
from datetime import timedelta


class crm_intervention(models.Model):
    _name = 'crm.intervention'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Intervention'
    _order = 'id desc'

    name = fields.Char(size=128, required=True, states={'done': [('readonly', True)]})
    active = fields.Boolean(default=True)
    date_action_last = fields.Datetime(string='Last Action', readonly=True)
    date_action_next = fields.Datetime(string='Next Action', readonly=True)
    description = fields.Text(states={'done': [('readonly', True)]})
    user_id = fields.Many2one('res.users', string='Responsible', required=True, default=lambda self: self.env.user, states={'done': [('readonly', True)]})
    section_id = fields.Many2one(
        'crm.case.section', string='Interventions Team',
        default=lambda self: self.env['crm.case.section'].search([('code', '=', 'inter')]),
        states={'done': [('readonly', True)]},
        help='Interventions team to which Case belongs to. Define Responsible user and Email account for mail gateway.',
    )
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env['res.company'].browse(self.env['res.company']._company_default_get('crm.helpdesk')))
    date_closed = fields.Datetime(string='Closed on', readonly=True)
    email_from = fields.Char(string='Email', size=128, states={'done': [('readonly', True)]}, help='These people will receive email.')
    priority = fields.Selection(crm.AVAILABLE_PRIORITIES, default='2', states={'done': [('readonly', True)]})
    categ_id = fields.Many2one('crm.case.categ', string='Category', domain="[('section_id', '=', section_id), ('object_id.model', '=', 'crm.intervention')]", states={'done': [('readonly', True)]})
    number_request = fields.Char(string='Number Request', size=64, default=lambda self: self.env['ir.sequence'].get('intervention'), states={'done': [('readonly', True)]})
    customer_information = fields.Text(string='Customer_information', states={'done': [('readonly', True)]})
    intervention_todo = fields.Text(string='Intervention to do', states={'done': [('readonly', True)]}, help='Indicate the description of this intervention to do')
    date_planned_start = fields.Datetime(string='Planned Start Date', states={'done': [('readonly', True)]}, help='Indicate the date of begin intervention planned')
    date_planned_end = fields.Datetime(string='Planned End Date', states={'done': [('readonly', True)]}, help='Indicate the date of end intervention planned')
    date_effective_start = fields.Datetime(string='Effective start date', states={'done': [('readonly', True)]}, help='Indicate the date of begin intervention')
    date_effective_end = fields.Datetime(string='Effective end date', states={'done': [('readonly', True)]}, help='Indicate the date of end intervention')
    duration_planned = fields.Float(string='Planned duration', states={'done': [('readonly', True)]}, help='Indicate estimated to do the intervention.')
    duration_effective = fields.Float(string='Effective duration', states={'done': [('readonly', True)]}, help='Indicate real time to do the intervention.')
    partner_id = fields.Many2one('res.partner', string='Customer', domain="[('parent_id', '=', False)]", required=True, states={'done': [('readonly', True)]}, change_default=True, select=True)
    partner_invoice_id = fields.Many2one(
        'res.partner', string='Invoice Address',
        domain="[('parent_id', '!=', False), ('parent_id', '=', partner_id)]",
        required=True, states={'done': [('readonly', True)]},
        # default=lambda self: self.env.context.get('partner_id', False) and self.env['res.partner'].address_get([self.env.context['partner_id']], ['invoice'])['invoice'],
        help='The name and address for the invoice',
    )
    partner_order_id = fields.Many2one(
        'res.partner', string='Intervention Contact',
        domain="[('parent_id', '!=', False), ('parent_id', '=', partner_id)]",
        required=True, states={'done': [('readonly', True)]},
        # default=lambda self: self.env.context.get('partner_id', False) and self.env['res.partner'].address_get([self.env.context['partner_id']], ['contact'])['contact'],
        help='The name and address of the contact that requested the intervention.',
    )
    partner_shipping_id = fields.Many2one(
        'res.partner', string='Intervention Address',
        domain="[('parent_id', '!=', False)]",
        required=True, states={'done': [('readonly', True)]},
        # default=lambda self: self.env.context.get('partner_id', False) and self.env['res.partner'].address_get([self.env.context['partner_id']], ['delivery'])['delivery'],
    )
    partner_address_phone = fields.Char(string='Phone', states={'done': [('readonly', True)]}, size=64)
    partner_address_mobile = fields.Char(string='Mobile', states={'done': [('readonly', True)]}, size=64)
    state = fields.Selection(
        [('draft', 'Draft'), ('open', 'Open'), ('cancel', 'Cancelled'), ('done', 'Done'), ('pending', 'Pending')],
        readonly=True, default='draft',
        help="""The state is set to 'Draft', when a case is created.
        If the case is in progress the state is set to 'Open'.
        When the case is over, the state is set to 'Done'.
        If the case needs to be reviewed then the state is set to 'Pending'.""",
    )

    # FIXME : Change to new API when fixed
    _defaults = {
        'partner_invoice_id': lambda self, cr, uid, context=None: context.get('partner_id', False) and self.pool['res.partner'].address_get([context['partner_id']], ['invoice'])['invoice'],
        'partner_order_id': lambda self, cr, uid, context=None: context.get('partner_id', False) and self.pool['res.partner'].address_get([context['partner_id']], ['contact'])['contact'],
        'partner_shipping_id': lambda self, cr, uid, context=None: context.get('partner_id', False) and self.pool['res.partner'].address_get([context['partner_id']], ['delivery'])['delivery'],
    }

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False, 'partner_order_id': False, 'email_from': False, 'partner_address_phone': False, 'partner_address_mobile': False}}

        address = self.partner_id.address_get(['default', 'delivery', 'invoice', 'contact'])
        self.partner_invoice_id = address['invoice']
        self.partner_order_id = address['contact']
        self.partner_shipping_id = address['delivery']
        delivery_address = self.env['res.partner'].browse([address['invoice']])
        self.email_from = delivery_address.email
        self.partner_address_phone = delivery_address.phone
        self.partner_address_mobile = delivery_address.mobile

    @api.onchange('duration_planned')
    def onchange_planned_duration(self):
        if not self.duration_planned:
            return {'value': {'date_planned_end': False}}
        start_date = fields.Datetime.from_string(self.date_planned_start)
        self.date_planned_end = fields.Datetime.to_string(start_date + timedelta(hours=self.duration_planned))

    @api.onchange('date_planned_end')
    def onchange_planned_end_date(self):
        if not self.date_planned_start or not self.date_planned_end:
            return
        start_date = fields.Datetime.from_string(self.date_planned_start)
        end_date = fields.Datetime.from_string(self.date_planned_end)
        difference = end_date - start_date
        minutes, secondes = divmod(difference.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        self.duration_planned = float(difference.days * 24) + float(hours) + float(minutes) / float(60)

    @api.onchange('duration_effective')
    def onchange_effective_duration(self):
        if not self.duration_effective:
            return {'value': {'date_effective_end': False}}
        start_date = fields.Datetime.from_string(self.date_effective_start)
        self.date_effective_end = fields.Datetime.to_string(start_date + timedelta(hours=self.duration_effective))

    @api.onchange('date_effective_end')
    def onchange_effective_end_date(self):
        if not self.date_effective_start or not self.date_effective_end:
            return
        start_date = fields.Datetime.from_string(self.date_effective_start)
        end_date = fields.Datetime.from_string(self.date_effective_end)
        difference = end_date - start_date
        minutes, secondes = divmod(difference.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        self.duration_effective = float(difference.days * 24) + float(hours) + float(minutes) / float(60)

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}

        default['number_request'] = self.env['ir.sequence'].get('intervention')
        default['date_effective_start'] = False
        default['date_effective_end'] = False
        default['duration_effective'] = 0.0
        default['categ_id'] = False
        default['description'] = False
        default['timesheet_ids'] = False

        return super(crm_intervention, self).copy(default)

    @api.one
    def set_cancel(self):
        """
        Set the state to Cancel
        """
        self.state = 'cancel'

    @api.one
    def set_open(self):
        """
        Set the state to Open
        """
        self.state = 'open'

    @api.one
    def set_pending(self):
        """
        Set the state to Pending
        """
        self.state = 'pending'

    @api.one
    def set_done(self):
        """
        Set the state to done
        """
        self.state = 'done'

    @api.one
    def set_draft(self):
        """
        Set the state to draft
        """
        self.state = 'draft'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
