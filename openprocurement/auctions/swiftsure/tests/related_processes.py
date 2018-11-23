# -*- coding: utf-8 -*-
import unittest

from openprocurement.auctions.core.tests.base import (
    RelatedProcessesTestMixinBase,
)
from openprocurement.auctions.swiftsure.tests.base import (
    BaseAuctionWebTest,
    test_auction_data,
)

from openprocurement.auctions.core.tests.fixtures.related_process import (
    test_related_process_data,
)


class RelatedProcessesTestMixin(RelatedProcessesTestMixinBase):
    """These methods adapt test blank to the test case

    This adaptation is required because the mixin would test different types
    of resources, e.g. auctions, lots, assets.
    """

    def mixinSetUp(self):
        self.base_resource_collection_url = '/auctions'
        self.base_resource_url = '/auctions/{0}'.format(self.auction_id)

        token = self.db[self.auction_id]['owner_token']
        self.access_header = {'X-Access-Token': str(token)}

        self.base_resource_initial_data = test_auction_data
        self.initial_related_process_data = test_related_process_data

        # only concierge can edit relatedProcesses
        self.app.authorization = ('Basic', ('concierge', ''))


class SwiftsureAuctionRelatedProcessResourceTest(BaseAuctionWebTest, RelatedProcessesTestMixin):
    initial_status = 'active.tendering'
    initial_data = test_auction_data


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SwiftsureAuctionRelatedProcessResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
