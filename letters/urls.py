from letters.views import GeneratedLetterView
from django.urls import path
from .views import (
    ApiIntegrationRequestApi, OfferLetterGeneratorView, AppointmentLetterGeneratorView, ConfirmationLetterGeneratorView,
    ExperienceLetterGeneratorView, IncrementLetterGeneratorView, RelievingLetterGeneratorView,
    LeavePolicyGeneatorView, WFHHybridPolicyGeneatorView, FreelancerContractGeneratorView,
    NDAContractGeneratorView, OnbordingEmployerBrandingGeneatorView, EVPBuilderEmployerBrandingGeneatorView,
    EmployerBrandingEmployerBrandingGeneratorView, LetterSettingsView,
    # Billing
    LetterCreditPackageListView, LetterCreditWalletView, LetterCreditTransactionListView,
    LetterCreateOrderView, LetterPaymentSuccessView,
    # Tool Request
    ToolRequestView
)

urlpatterns = [

    path('offer-letter/', OfferLetterGeneratorView.as_view(), name='generate-offer-letter'),
    path('offer-letter/<int:id>/', OfferLetterGeneratorView.as_view(), name='generate-offer-letter'),

    path('appointment-letter/', AppointmentLetterGeneratorView.as_view(), name='generate-appointment-letter'),
    path('appointment-letter/<int:id>/', AppointmentLetterGeneratorView.as_view(), name='generate-appointment-letter'),

    path('confirmation-letter/', ConfirmationLetterGeneratorView.as_view(), name='generate-confirmation-letter'),
    path('confirmation-letter/<int:id>/', ConfirmationLetterGeneratorView.as_view(), name='generate-confirmation-letter'),
 
    path('increment-letter/', IncrementLetterGeneratorView.as_view(), name='generate-increment-letter'),
    path('increment-letter/<int:id>/', IncrementLetterGeneratorView.as_view(), name='generate-increment-letter'),
 
    path('experience-letter/', ExperienceLetterGeneratorView.as_view(), name='generate-experience-letter'),
    path('experience-letter/<int:id>/', ExperienceLetterGeneratorView.as_view(), name='generate-experience-letter'),
 
    path('relieving-letter/', RelievingLetterGeneratorView.as_view(), name='generate-relieving-letter'),
    path('relieving-letter/<int:id>/', RelievingLetterGeneratorView.as_view(), name='generate-relieving-letter'),

    path('leave-policy/', LeavePolicyGeneatorView.as_view(), name='generate-leave-policy'),
    path('leave-policy/<int:id>/', LeavePolicyGeneatorView.as_view(), name='generate-leave-policy'),

    path('wfh-policy/', WFHHybridPolicyGeneatorView.as_view(), name='generate-wfh-policy'),
    path('wfh-policy/<int:id>/', WFHHybridPolicyGeneatorView.as_view(), name='generate-wfh-policy'),

    path('freelancer-contract/', FreelancerContractGeneratorView.as_view(), name='generate-freelancer-contract'),
    path('freelancer-contract/<int:id>/', FreelancerContractGeneratorView.as_view(), name='generate-freelancer-contract'),

    path('nda/', NDAContractGeneratorView.as_view(), name='generate-nda'),
    path('nda/<int:id>/', NDAContractGeneratorView.as_view(), name='generate-nda'),

    path('onboarding/', OnbordingEmployerBrandingGeneatorView.as_view(), name='generate-onboarding'),
    path('onboarding/<int:id>/', OnbordingEmployerBrandingGeneatorView.as_view(), name='generate-onboarding'),

    path('evp-builder/', EVPBuilderEmployerBrandingGeneatorView.as_view(), name='generate-evp-builder'),
    path('evp-builder/<int:id>/', EVPBuilderEmployerBrandingGeneatorView.as_view(), name='generate-evp-builder'),

    path('branding-post/', EmployerBrandingEmployerBrandingGeneratorView.as_view(), name='generate-branding-post'),
    path('branding-post/<int:id>/', EmployerBrandingEmployerBrandingGeneratorView.as_view(), name='generate-branding-post'),

    path('settings/', LetterSettingsView.as_view(), name='letter-settings'),
    path('generated-letters/', GeneratedLetterView.as_view(), name='generated-letters'),
    path('generated-letters/<int:id>/', GeneratedLetterView.as_view(), name='generated-letter'),

    # ── Credit Billing ──────────────────────────────────────────────────────────
    path('billing/packages/', LetterCreditPackageListView.as_view(), name='letter-billing-packages'),
    path('billing/wallet/', LetterCreditWalletView.as_view(), name='letter-billing-wallet'),
    path('billing/transactions/', LetterCreditTransactionListView.as_view(), name='letter-billing-transactions'),
    path('billing/create-order/', LetterCreateOrderView.as_view(), name='letter-billing-create-order'),
    path('billing/payment-success/', LetterPaymentSuccessView.as_view(), name='letter-billing-payment-success'),
    
    # ── Tool Request ───────────────────────────────────────────────────────────
    path('tool-request/', ToolRequestView.as_view(), name='tool-request'),
    
    # ── API Request ───────────────────────────────────────────────────────────
    path('api-integration-request/', ApiIntegrationRequestApi.as_view(), name='api-integration-request'),
]
