from django.urls import path
from bses_module.views.billing_rcm import BillingRcmView
from bses_module.views.non_sm_to_sm_replacement import NonSmartToSmartReplacementView
from bses_module.views.meter_removal import MeterRemovalView
from bses_module.views.sm_to_sm_replacement import SmartToSmartReplacementView


urlpatterns = [
    path(
        "nonsm-to-sm",
        NonSmartToSmartReplacementView.as_view(),
        name="nonsmtosm_inbound",
    ),
    path(
        "billing-rcm",
        BillingRcmView.as_view(),
        name="billing_rcm_inbound",
    ),
    path(
        "meter-removal",
        MeterRemovalView.as_view(),
        name="meter_removal_inbound",
    ),
    path(
        "sm-to-sm",
        SmartToSmartReplacementView.as_view(),
        name="smtosm_inbound",
    ),
]
