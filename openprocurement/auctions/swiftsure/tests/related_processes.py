# -*- coding: utf-8 -*-
import unittest

from copy import deepcopy

from openprocurement.auctions.core.tests.base import (
    RelatedProcessesTestMixinBase,
)
from openprocurement.auctions.core.tests.fixtures.related_process import (
    test_related_process_data,
)
from openprocurement.auctions.swiftsure.tests.base import (
    test_auction_data,
    BaseAuctionWebTest,
)


class RelatedProcessesTestMixin(RelatedProcessesTestMixinBase):
    """These methods adapt test blank to the test case

    This adaptation is required because the mixin would test different types
    of resources, e.g. auctions, lots, assets.
    """

    def mixinSetUp(self):
        self.base_resource_url = '/auctions/{0}'.format(self.auction_id)
        self.base_resource_collection_url = '/auctions'

        token = self.auction_token
        self.access_header = {'X-Access-Token': str(token)}

        self.base_resource_initial_data = test_auction_data
        self.initial_related_process_data = test_related_process_data


class BounceAssetRelatedProcessResourceTest(BaseAuctionWebTest, RelatedProcessesTestMixin):
    initial_status = 'active.tendering'


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BounceAssetRelatedProcessResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
