import logging

from pyramid.interfaces import IRequest
from openprocurement.auctions.core.interfaces import IAuctionManager
from openprocurement.auctions.core.utils import add_related_processes_views
from openprocurement.auctions.core.traversal import factory
from openprocurement.auctions.swiftsure.models import (
    ISwiftsureAuction,
    SwiftsureAuction,
)
from openprocurement.auctions.swiftsure.adapters import (
    AuctionSwiftsureConfigurator,
    AuctionSwiftsureManagerAdapter
)
from openprocurement.auctions.core.plugins.awarding.v3_1.adapters import (
    AwardingNextCheckV3_1
)
from openprocurement.auctions.core.includeme import (
    IContentConfigurator,
    IAwardingNextCheck
)
from openprocurement.auctions.swiftsure.constants import (
    VIEW_LOCATIONS,
    DEFAULT_PROCUREMENT_METHOD_TYPE,
    DEFAULT_LEVEL_OF_ACCREDITATION
)

LOGGER = logging.getLogger(__name__)


def includeme(config, plugin_config=None):
    procurement_method_types = plugin_config.get('aliases', [])
    if plugin_config.get('use_default', False):
        procurement_method_types.append(DEFAULT_PROCUREMENT_METHOD_TYPE)
    for procurementMethodType in procurement_method_types:
        config.add_auction_procurementMethodType(SwiftsureAuction,
                                                 procurementMethodType)

    for view_location in VIEW_LOCATIONS:
        config.scan(view_location)

    # Register adapters
    config.registry.registerAdapter(
        AuctionSwiftsureConfigurator,
        (ISwiftsureAuction, IRequest),
        IContentConfigurator
    )
    config.registry.registerAdapter(
        AuctionSwiftsureManagerAdapter,
        (ISwiftsureAuction,),
        IAuctionManager
    )
    config.registry.registerAdapter(
        AwardingNextCheckV3_1,
        (ISwiftsureAuction,),
        IAwardingNextCheck
    )

    LOGGER.info("Included openprocurement.auctions.swiftsure plugin",
                extra={'MESSAGE_ID': 'included_plugin'})

    # add accreditation level
    if not plugin_config.get('accreditation'):
        config.registry.accreditation['auction'][SwiftsureAuction._internal_type] = DEFAULT_LEVEL_OF_ACCREDITATION
    else:
        config.registry.accreditation['auction'][SwiftsureAuction._internal_type] = plugin_config['accreditation']

    # add related processes views
    add_related_processes_views(config, '/auctions/{auction_id}', factory)
