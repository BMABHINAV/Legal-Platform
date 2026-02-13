from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    
    # Authentication
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Providers
    path('providers/', views.providers_list, name='providers'),
    path('providers/<str:provider_id>/', views.provider_detail, name='provider_detail'),
    path('become-provider/', views.become_provider, name='become_provider'),
    
    # Dashboards
    path('provider/dashboard/', views.provider_dashboard, name='provider_dashboard'),
    path('citizen/dashboard/', views.citizen_dashboard, name='citizen_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Features
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('incentives/', views.incentives, name='incentives'),
    
    # Document Analyzer
    path('document-analyzer/', views.document_analyzer, name='document_analyzer'),
    path('document-analyzer/analyze/', views.analyze_document, name='analyze_document'),
    path('document-analyzer/results/', views.document_results, name='document_results'),
    
    # AI Assistant
    path('ai-assistant/', views.ai_assistant, name='ai_assistant'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/htmx/chat/', views.htmx_chat, name='htmx_chat'),  # HTMX real-time chat
    
    # Triage
    path('triage/', views.triage, name='triage'),
    path('triage/results/', views.triage_results, name='triage_results'),
    
    # Bookings
    path('booking/<str:provider_id>/', views.booking_create, name='booking_create'),
    path('booking/<str:provider_id>/create/', views.htmx_create_booking, name='create_booking'),  # HTMX booking
    path('booking/<str:provider_id>/availability/', views.htmx_check_availability, name='check_availability'),  # HTMX availability
    path('bookings/<str:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<str:booking_id>/status/', views.htmx_booking_status, name='booking_status'),  # HTMX status polling
    path('bookings/<str:booking_id>/cancel/', views.htmx_cancel_booking, name='cancel_booking'),  # HTMX cancel
    
    # ============================================
    # REAL-TIME FEATURES
    # ============================================
    
    # Real-Time Chat
    path('chat/<str:room_id>/', views.chat_room, name='chat_room'),
    path('api/chat-rooms/', views.get_chat_rooms, name='get_chat_rooms'),
    
    # Video Consultations
    path('video/<str:room_code>/', views.video_room, name='video_room'),
    path('api/video/create/<str:booking_id>/', views.create_video_session, name='create_video_session'),
    
    # Panic Button / Legal Emergency
    path('emergency/', views.emergency_page, name='emergency_page'),
    path('api/emergency/create/', views.create_emergency, name='create_emergency'),
    path('api/emergency/respond/<str:emergency_id>/', views.respond_to_emergency, name='respond_to_emergency'),
    
    # AI Judge Simulator
    path('case-predictor/', views.case_predictor, name='case_predictor'),
    path('api/predict-case/', views.predict_case_api, name='predict_case_api'),
    
    # Escrow / Payments
    path('api/escrow/release/<str:booking_id>/', views.release_escrow, name='release_escrow'),
    path('api/escrow/dispute/<str:booking_id>/', views.dispute_escrow, name='dispute_escrow'),
    
    # Crowdfunding / Pro Bono
    path('crowdfunding/', views.crowdfunding_list, name='crowdfunding_list'),
    path('crowdfunding/create/', views.crowdfunding_create, name='crowdfunding_create'),
    path('crowdfunding/<str:campaign_id>/', views.crowdfunding_detail, name='crowdfunding_detail'),
    path('api/crowdfunding/donate/<str:campaign_id>/', views.donate_to_campaign, name='donate_to_campaign'),
    
    # Voice Transcription
    path('voice-input/', views.voice_input, name='voice_input'),
    path('api/voice/transcribe/', views.transcribe_voice, name='voice_transcribe'),
    
    # AI Status / Utility
    path('api/ai-status/', views.ai_status, name='ai_status'),
    
    # ============================================
    # PAYMENT GATEWAY (Razorpay)
    # ============================================
    path('api/payment/create-order/', views.create_payment_order, name='create_payment_order'),
    path('api/payment/verify/', views.verify_payment, name='verify_payment'),
    path('api/payment/webhook/', views.razorpay_webhook, name='razorpay_webhook'),
    
    # ============================================
    # PROVIDER/LAWYER FEATURES
    # ============================================
    path('provider/bookings/', views.provider_bookings, name='provider_bookings'),
    path('provider/earnings/', views.provider_earnings, name='provider_earnings'),
    path('provider/availability/', views.provider_availability_manage, name='provider_availability_manage'),
    path('api/booking/<str:booking_id>/accept/', views.accept_booking, name='accept_booking'),
    path('api/booking/<str:booking_id>/complete/', views.complete_booking, name='complete_booking'),
    path('api/booking/<str:booking_id>/note/', views.add_consultation_note, name='add_consultation_note'),
    
    # ============================================
    # CLIENT FEATURES
    # ============================================
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('my-favorites/', views.my_favorites, name='my_favorites'),
    path('api/provider/<str:provider_id>/favorite/', views.toggle_favorite_provider, name='toggle_favorite'),
    path('api/booking/<str:booking_id>/review/', views.submit_review, name='submit_review'),
    path('api/booking/<str:booking_id>/refund/', views.request_refund, name='request_refund'),
]
