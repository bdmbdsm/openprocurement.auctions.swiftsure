# -*- coding: utf-8 -*-
from openprocurement.auctions.core.adapters import (
    AuctionConfigurator,
    AuctionManagerAdapter,
    Manager,
)
from openprocurement.auctions.core.plugins.awarding.v3_1.adapters import (
    AwardingV3_1ConfiguratorMixin
)
from openprocurement.auctions.core.utils import (
    apply_patch,
    save_auction,
)

from openprocurement.auctions.swiftsure.models import (
    SwiftsureAuction,
)
from openprocurement.auctions.swiftsure.validation import (
    validate_post_auction_status_role
)


class AuctionSwiftsureConfigurator(AuctionConfigurator,
                                   AwardingV3_1ConfiguratorMixin):
    name = 'Auction Swiftsure Configurator'
    model = SwiftsureAuction
    pending_admission_for_one_bid = True


class SwiftsureRelatedProcessesManager(Manager):
    def create(self, request):
        self.context.relatedProcesses.append(request.validated['relatedProcess'])
        return save_auction(request)

    def update(self, request):
        return apply_patch(request, src=request.context.serialize())

    def delete(self, request):
        self.context.relatedProcesses.remove(request.validated['relatedProcess'])
        self.context.modified = False
        return save_auction(request)


class AuctionSwiftsureManagerAdapter(AuctionManagerAdapter):
    create_validation = (
        validate_post_auction_status_role,
    )
    allow_pre_terminal_statuses = False

    def __init__(self, *args, **kwargs):
        super(AuctionSwiftsureManagerAdapter, self).__init__(*args, **kwargs)
        context = args[0]
        self.related_processes_manager = SwiftsureRelatedProcessesManager(parent=context, parent_name='context')

    def _create_auction(self, request):
        auction = request.validated['auction']
        for i in request.validated['json_data'].get('documents', []):
            document = type(auction).documents.model_class(i)
            document.__parent__ = auction
            auction.documents.append(document)

    def create_auction(self, request):
        self._validate(request, self.create_validation)
        self._create_auction(request)

    def change_auction(self, request):
        pass
