# -*- coding: utf-8 -*-
from datetime import timedelta
from functools import partial
from random import randint

from pyramid.security import Allow
from schematics.exceptions import ValidationError
from schematics.transforms import whitelist
from schematics.types import (
    StringType,
    IntType,
    MD5Type,
    BooleanType
)
from schematics.types.compound import ModelType
from schematics.types.serializable import serializable
from zope.interface import implementer

from openprocurement.auctions.core.includeme import IAwardingNextCheck
from openprocurement.api.models.schema import (
    SwiftsureProcuringEntity,
)
from openprocurement.auctions.core.models.schema import (
    Auction as BaseAuction,
    AuctionParameters as BaseAuctionParameters,
    BankAccount,
    Bid as BaseBid,
    ComplaintModelType,
    ContractTerms,
    Feature,
    Guarantee,
    IAuction,
    ListType,
    LokiItem,
    Lot,
    Period,
    RelatedProcess,
    calc_auction_end_time,
    dgfComplaint as Complaint,
    get_auction,
    swiftsureBidDocument,
    swiftsureCancellation,
    swiftsureDocument,
    validate_contract_type,
    validate_features_uniq,
    validate_items_uniq,
    validate_lots_uniq,
    validate_not_available,
)
from openprocurement.auctions.core.models.roles import (
    swiftsure_auction_roles,
)
from openprocurement.auctions.core.plugins.awarding.v3_1.models import (
    Award
)
from openprocurement.auctions.core.plugins.contracting.v3_1.models import (
    Contract,
)
from openprocurement.auctions.core.utils import (
    rounding_shouldStartAfter_after_midnigth,
    AUCTIONS_COMPLAINT_STAND_STILL_TIME,
    calculate_business_date,
    get_request_from_root,
    get_now,
    TZ
)
from openprocurement.auctions.core.validation import (
    validate_disallow_dgfPlatformLegalDetails
)

from openprocurement.auctions.swiftsure.constants import (
    CONTRACT_TYPES,
    SWIFTSURE_STATUSES,
    SWIFTSURE_DEFAULT_STATUS,
)


validate_contract_type = partial(
    validate_contract_type,
    choices=CONTRACT_TYPES)


class AuctionParameters(BaseAuctionParameters):
    class Options:
        roles = {
            'create': whitelist('type')
        }


class Bid(BaseBid):
    class Options:
        roles = {
            'create': whitelist(
                'value',
                'tenderers',
                'parameters',
                'lotValues',
                'status',
                'qualified'),
        }

    status = StringType(
        choices=[
            'active',
            'draft',
            'invalid'],
        default='active')
    documents = ListType(
        ModelType(swiftsureBidDocument),
        default=list(),
        validators=[validate_disallow_dgfPlatformLegalDetails])
    qualified = BooleanType(required=True, choices=[True])


class AuctionAuctionPeriod(Period):
    """The auction period."""

    @serializable(serialize_when_none=False)
    def shouldStartAfter(self):
        if self.endDate:
            return
        auction = self.__parent__
        if auction.lots or auction.status not in [
                'active.tendering', 'active.auction']:
            return
        if self.startDate and get_now() > calc_auction_end_time(
                auction.numberOfBids, self.startDate):
            start_after = calc_auction_end_time(
                auction.numberOfBids, self.startDate)
        elif auction.tenderPeriod and auction.tenderPeriod.endDate:
            start_after = auction.tenderPeriod.endDate
        else:
            return
        return rounding_shouldStartAfter_after_midnigth(
            start_after, auction).isoformat()

    def validate_startDate(self, data, startDate):
        auction = get_auction(data['__parent__'])
        if not auction.revisions and not startDate:
            raise ValidationError(u'This field is required.')


class ISwiftsureAuction(IAuction):
    """Marker interface for Swiftsure auctions"""


@implementer(ISwiftsureAuction)
class SwiftsureAuction(BaseAuction):
    """Data regarding auction process

    Publicly inviting prospective contractors to submit bids for evaluation and selecting a winner or winners.
    """
    class Options:
        roles = swiftsure_auction_roles
    _internal_type = "swiftsure"
    awards = ListType(ModelType(Award), default=list())
    # A list of all the companies who entered submissions for the auction.
    bids = ListType(ModelType(Bid), default=list())
    cancellations = ListType(ModelType(swiftsureCancellation), default=list())
    complaints = ListType(ComplaintModelType(Complaint), default=list())
    contracts = ListType(ModelType(Contract), default=list())
    relatedProcesses = ListType(ModelType(RelatedProcess), default=list(), max_size=1)
    # All documents and attachments related to the auction.
    documents = ListType(ModelType(swiftsureDocument), default=list())
    # The period during which enquiries may be made and will be answered.
    enquiryPeriod = ModelType(Period)
    # The period when the auction is open for submissions. The end date is the
    # closing date for auction submissions.
    tenderPeriod = ModelType(Period)
    tenderAttempts = IntType(choices=[1, 2, 3, 4, 5, 6, 7, 8])
    auctionPeriod = ModelType(AuctionAuctionPeriod, required=True, default={})
    status = StringType(choices=SWIFTSURE_STATUSES, default=SWIFTSURE_DEFAULT_STATUS)
    features = ListType(
        ModelType(Feature),
        validators=[
            validate_features_uniq,
            validate_not_available])
    lots = ListType(
        ModelType(Lot),
        default=list(),
        validators=[
            validate_lots_uniq,
            validate_not_available])
    items = ListType(
        ModelType(LokiItem),
        default=list(),
        validators=[validate_items_uniq],
        min_size=1)
    suspended = BooleanType()
    registrationFee = ModelType(Guarantee)
    bankAccount = ModelType(BankAccount)
    auctionParameters = ModelType(AuctionParameters)
    minNumberOfQualifiedBids = IntType(choices=[1], default=1)
    procuringEntity = ModelType(SwiftsureProcuringEntity, required=True)
    contractTerms = ModelType(
        ContractTerms,
        validators=[validate_contract_type])

    def __acl__(self):
        return [
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_auction'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_auction_award'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_auction_documents'),
            (Allow, 'g:concierge', 'create_related_process'),
            (Allow, 'g:concierge', 'edit_related_process'),
            (Allow, 'g:concierge', 'delete_related_process'),
        ]

    def get_role(self):
        root = self.__parent__
        request = root.request
        if request.authenticated_role == 'Administrator':
            role = 'Administrator'
        elif request.authenticated_role == 'chronograph':
            role = 'chronograph'
        elif request.authenticated_role == 'auction':
            role = 'auction_{}'.format(request.method.lower())
        elif request.authenticated_role == 'convoy':
            role = 'convoy'
        else:
            role = 'edit_{}'.format(request.context.status)
        return role

    def initialize(self):
        if not self.enquiryPeriod:
            self.enquiryPeriod = type(self).enquiryPeriod.model_class()
        if not self.tenderPeriod:
            self.tenderPeriod = type(self).tenderPeriod.model_class()
        now = get_now()
        start_date = TZ.localize(
            self.auctionPeriod.startDate.replace(
                tzinfo=None))
        self.auctionPeriod.startDate = None
        self.auctionPeriod.endDate = None
        self.tenderPeriod.startDate = self.enquiryPeriod.startDate = now
        pause_between_periods = start_date - (
            start_date.replace(hour=20, minute=0, second=0, microsecond=0) -
            # set period end at 19:30-20:30 to reduce system load
            timedelta(days=1, minutes=randint(-30, 30))
        )
        end_date = calculate_business_date(
            start_date, -pause_between_periods, self)
        self.enquiryPeriod.endDate = end_date
        self.tenderPeriod.endDate = self.enquiryPeriod.endDate
        self.date = now
        if self.lots:
            for lot in self.lots:
                lot.date = now

    def validate_value(self, data, value):
        if value.currency != u'UAH':
            raise ValidationError(u"currency should be only UAH")

    def validate_merchandisingObject(self, data, merchandisingObject):
        if data['status'] == 'pending.activation' and not merchandisingObject:
            raise ValidationError(u'This field is required.')

    @serializable(serialize_when_none=False)
    def next_check(self):
        if self.suspended:
            return None
        now = get_now()
        checks = []
        if (
            self.status == 'active.tendering'
            and self.tenderPeriod
            and self.tenderPeriod.endDate
        ):
            checks.append(self.tenderPeriod.endDate.astimezone(TZ))
        elif (
            not self.lots
            and self.status == 'active.auction'
            and self.auctionPeriod
            and self.auctionPeriod.startDate
            and not self.auctionPeriod.endDate
        ):
            if now < self.auctionPeriod.startDate:
                checks.append(self.auctionPeriod.startDate.astimezone(TZ))
            elif now < calc_auction_end_time(self.numberOfBids, self.auctionPeriod.startDate).astimezone(TZ):
                checks.append(
                    calc_auction_end_time(
                        self.numberOfBids,
                        self.auctionPeriod.startDate).astimezone(TZ))
        elif self.lots and self.status == 'active.auction':
            for lot in self.lots:
                if (
                    lot.status != 'active'
                    or not lot.auctionPeriod
                    or not lot.auctionPeriod.startDate
                    or lot.auctionPeriod.endDate
                ):
                    continue
                if now < lot.auctionPeriod.startDate:
                    checks.append(lot.auctionPeriod.startDate.astimezone(TZ))
                elif now < calc_auction_end_time(lot.numberOfBids, lot.auctionPeriod.startDate).astimezone(TZ):
                    checks.append(
                        calc_auction_end_time(
                            lot.numberOfBids,
                            lot.auctionPeriod.startDate).astimezone(TZ))
        # Use next_check part from awarding 2.0
        request = get_request_from_root(self)
        if request is not None:
            awarding_check = request.registry.getAdapter(
                self, IAwardingNextCheck).add_awarding_checks(self)
            if awarding_check is not None:
                checks.append(awarding_check)
        if self.status.startswith('active'):
            for complaint in self.complaints:
                if complaint.status == 'claim' and complaint.dateSubmitted:
                    checks.append(
                        calculate_business_date(
                            complaint.dateSubmitted,
                            AUCTIONS_COMPLAINT_STAND_STILL_TIME,
                            self))
                elif complaint.status == 'answered' and complaint.dateAnswered:
                    checks.append(
                        calculate_business_date(
                            complaint.dateAnswered,
                            AUCTIONS_COMPLAINT_STAND_STILL_TIME,
                            self))
            for award in self.awards:
                for complaint in award.complaints:
                    if complaint.status == 'claim' and complaint.dateSubmitted:
                        checks.append(
                            calculate_business_date(
                                complaint.dateSubmitted,
                                AUCTIONS_COMPLAINT_STAND_STILL_TIME,
                                self))
                    elif complaint.status == 'answered' and complaint.dateAnswered:
                        checks.append(
                            calculate_business_date(
                                complaint.dateAnswered,
                                AUCTIONS_COMPLAINT_STAND_STILL_TIME,
                                self))
        return min(checks).isoformat() if checks else None
