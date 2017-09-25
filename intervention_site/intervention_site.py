# -*- coding: utf-8 -*-

from openerp.osv import orm
from openerp.osv import fields
import time


class InterventionSite(orm.Model):
    _name = 'intervention.site'
    _description = 'Site of the intervention'

    _columns = {
        'name': fields.char(
            'Site Name', size=64, required=True, help='Name of the site'),
        'code': fields.char(
            'Site Code', size=16,
            help='Code for this site, keep / for automatic code'),
        'partner_id': fields.many2one(
            'res.partner', 'Address', help='Select address for this site'),
        'customer_id': fields.many2one(
            'res.partner', 'Customer', help='Select customer for this site'),
        'active': fields.boolean(
            'Active', help='if check, this object is always available'),
        'contract_id': fields.many2one(
            'account.analytic.account', 'Contract',
            help='Contract relate to this site'),
        'equipment_ids': fields.one2many(
            'intervention.equipment', 'site_id', 'Equipments',
            help='Equipment in this site'),
        'company_id': fields.many2one(
            'res.company', 'Company'),
        'notes': fields.text('Notes', help='Notes'),
        'last_date': fields.date(
            'Last Inspection', help='Date to the last inspection'),
        'next_date': fields.date(
            'Next Inspection', help='Date to the next inspection'),
        'inspection_month': fields.integer(
            'Month', help='Number of month beetween two inspection visit'),
        'section_id': fields.many2one(
            'crm.case.section', 'Section',
            help='Section assigned to this site'),
        'user_id': fields.many2one(
            'res.users', 'Repairer',
            help='Choose dedicate repairer for this site'),
        'zip': fields.related(
            'partner_id', 'zip', type='char',
            relation='res.partner', string='Zip site',
            help='Zip code for the physical address of the site'),
        'city': fields.related(
            'partner_id', 'city', type='char',
            relation='res.partner', string='City',
            help='City for the physical address of the site'),
    }

    _defaults = {
        'code': '/',
        'active': True,
        'company_id': lambda s, cr, uid,c:
            s.pool.get('res.company')._company_default_get(
                cr, uid, 'intervention.site', context=c),
        'inspection_month': 12,
    }

    def name_get(self, cr, uid, ids, context=None):
        """
        For each site, add zip and city
        """
        if context is None:
            context = {}
        if not len(ids):
            return []
        sites = self.browse(cr, uid, ids, context=context)
        res = []
        for site in sites:
            name = site.name
            p = site.partner_id
            if p:
                name += ' (%s %s)' % (p.zip or '',p.city or '')
            res.append((site.id, name))
        return res

    def create(self, cr, uid, values, context=None):
        """
        Generate site code
        """
        if context is None:
            context = {}

        if values.get('code', '') == '/':
            values['code'] = self.pool.get('ir.sequence').get(cr, uid, 'intervention.site') or '/'

        return super(InterventionSite, self).create(cr, uid, values, context=context)

    def create_intervention(self, cr, uid, ids, context=None):
        """Create an inetrvention from the site"""
        inter_obj = self.pool['crm.intervention']
        int_ids = []
        for site in self.browse(cr, uid, ids, context=context):
            part_id = site.customer_id and site.customer_id.id or False
            part_vals = inter_obj.onchange_partner_intervention_id(cr, uid, [], part_id)
            int_args = {
                'name': site.name,
                'section_id': site.section_id and site.section_id.id or False,
                'user_id': site.user_id and site.user_id.id or False,
                'date_planned_start': time.strftime('%Y-%m-%d %H:%M:00'),
                'duration_planned': 1.0,
                'partner_id': part_id,
                'equipment_id': False,
            }
            int_args['date_planned_end'] = inter_obj.onchange_planned_duration(
                cr, uid, [], 1.0, int_args['date_planned_start']
            )['value']['date_planned_end']
            if site.partner_id:
                int_args['partner_shipping_id'] = site.partner_id.id
            int_args.update(part_vals['value'])
            int_ids.append(inter_obj.create(cr, uid, int_args, context=context))
        return inter_obj.open_intervention(cr, uid, int_ids, context=context)
