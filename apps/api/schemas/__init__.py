"""
Pydantic response schemas for FlowSync Revenue Intelligence API.
All schemas use snake_case field names matching dbt mart column names.
"""

from .executive import (
    ExecKPIResponse,
    MRRTrendPoint,
    MRRTrendResponse,
    WaterfallItem,
    WaterfallResponse,
    RevenueByDimensionItem,
    RevenueByDimensionResponse,
    TopAccountItem,
    TopAccountsResponse,
)
from .revenue import (
    MRRBridgePoint,
    MRRBridgeResponse,
    AccountMovementItem,
    AccountMovementResponse,
    NewMRRByChannelItem,
    NewMRRByChannelResponse,
    ExpansionBySegmentItem,
    ExpansionBySegmentResponse,
    ChurnedByPlanItem,
    ChurnedByPlanResponse,
    PaymentTrendPoint,
    PaymentTrendResponse,
)
from .cohorts import (
    CohortHeatmapCell,
    CohortHeatmapResponse,
    LogoChurnTrendPoint,
    LogoChurnTrendResponse,
    NRRByCohortItem,
    NRRByCohortResponse,
    RetentionBySegmentItem,
    RetentionBySegmentResponse,
)
from .health import (
    HealthDistributionItem,
    HealthDistributionResponse,
    ChurnRiskQuadrantItem,
    ChurnRiskQuadrantResponse,
    UsageDropTrendPoint,
    UsageDropTrendResponse,
    SupportBurdenItem,
    SupportBurdenResponse,
    RiskyAccountItem,
    RiskyAccountsResponse,
)
from .funnel import (
    FunnelOverviewResponse,
    ConversionByChannelItem,
    ConversionByChannelResponse,
    SalesCycleItem,
    SalesCycleResponse,
    TrialEngagementItem,
    TrialEngagementResponse,
    ExpansionBySegmentFunnelItem,
    ExpansionBySegmentFunnelResponse,
)
