"""
Management command to seed sample providers for testing.
Run with: python manage.py seed_providers
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import ProviderProfile, ServiceListing, Badge, ProviderAvailability
import random

User = get_user_model()

SAMPLE_PROVIDERS = [
    {
        'username': 'priya_sharma',
        'email': 'priya.sharma@legalplatform.com',
        'first_name': 'Priya',
        'last_name': 'Sharma',
        'phone': '+91 98765 43210',
        'provider_type': 'advocate',
        'bar_registration_number': 'BCI/2015/12345',
        'years_of_experience': 8,
        'specializations': ['family', 'property'],
        'languages': ['English', 'Hindi', 'Marathi'],
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'rating': 4.8,
        'review_count': 156,
        'completed_cases': 234,
        'response_time': '2 hours',
        'hourly_rate': 2500,
        'bio': 'Experienced family law advocate with expertise in divorce, custody, and property disputes. Committed to providing compassionate and effective legal solutions.',
        'incentive_points': 1250,
    },
    {
        'username': 'rajesh_kumar',
        'email': 'rajesh.kumar@legalplatform.com',
        'first_name': 'Rajesh',
        'last_name': 'Kumar',
        'phone': '+91 98765 43211',
        'provider_type': 'advocate',
        'bar_registration_number': 'BCI/2012/67890',
        'years_of_experience': 12,
        'specializations': ['criminal', 'civil'],
        'languages': ['English', 'Hindi', 'Tamil'],
        'city': 'Chennai',
        'state': 'Tamil Nadu',
        'rating': 4.9,
        'review_count': 203,
        'completed_cases': 345,
        'response_time': '1 hour',
        'hourly_rate': 3000,
        'bio': 'Senior advocate specializing in criminal defense and civil litigation. Known for thorough case preparation and courtroom excellence.',
        'incentive_points': 2100,
    },
    {
        'username': 'anil_desai',
        'email': 'anil.desai@legalplatform.com',
        'first_name': 'Anil',
        'last_name': 'Desai',
        'phone': '+91 98765 43212',
        'provider_type': 'mediator',
        'years_of_experience': 15,
        'specializations': ['family', 'property', 'civil'],
        'languages': ['English', 'Hindi', 'Gujarati'],
        'city': 'Ahmedabad',
        'state': 'Gujarat',
        'rating': 4.7,
        'review_count': 89,
        'completed_cases': 167,
        'response_time': '3 hours',
        'hourly_rate': 2000,
        'bio': 'Certified mediator with extensive experience in resolving family and property disputes through alternative dispute resolution.',
        'incentive_points': 890,
    },
    {
        'username': 'meera_nair',
        'email': 'meera.nair@legalplatform.com',
        'first_name': 'Meera',
        'last_name': 'Nair',
        'phone': '+91 98765 43213',
        'provider_type': 'advocate',
        'bar_registration_number': 'BCI/2018/11111',
        'years_of_experience': 6,
        'specializations': ['corporate', 'tax'],
        'languages': ['English', 'Hindi', 'Malayalam'],
        'city': 'Kochi',
        'state': 'Kerala',
        'rating': 4.6,
        'review_count': 72,
        'completed_cases': 98,
        'response_time': '4 hours',
        'hourly_rate': 3500,
        'bio': 'Corporate lawyer with expertise in business law, tax planning, and compliance. Helping startups and SMEs navigate legal complexities.',
        'incentive_points': 650,
    },
    {
        'username': 'vikram_singh',
        'email': 'vikram.singh@legalplatform.com',
        'first_name': 'Vikram',
        'last_name': 'Singh',
        'phone': '+91 98765 43214',
        'provider_type': 'advocate',
        'bar_registration_number': 'BCI/2010/22222',
        'years_of_experience': 14,
        'specializations': ['labor', 'civil', 'consumer'],
        'languages': ['English', 'Hindi', 'Punjabi'],
        'city': 'New Delhi',
        'state': 'Delhi',
        'rating': 4.85,
        'review_count': 189,
        'completed_cases': 312,
        'response_time': '2 hours',
        'hourly_rate': 2800,
        'bio': 'Labor law specialist with a strong track record in workplace disputes, employee rights, and consumer protection cases.',
        'incentive_points': 1800,
    },
    {
        'username': 'sunita_patel',
        'email': 'sunita.patel@legalplatform.com',
        'first_name': 'Sunita',
        'last_name': 'Patel',
        'phone': '+91 98765 43215',
        'provider_type': 'notary',
        'years_of_experience': 20,
        'specializations': ['property', 'civil'],
        'languages': ['English', 'Hindi', 'Gujarati'],
        'city': 'Surat',
        'state': 'Gujarat',
        'rating': 4.5,
        'review_count': 256,
        'completed_cases': 1200,
        'response_time': '1 hour',
        'hourly_rate': 1500,
        'bio': 'Registered notary with 20 years of experience in document authentication, property transactions, and legal attestations.',
        'incentive_points': 2500,
    },
    {
        'username': 'arjun_reddy',
        'email': 'arjun.reddy@legalplatform.com',
        'first_name': 'Arjun',
        'last_name': 'Reddy',
        'phone': '+91 98765 43216',
        'provider_type': 'advocate',
        'bar_registration_number': 'BCI/2016/33333',
        'years_of_experience': 8,
        'specializations': ['criminal', 'family'],
        'languages': ['English', 'Hindi', 'Telugu'],
        'city': 'Hyderabad',
        'state': 'Telangana',
        'rating': 4.75,
        'review_count': 134,
        'completed_cases': 189,
        'response_time': '3 hours',
        'hourly_rate': 2200,
        'bio': 'Criminal defense attorney with expertise in bail matters, FIR quashing, and family court disputes. Available 24/7 for emergencies.',
        'incentive_points': 980,
    },
    {
        'username': 'kavitha_menon',
        'email': 'kavitha.menon@legalplatform.com',
        'first_name': 'Kavitha',
        'last_name': 'Menon',
        'phone': '+91 98765 43217',
        'provider_type': 'arbitrator',
        'years_of_experience': 18,
        'specializations': ['corporate', 'civil', 'property'],
        'languages': ['English', 'Hindi', 'Kannada'],
        'city': 'Bangalore',
        'state': 'Karnataka',
        'rating': 4.9,
        'review_count': 67,
        'completed_cases': 145,
        'response_time': '6 hours',
        'hourly_rate': 4500,
        'bio': 'Certified arbitrator specializing in commercial disputes, real estate conflicts, and corporate arbitration. Former High Court judge.',
        'incentive_points': 3200,
    },
]

SAMPLE_SERVICES = [
    {'title': 'Initial Consultation', 'description': 'One-hour consultation to understand your case', 'category': 'other', 'price_min': 500, 'price_max': 1500, 'duration': '1 hour'},
    {'title': 'Document Review', 'description': 'Review and analysis of legal documents', 'category': 'other', 'price_min': 1000, 'price_max': 3000, 'duration': '1-2 days'},
    {'title': 'Case Filing', 'description': 'Complete case filing with court', 'category': 'other', 'price_min': 5000, 'price_max': 15000, 'duration': '1-2 weeks'},
    {'title': 'Legal Notice Drafting', 'description': 'Draft and send legal notices', 'category': 'civil', 'price_min': 2000, 'price_max': 5000, 'duration': '2-3 days'},
    {'title': 'Court Representation', 'description': 'Represent you in court proceedings', 'category': 'other', 'price_min': 10000, 'price_max': 50000, 'duration': 'Per hearing'},
]

BADGES = [
    {'name': 'Top Rated', 'description': 'Maintained 4.5+ rating for 6 months', 'icon': '⭐'},
    {'name': 'Quick Responder', 'description': 'Average response time under 3 hours', 'icon': '⚡'},
    {'name': 'Pro Bono Champion', 'description': 'Completed 10+ pro bono cases', 'icon': '🏆'},
    {'name': 'Verified Expert', 'description': 'Credentials verified by platform', 'icon': '✓'},
    {'name': 'Emergency Helper', 'description': 'Responded to 5+ panic button requests', 'icon': '🆘'},
]


class Command(BaseCommand):
    help = 'Seeds the database with sample providers for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing providers before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing providers...')
            ProviderProfile.objects.all().delete()
            User.objects.filter(role='provider').delete()
            self.stdout.write(self.style.WARNING('Cleared existing providers'))

        self.stdout.write('Seeding sample providers...')
        
        created_count = 0
        for provider_data in SAMPLE_PROVIDERS:
            # Check if user already exists
            if User.objects.filter(username=provider_data['username']).exists():
                self.stdout.write(f"  Skipping {provider_data['username']} - already exists")
                continue
            
            # Create user
            user = User.objects.create_user(
                username=provider_data['username'],
                email=provider_data['email'],
                password='demo123456',  # Default password for demo
                first_name=provider_data['first_name'],
                last_name=provider_data['last_name'],
                phone=provider_data['phone'],
                role='provider',
                verification_status='verified',  # Auto-verify for demo
            )
            
            # Create provider profile
            profile = ProviderProfile.objects.create(
                user=user,
                provider_type=provider_data['provider_type'],
                bar_registration_number=provider_data.get('bar_registration_number', ''),
                years_of_experience=provider_data['years_of_experience'],
                specializations=provider_data['specializations'],
                languages=provider_data['languages'],
                city=provider_data['city'],
                state=provider_data['state'],
                rating=provider_data['rating'],
                review_count=provider_data['review_count'],
                completed_cases=provider_data['completed_cases'],
                response_time=provider_data['response_time'],
                hourly_rate=provider_data['hourly_rate'],
                bio=provider_data['bio'],
                incentive_points=provider_data['incentive_points'],
                availability_status='available',
            )
            
            # Add services
            for service_data in random.sample(SAMPLE_SERVICES, min(3, len(SAMPLE_SERVICES))):
                ServiceListing.objects.create(
                    provider=profile,
                    title=service_data['title'],
                    description=service_data['description'],
                    category=service_data['category'],
                    price_min=service_data['price_min'],
                    price_max=service_data['price_max'],
                    duration=service_data['duration'],
                    is_active=True,
                )
            
            # Add badges
            for badge_data in random.sample(BADGES, min(2, len(BADGES))):
                Badge.objects.create(
                    provider=profile,
                    name=badge_data['name'],
                    description=badge_data['description'],
                    icon=badge_data['icon'],
                )
            
            # Add availability (Mon-Fri, 9AM-6PM)
            for day in range(5):  # Monday to Friday
                ProviderAvailability.objects.create(
                    provider=profile,
                    day_of_week=day,
                    start_time='09:00',
                    end_time='18:00',
                    is_available=True,
                )
            
            created_count += 1
            self.stdout.write(f"  Created provider: {user.get_full_name()}")
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} providers'))
        self.stdout.write(self.style.SUCCESS('Default password for all demo providers: demo123456'))
