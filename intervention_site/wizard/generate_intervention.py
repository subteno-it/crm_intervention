# -*- coding: utf-8 -*-
from openerp.osv import orm
from openerp.osv import fields


class GenerateIntervention(orm.TransientModel):
    _name = 'generate.equipment.intervention'
    _description = 'Generate intervention from equipment'

    _columns = {
        'name': fields.char(
            'Prefix for the intervention', size=32, required=True),
        'begin_date': fields.datetime(
            'Start date', help='Date to begin intervention'),
        'section_id': fields.many2one(
            'crm.case.section', 'Section', help='Select section'),
        'user_id': fields.many2one(
            'res.users', 'Repairer', help='Select repairer'),
    }

    def create_intervention(self, cr, uid, ids, context=None):
        """
        Generate intervention from the equipment
        """
        equip_ids = context.get('active_ids', [])
        this = self.browse(cr, uid, ids[0], context=context)
        inter_obj = self.pool['crm.intervention']
        int_ids = []
        mod_obj = self.pool['ir.model.data']
        act_obj = self.pool['ir.actions.act_window']
        for eq in self.pool['intervention.equipment'].browse(
                cr, uid, equip_ids, context=context):
            part_id = eq.partner_id and eq.partner_id.id or False
            if eq.site_id and eq.site_id.customer_id:
                part_id = eq.site_id.customer_id.id

            part_vals = inter_obj.onchange_partner_intervention_id(cr, uid, [], part_id)
            int_args = {
                'name': this.name + ' ' + eq.name,
                'section_id': this.section_id and this.section_id.id or False,
                'user_id': this.user_id and this.user_id.id or False,
                'date_planned_start': this.begin_date,
                'partner_id': part_id,
                'equipment_id': eq.id,
            }
            int_args.update(part_vals['value'])
            if eq.site_id:
                int_args['site_id'] = eq.site_id.id
                if eq.site_id.partner_id:
                    int_args['partner_shipping_id'] = eq.site_id.partner_id.id
            int_ids.append(inter_obj.create(cr, uid, int_args, context=context))

        # Open the intervention with ths generate list
        result = mod_obj.get_object_reference(cr, uid, 'crm_intervention', 'crm_case_intervention_act111')
        r_id = result and result[1] or False
        result = act_obj.read(cr, uid, [r_id], context=context)[0]
        result['domain'] = "[('id','in', [" + ','.join(map(str, int_ids)) + "])]"

        return result
