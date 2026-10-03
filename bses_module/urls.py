from django.urls import path
from bses_module.views.billing_rcm import BillingRcmView
from bses_module.views.non_sm_to_sm_replacement import NonSmartToSmartReplacementView


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
]
