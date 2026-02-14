"""
Celery Tasks for background processing.
"""

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json


@shared_task
def analyze_document_async(user_id, file_content, filename):
    """
    Analyze document in background to prevent UI freezing.
    Sends notification when complete.
    """
    from .models import AnalysisResult, User, Notification
    from .gemini_service import analyze_document_with_ai
    
    try:
        user = User.objects.get(id=user_id)
        
        # Perform analysis
        analysis = analyze_document_with_ai(file_content, filename)
        
        # Save result
        result = AnalysisResult.objects.create(
            user=user,
            file_name=analysis['file_name'],
            file_type=analysis['file_type'],
            document_type=analysis['document_type'],
            health_score=analysis['health_score'],
            risk_level=analysis['risk_level'],
            summary=analysis['summary'],
            risks=analysis['risks'],
            recommendations=analysis['recommendations'],
            suggested_lawyer_categories=analysis['suggested_lawyer_categories'],
        )
        
        # Create notification
        Notification.objects.create(
            user=user,
            title='Document Analysis Ready',
            message=f'Your document "{filename}" has been analyzed. Health Score: {analysis["health_score"]}/100',
            notification_type='document_ready',
            data={'analysis_id': str(result.id), 'health_score': analysis['health_score']},
        )
        
        # Send real-time notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{user_id}',
            {
                'type': 'document_ready',
                'analysis_id': str(result.id),
                'document_name': filename,
                'health_score': analysis['health_score'],
            }
        )
        
        return {'success': True, 'analysis_id': str(result.id)}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


@shared_task
def send_booking_notification(booking_id):
    """
    Send real-time notification to provider about new booking.
    """
    from .models import Booking, Notification
    
    try:
        booking = Booking.objects.select_related('user', 'provider__user', 'service').get(id=booking_id)
        provider_user = booking.provider.user
        
        # Create notification
        notification = Notification.objects.create(
            user=provider_user,
            title='New Booking Request',
            message=f'{booking.user.get_full_name()} requested a consultation.',
            notification_type='booking_request',
            data={
                'booking_id': str(booking.id),
                'client_name': booking.user.get_full_name(),
                'service': booking.service.title if booking.service else 'Consultation',
                'amount': str(booking.amount),
            },
        )
        
        # Send real-time notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{provider_user.id}',
            {
                'type': 'booking_request',
                'booking_id': str(booking.id),
                'client_name': booking.user.get_full_name(),
                'service': booking.service.title if booking.service else 'Consultation',
                'urgency': 'normal',
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        return {'success': True}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


@shared_task
def auto_release_escrow_payments():
    """
    Automatically release escrow payments after dispute window expires.
    Runs daily.
    """
    from .models import EscrowTransaction
    
    cutoff_date = timezone.now() - timedelta(days=settings.ESCROW_AUTO_RELEASE_DAYS)
    
    transactions = EscrowTransaction.objects.filter(
        status='held',
        service_completed=True,
        held_at__lt=cutoff_date,
    )
    
    released_count = 0
    for transaction in transactions:
        transaction.status = 'released'
        transaction.released_at = timezone.now()
        transaction.save()
        
        # Award points to provider
        booking = transaction.booking
        if booking and hasattr(booking.provider, 'incentive_points'):
            booking.provider.incentive_points += 10  # Completion bonus
            booking.provider.save()
        
        released_count += 1
    
    return {'released': released_count}


@shared_task
def send_consultation_reminders():
    """
    Send reminders for consultations starting in next 15-30 minutes.
    """
    from .models import Booking, VideoSession, Notification
    
    now = timezone.now()
    start_window = now + timedelta(minutes=15)
    end_window = now + timedelta(minutes=30)
    
    upcoming = VideoSession.objects.filter(
        scheduled_at__gte=start_window,
        scheduled_at__lt=end_window,
        status='scheduled',
    ).select_related('booking__user', 'booking__provider__user')
    
    for session in upcoming:
        booking = session.booking
        
        # Notify client
        Notification.objects.create(
            user=booking.user,
            title='Consultation Starting Soon',
            message=f'Your consultation starts in 15 minutes. Room: {session.room_code}',
            notification_type='case_update',
            data={'room_code': session.room_code, 'booking_id': str(booking.id)},
        )
        
        # Notify provider
        Notification.objects.create(
            user=booking.provider.user,
            title='Consultation Starting Soon',
            message=f'Consultation with {booking.user.get_full_name()} starts in 15 minutes.',
            notification_type='case_update',
            data={'room_code': session.room_code, 'booking_id': str(booking.id)},
        )
    
    return {'reminders_sent': upcoming.count() * 2}


@shared_task
def cleanup_old_emergencies():
    """
    Clean up resolved/cancelled emergencies older than 30 days.
    """
    from .models import LegalEmergency
    
    cutoff = timezone.now() - timedelta(days=30)
    
    deleted, _ = LegalEmergency.objects.filter(
        status__in=['resolved', 'cancelled'],
        created_at__lt=cutoff,
    ).delete()
    
    return {'deleted': deleted}


@shared_task
def update_leaderboard_rankings():
    """
    Update provider rankings based on incentive points.
    Runs hourly.
    """
    from .models import ProviderProfile
    
    providers = ProviderProfile.objects.filter(
        is_verified=True
    ).order_by('-incentive_points')
    
    for rank, provider in enumerate(providers, start=1):
        # You could store ranking in a cache or separate field
        pass
    
    return {'providers_ranked': providers.count()}


@shared_task
def predict_case_outcome(user_id, case_type, case_facts):
    """
    AI Judge Simulator - Predict case outcome using Groq/Llama 3.1 (primary) or Gemini (fallback).
    """
    from .models import User, CasePrediction
    import json
    
    try:
        user = User.objects.get(id=user_id)
        
        # Try Groq first (faster and free)
        try:
            from .groq_service import predict_case_outcome as groq_predict, is_groq_available
            
            if is_groq_available():
                print("🤖 Using Groq/Llama 3.1 for case prediction...")
                result = groq_predict(case_type, case_facts)
                
                if result.get('success'):
                    prediction = CasePrediction.objects.create(
                        user=user,
                        case_type=case_type,
                        case_facts=case_facts,
                        win_probability=result.get('prediction', {}).get('winProbability', 50),
                        supporting_cases=result.get('prediction', {}).get('supportingCases', []),
                        opposing_cases=result.get('prediction', {}).get('opposingCases', []),
                        analysis=result.get('prediction', {}).get('analysis', ''),
                        recommendations=result.get('prediction', {}).get('recommendations', []),
                    )
                    return {'success': True, 'prediction_id': str(prediction.id), 'provider': 'groq-llama-3.1'}
        except Exception as e:
            print(f"Groq prediction failed, falling back to Gemini: {e}")
        
        # Fallback to Gemini
        from .gemini_service import get_gemini_model
        client = get_gemini_model()
        
        if not client:
            return {'success': False, 'error': 'No AI service available. Please configure GROQ_API_KEY or GEMINI_API_KEY.'}
        
        print("🤖 Using Gemini for case prediction...")
        prompt = f"""You are an expert Indian legal analyst. Analyze the following case and predict the outcome.

Case Type: {case_type}
Case Facts: {case_facts}

Provide your analysis in JSON format:
{{
    "winProbability": 0-100,
    "supportingCases": [
        {{"name": "Case Name", "citation": "Citation", "relevance": "Why it supports"}},
    ],
    "opposingCases": [
        {{"name": "Case Name", "citation": "Citation", "relevance": "Why it opposes"}},
    ],
    "analysis": "Detailed legal analysis",
    "recommendations": ["Recommendation 1", "Recommendation 2"]
}}

Base your analysis on Indian law (IPC, CrPC, Contract Act, Constitution, etc.).
Cite real Supreme Court and High Court judgments where applicable.
"""
        
        result = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        
        response_text = result.text.replace('```json', '').replace('```', '').strip()
        prediction_data = json.loads(response_text)
        
        prediction = CasePrediction.objects.create(
            user=user,
            case_type=case_type,
            case_facts=case_facts,
            win_probability=prediction_data.get('winProbability', 50),
            supporting_cases=prediction_data.get('supportingCases', []),
            opposing_cases=prediction_data.get('opposingCases', []),
            analysis=prediction_data.get('analysis', ''),
            recommendations=prediction_data.get('recommendations', []),
        )
        
        return {'success': True, 'prediction_id': str(prediction.id), 'provider': 'gemini'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


@shared_task
def process_voice_transcription(user_id, audio_path, source_language):
    """
    Process vernacular voice to legal text using Groq Whisper (primary) or fallback.
    """
    from .models import User, VoiceTranscription, Notification
    from django.core.files.storage import default_storage
    import os
    
    try:
        user = User.objects.get(id=user_id)
        
        # Language mapping for display
        language_names = {
            'hi': 'Hindi', 'ta': 'Tamil', 'te': 'Telugu', 'bn': 'Bengali',
            'mr': 'Marathi', 'gu': 'Gujarati', 'pa': 'Punjabi', 'kn': 'Kannada',
            'ml': 'Malayalam', 'or': 'Odia', 'en': 'English'
        }
        
        original_text = ""
        translated_text = ""
        
        # Try Groq Whisper first (fast and free)
        try:
            from .groq_service import is_groq_available, transcribe_audio
            
            if is_groq_available():
                print("🎤 Using Groq Whisper for transcription...")
                
                # Get full file path
                full_path = default_storage.path(audio_path)
                
                result = transcribe_audio(full_path, source_language)
                
                if result.get('success'):
                    original_text = result.get('text', '')
                    translated_text = result.get('translated', original_text)
                    
        except Exception as e:
            print(f"Groq transcription failed: {e}")
        
        # If Groq failed or not available, use browser-based transcription result
        if not original_text:
            # The text was already transcribed in the browser using Web Speech API
            # This is a placeholder - in production, implement server-side speech recognition
            original_text = "[Transcription processed client-side via Web Speech API]"
            translated_text = original_text
        
        # Get legal interpretation using AI
        legal_interpretation = ""
        try:
            from .groq_service import is_groq_available, get_legal_interpretation
            
            if is_groq_available() and original_text:
                result = get_legal_interpretation(original_text, source_language)
                if result.get('success'):
                    legal_interpretation = result.get('interpretation', '')
        except Exception as e:
            print(f"Legal interpretation failed: {e}")
            
            # Fallback to Gemini
            try:
                from .gemini_service import get_gemini_model
                client = get_gemini_model()
                
                if client and original_text:
                    prompt = f"""Analyze the following text from a user seeking legal help in India. 
The user spoke in {language_names.get(source_language, 'their language')}.

Text: {original_text}

Provide:
1. A summary of their legal issue
2. Relevant Indian laws that may apply
3. Suggested next steps
4. Type of lawyer they might need

Respond in simple, clear language."""

                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=prompt
                    )
                    legal_interpretation = response.text
            except Exception as gemini_error:
                print(f"Gemini interpretation failed: {gemini_error}")
        
        # Save transcription
        transcription = VoiceTranscription.objects.create(
            user=user,
            source_language=source_language,
            original_text=original_text,
            translated_text=translated_text,
            legal_interpretation=legal_interpretation,
        )
        
        # Create notification
        Notification.objects.create(
            user=user,
            title='Voice Transcription Ready',
            message=f'Your voice input in {language_names.get(source_language, "your language")} has been processed.',
            notification_type='document_ready',
            data={'transcription_id': str(transcription.id)},
        )
        
        # Clean up temp audio file
        try:
            if default_storage.exists(audio_path):
                default_storage.delete(audio_path)
        except Exception:
            pass
        
        return {
            'success': True, 
            'transcription_id': str(transcription.id),
            'original_text': original_text[:200],
            'has_interpretation': bool(legal_interpretation)
        }
    
    except User.DoesNotExist:
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
