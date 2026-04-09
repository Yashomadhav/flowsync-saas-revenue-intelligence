"""
FlowSync Revenue Intelligence - SQLAlchemy ORM Models
Maps all three schema layers: raw, staging, marts.
"""

import uuid

from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime, ForeignKey,
    Integer, Numeric, String, Text, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


# ===========================================================================
# RAW SCHEMA — Bronze layer (text columns, append-only ingestion)
# ===========================================================================

class RawPlan(Base):
    __tablename__ = "raw_plans"
    __table_args__ = {"schema": "raw"}

    _row_id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_id = Column(Text)
    plan_name = Column(Text)
    monthly_price = Column(Text)
    annual_price = Column(Text)
    max_seats = Column(Text)
    max_workflows = Column(Text)
    tier = Column(Text)
    is_active = Column(Text)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())
    _source_file = Column(Text)


class RawFeature(Base):
    __tablename__ = "raw_features"
    __table_args__ = {"schema": "raw"}

    _row_id = Column(BigInteger, primary_key=True, autoincrement=True)
    feature_id = Column(Text)
    feature_name = Column(Text)
    feature_category = Column(Text)
    plan_tier_required = Column(Text)
    is_core = Column(Text)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())
    _source_file = Column(Text)


class RawCalendar(Base):
    __tablename__ = "raw_calendar"
    __table_args__ = {"schema": "raw"}

    _row_id = Column(BigInteger, primary_key=True, autoincrement=True)
    date_id = Column(Text)
    full_date = Column(Text)
    year = Column(Text)
    quarter = Column(Text)
    month = Column(Text)
    month_name = Column(Text)
    week = Column(Text)
    day_of_week = Column(Text)
    day_name = Column(Text)
    is_weekend = Column(Text)
    is_month_start = Column(Text)
    is_month_end = Column(Text)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())
    _source_file = Column(Text)


class RawAccount(Base):
    __tablename__ = "raw_accounts"
    __table_args__ = {"schema": "raw"}

    _row_id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_id = Column(Text)
    company_name = Column(Text)
    industry = Column(Text)
    company_size = Column(Text)
    region = Column(Text)
    country = Column(Text)
    acquisition_channel = Column(Text)
    account_owner = Column(Text)
    created_at = Column(Text)
    website = Column(Text)
    annual_revenue_usd = Column(Text)
    employee_count = Column(Text)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())
    _source_file = Column(Text)


class RawSubscription(Base):
    __tablename__ = "raw_subscriptions"
    __table_args__ = {"schema": "raw"}

    _row_id = Column(BigInteger, primary_key=True, autoincrement=True)
    subscription_id = Column(Text)
    account_id = Column(Text)
    plan_id = Column(Text)
    status = Column(Text)
    billing_cycle = Column(Text)
    mrr = Column(Text)
    arr = Column(Text)
    seats = Column(Text)
    start_date = Column(Text)
    end_date = Column(Text)
    trial_start = Column(Text)
    trial_end = Column(Text)
    cancelled_at = Column(Text)
    cancellation_reason = Column(Text)
    discount_pct = Column(Text)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())
    _source_file = Column(Text)


class RawInvoice(Base):
    __tablename__ = "raw_invoices"
    __table_args__ = {"schema": "raw"}

    _row_id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id = Column(Text)
    account_id = Column(Text)
    subscription_id = Column(Text)
    invoice_date = Column(Text)
    due_date = Column(Text)
    amount = Column(Text)
    currency = Column(Text)
    status = Column(Text)
    payment_method = Column(Text)
    paid_at = Column(Text)
    failure_reason = Column(Text)
    retry_count = Column(Text)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())
    _source_file = Column(Text)


class RawUsageEvent(Base):
    __tablename__ = "raw_usage_events"
    __table_args__ = {"schema": "raw"}

    _row_id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id = Column(Text)
    account_id = Column(Text)
    user_id = Column(Text)
    feature_id = Column(Text)
    event_type = Column(Text)
    event_date = Column(Text)
    session_duration_min = Column(Text)
    actions_count = Column(Text)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())
    _source_file = Column(Text)


class RawTicket(Base):
    __tablename__ = "raw_tickets"
    __table_args__ = {"schema": "raw"}

    _row_id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id = Column(Text)
    account_id = Column(Text)
    subject = Column(Text)
    category = Column(Text)
    priority = Column(Text)
    status = Column(Text)
    created_at = Column(Text)
    resolved_at = Column(Text)
    csat_score = Column(Text)
    agent_id = Column(Text)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())
    _source_file = Column(Text)


class RawLead(Base):
    __tablename__ = "raw_leads"
    __table_args__ = {"schema": "raw"}

    _row_id = Column(BigInteger, primary_key=True, autoincrement=True)
    lead_id = Column(Text)
    company_name = Column(Text)
    industry = Column(Text)
    company_size = Column(Text)
    region = Column(Text)
    acquisition_channel = Column(Text)
    lead_source = Column(Text)
    lead_date = Column(Text)
    trial_start_date = Column(Text)
    trial_end_date = Column(Text)
    converted_at = Column(Text)
    account_id = Column(Text)
    plan_id = Column(Text)
    first_mrr = Column(Text)
    lost_reason = Column(Text)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())
    _source_file = Column(Text)


# ===========================================================================
# STAGING SCHEMA — Silver layer (typed, cleaned, validated)
# ===========================================================================

class StgPlan(Base):
    __tablename__ = "stg_plans"
    __table_args__ = {"schema": "staging"}

    plan_id = Column(String(50), primary_key=True)
    plan_name = Column(String(100), nullable=False)
    monthly_price = Column(Numeric(10, 2), nullable=False)
    annual_price = Column(Numeric(10, 2))
    max_seats = Column(Integer)
    max_workflows = Column(Integer)
    tier = Column(String(20))
    is_active = Column(Boolean, default=True)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())


class StgFeature(Base):
    __tablename__ = "stg_features"
    __table_args__ = {"schema": "staging"}

    feature_id = Column(String(50), primary_key=True)
    feature_name = Column(String(200), nullable=False)
    feature_category = Column(String(100))
    plan_tier_required = Column(String(20))
    is_core = Column(Boolean, default=False)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())


class StgCalendar(Base):
    __tablename__ = "stg_calendar"
    __table_args__ = {"schema": "staging"}

    date_id = Column(Integer, primary_key=True)
    full_date = Column(Date, nullable=False, unique=True)
    year = Column(Integer)
    quarter = Column(Integer)
    month = Column(Integer)
    month_name = Column(String(20))
    week = Column(Integer)
    day_of_week = Column(Integer)
    day_name = Column(String(20))
    is_weekend = Column(Boolean)
    is_month_start = Column(Boolean)
    is_month_end = Column(Boolean)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())


class StgAccount(Base):
    __tablename__ = "stg_accounts"
    __table_args__ = {"schema": "staging"}

    account_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(300), nullable=False)
    industry = Column(String(100))
    company_size = Column(String(50))
    region = Column(String(100))
    country = Column(String(100))
    acquisition_channel = Column(String(100))
    account_owner = Column(String(200))
    created_at = Column(DateTime(timezone=True))
    website = Column(String(300))
    annual_revenue_usd = Column(Numeric(15, 2))
    employee_count = Column(Integer)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())

    subscriptions = relationship("StgSubscription", back_populates="account")
    invoices = relationship("StgInvoice", back_populates="account")
    tickets = relationship("StgTicket", back_populates="account")


class StgSubscription(Base):
    __tablename__ = "stg_subscriptions"
    __table_args__ = (
        UniqueConstraint("account_id", "plan_id", "start_date", name="uq_stg_sub_account_plan_start"),
        {"schema": "staging"},
    )

    subscription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("staging.stg_accounts.account_id"))
    plan_id = Column(String(50), ForeignKey("staging.stg_plans.plan_id"))
    status = Column(String(30))
    billing_cycle = Column(String(20))
    mrr = Column(Numeric(12, 2))
    arr = Column(Numeric(12, 2))
    seats = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    trial_start = Column(Date)
    trial_end = Column(Date)
    cancelled_at = Column(DateTime(timezone=True))
    cancellation_reason = Column(String(200))
    discount_pct = Column(Numeric(5, 2))
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("StgAccount", back_populates="subscriptions")
    plan = relationship("StgPlan")


class StgInvoice(Base):
    __tablename__ = "stg_invoices"
    __table_args__ = {"schema": "staging"}

    invoice_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("staging.stg_accounts.account_id"))
    subscription_id = Column(UUID(as_uuid=True))
    invoice_date = Column(Date)
    due_date = Column(Date)
    amount = Column(Numeric(12, 2))
    currency = Column(String(3), default="USD")
    status = Column(String(30))
    payment_method = Column(String(50))
    paid_at = Column(DateTime(timezone=True))
    failure_reason = Column(String(200))
    retry_count = Column(Integer, default=0)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("StgAccount", back_populates="invoices")


class StgUsageEvent(Base):
    __tablename__ = "stg_usage_events"
    __table_args__ = {"schema": "staging"}

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True))
    user_id = Column(String(100))
    feature_id = Column(String(50))
    event_type = Column(String(100))
    event_date = Column(Date)
    session_duration_min = Column(Integer)
    actions_count = Column(Integer)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())


class StgTicket(Base):
    __tablename__ = "stg_tickets"
    __table_args__ = {"schema": "staging"}

    ticket_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("staging.stg_accounts.account_id"))
    subject = Column(String(500))
    category = Column(String(100))
    priority = Column(String(20))
    status = Column(String(30))
    created_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    csat_score = Column(Numeric(3, 1))
    agent_id = Column(String(100))
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("StgAccount", back_populates="tickets")


class StgLead(Base):
    __tablename__ = "stg_leads"
    __table_args__ = {"schema": "staging"}

    lead_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(300))
    industry = Column(String(100))
    company_size = Column(String(50))
    region = Column(String(100))
    acquisition_channel = Column(String(100))
    lead_source = Column(String(100))
    lead_date = Column(Date)
    trial_start_date = Column(Date)
    trial_end_date = Column(Date)
    converted_at = Column(DateTime(timezone=True))
    account_id = Column(UUID(as_uuid=True))
    plan_id = Column(String(50))
    first_mrr = Column(Numeric(12, 2))
    lost_reason = Column(String(200))
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())


# ===========================================================================
# MARTS SCHEMA — Gold layer (aggregated, analytics-ready)
# ===========================================================================

class FctMrrMovement(Base):
    __tablename__ = "fct_mrr_movements"
    __table_args__ = (
        UniqueConstraint("month_date", "account_id", name="uq_fct_mrr_month_account"),
        {"schema": "marts"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    month_date = Column(Date, nullable=False)
    account_id = Column(UUID(as_uuid=True), nullable=False)
    company_name = Column(String(300))
    plan_id = Column(String(50))
    plan_name = Column(String(100))
    region = Column(String(100))
    industry = Column(String(100))
    company_size = Column(String(50))
    acquisition_channel = Column(String(100))
    starting_mrr = Column(Numeric(12, 2), default=0)
    ending_mrr = Column(Numeric(12, 2), default=0)
    new_mrr = Column(Numeric(12, 2), default=0)
    expansion_mrr = Column(Numeric(12, 2), default=0)
    contraction_mrr = Column(Numeric(12, 2), default=0)
    churned_mrr = Column(Numeric(12, 2), default=0)
    reactivation_mrr = Column(Numeric(12, 2), default=0)
    net_new_mrr = Column(Numeric(12, 2), default=0)
    movement_type = Column(String(30))
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())


class FctAccountMonthlyHealth(Base):
    __tablename__ = "fct_account_monthly_health"
    __table_args__ = (
        UniqueConstraint("month_date", "account_id", name="uq_fct_health_month_account"),
        {"schema": "marts"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    month_date = Column(Date, nullable=False)
    account_id = Column(UUID(as_uuid=True), nullable=False)
    company_name = Column(String(300))
    plan_id = Column(String(50))
    plan_name = Column(String(100))
    mrr = Column(Numeric(12, 2))
    seats = Column(Integer)
    active_users = Column(Integer)
    seat_utilization_pct = Column(Numeric(5, 2))
    total_events = Column(Integer)
    unique_features_used = Column(Integer)
    avg_session_min = Column(Numeric(8, 2))
    open_tickets = Column(Integer)
    high_priority_tickets = Column(Integer)
    avg_csat = Column(Numeric(3, 1))
    failed_invoices = Column(Integer)
    health_score = Column(Numeric(5, 2))
    health_label = Column(String(20))
    churn_risk_score = Column(Numeric(5, 2))
    churn_risk_label = Column(String(20))
    risk_flags = Column(Text)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())


class FctCustomerCohort(Base):
    __tablename__ = "fct_customer_cohorts"
    __table_args__ = (
        UniqueConstraint("cohort_month", "account_id", "months_since_start",
                         name="uq_fct_cohort_account_month"),
        {"schema": "marts"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    cohort_month = Column(Date, nullable=False)
    account_id = Column(UUID(as_uuid=True), nullable=False)
    months_since_start = Column(Integer, nullable=False)
    observation_month = Column(Date)
    is_active = Column(Boolean)
    mrr = Column(Numeric(12, 2))
    starting_mrr = Column(Numeric(12, 2))
    plan_id = Column(String(50))
    plan_name = Column(String(100))
    company_size = Column(String(50))
    acquisition_channel = Column(String(100))
    region = Column(String(100))
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())


class FctSalesConversion(Base):
    __tablename__ = "fct_sales_conversion"
    __table_args__ = {"schema": "marts"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    lead_id = Column(UUID(as_uuid=True))
    lead_date = Column(Date)
    trial_start_date = Column(Date)
    converted_at = Column(DateTime(timezone=True))
    acquisition_channel = Column(String(100))
    lead_source = Column(String(100))
    company_size = Column(String(50))
    industry = Column(String(100))
    region = Column(String(100))
    plan_id = Column(String(50))
    plan_name = Column(String(100))
    first_mrr = Column(Numeric(12, 2))
    had_trial = Column(Boolean)
    converted = Column(Boolean)
    lost_reason = Column(String(200))
    days_lead_to_trial = Column(Integer)
    days_trial_to_paid = Column(Integer)
    days_lead_to_paid = Column(Integer)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())


class MartExecRevenueSummary(Base):
    __tablename__ = "mart_exec_revenue_summary"
    __table_args__ = (
        UniqueConstraint("month_date", name="uq_mart_exec_month"),
        {"schema": "marts"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    month_date = Column(Date, nullable=False)
    total_mrr = Column(Numeric(14, 2))
    total_arr = Column(Numeric(14, 2))
    active_accounts = Column(Integer)
    new_mrr = Column(Numeric(12, 2))
    expansion_mrr = Column(Numeric(12, 2))
    contraction_mrr = Column(Numeric(12, 2))
    churned_mrr = Column(Numeric(12, 2))
    reactivation_mrr = Column(Numeric(12, 2))
    net_new_mrr = Column(Numeric(12, 2))
    logo_churn_rate = Column(Numeric(6, 4))
    revenue_churn_rate = Column(Numeric(6, 4))
    nrr = Column(Numeric(6, 4))
    grr = Column(Numeric(6, 4))
    arpa = Column(Numeric(10, 2))
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())


class MartCustomerSuccessSummary(Base):
    __tablename__ = "mart_customer_success_summary"
    __table_args__ = (
        UniqueConstraint("month_date", "account_id", name="uq_mart_cs_month_account"),
        {"schema": "marts"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    month_date = Column(Date, nullable=False)
    account_id = Column(UUID(as_uuid=True), nullable=False)
    company_name = Column(String(300))
    plan_name = Column(String(100))
    mrr = Column(Numeric(12, 2))
    health_score = Column(Numeric(5, 2))
    health_label = Column(String(20))
    churn_risk_score = Column(Numeric(5, 2))
    churn_risk_label = Column(String(20))
    seat_utilization_pct = Column(Numeric(5, 2))
    unique_features_used = Column(Integer)
    open_tickets = Column(Integer)
    avg_csat = Column(Numeric(3, 1))
    risk_flags = Column(Text)
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())


class MartRevenueBySegment(Base):
    __tablename__ = "mart_revenue_by_segment"
    __table_args__ = (
        UniqueConstraint("month_date", "segment_type", "segment_value",
                         name="uq_mart_rev_segment"),
        {"schema": "marts"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    month_date = Column(Date, nullable=False)
    segment_type = Column(String(50), nullable=False)
    segment_value = Column(String(100), nullable=False)
    total_mrr = Column(Numeric(14, 2))
    active_accounts = Column(Integer)
    new_mrr = Column(Numeric(12, 2))
    churned_mrr = Column(Numeric(12, 2))
    expansion_mrr = Column(Numeric(12, 2))
    arpa = Column(Numeric(10, 2))
    _loaded_at = Column(DateTime(timezone=True), server_default=func.now())
