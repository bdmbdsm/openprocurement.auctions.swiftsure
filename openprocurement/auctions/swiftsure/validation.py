# -*- coding: utf-8 -*-
from openprocurement.auctions.core.validation import validate_json_data, validate_data
from openprocurement.auctions.core.utils import (
    search_list_with_dicts,
)


def validate_patch_auction_data(request, **kwargs):
    data = validate_json_data(request)
    if data is None:
        return
    if request.authenticated_role == 'concierge' and request.context.status != "draft":
        request.errors.add(
            'body',
            'data',
            'Can\'t update auction in current ({}) status'.format(request.context.status))
        request.errors.status = 403
        return
    if request.context.status not in ['draft', 'pending.activation']:
        return validate_data(request, type(request.auction), data=data)
    default_status = type(request.auction).fields['status'].default
    new_status = data.get('status', '')
    related_lot_is_present = search_list_with_dicts(request.context.relatedProcesses, 'type', 'lot')

    if request.context.status == 'draft':
        if not new_status or new_status not in [default_status, 'pending.activation']:
            request.errors.add('body', 'data',
                               'Can\'t update auction in current ({}) status'.format(request.context.status))
            request.errors.status = 403
            return
        elif new_status == 'pending.activation':
            if request.authenticated_role != 'concierge':
                request.errors.add(
                    'body', 'data', 'Can\'t update auction in current ({}) status'.format(request.context.status))
                request.errors.status = 403
                return
            elif not related_lot_is_present:
                request.errors.add(
                    'body', 'data', 'Can\'t switch auction to status (pending.verification) without related lot'
                )
                request.errors.status = 422
                return

        request.validated['data'] = {'status': new_status}
        request.context.status = new_status
        return

    elif request.context.status == 'pending.activation':
        if not new_status or request.authenticated_role == 'concierge' or (new_status and new_status != default_status):
            request.errors.add('body', 'data',
                               'Can\'t update auction in current ({}) status'.format(request.context.status))
            request.errors.status = 403
            return

        request.validated['data'] = {'status': new_status}
        request.context.status = new_status
        return


def validate_post_auction_status_role(request, **kwargs):
    auction = request.validated['auction']
    status = auction.get('status', type(auction).fields['status'].default)
    if request.authenticated_role == 'concierge' and status not in ['draft', 'pending.activation']:
        request.errors.add('body', 'data',
                           'Can\'t create auction in current ({}) status'.format(status))
        request.errors.status = 403
        return
