"""
Dynamic Translation Service for Multilingual Support.
Uses AI/API-based translation instead of static .po files.
No GNU gettext required!
"""

import json
import hashlib
from functools import lru_cache
from django.core.cache import cache
from django.conf import settings

# Translation cache timeout (24 hours)
CACHE_TIMEOUT = 60 * 60 * 24

# Pre-defined translations for common UI strings (fast, no API call needed)
STATIC_TRANSLATIONS = {
    'hi': {
        'Find Lawyers': 'वकील खोजें',
        'Document Analyzer': 'दस्तावेज़ विश्लेषक',
        'AI Assistant': 'AI सहायक',
        'Features': 'सुविधाएँ',
        'Login': 'लॉगिन',
        'Sign Up': 'साइन अप',
        'Logout': 'लॉगआउट',
        'Dashboard': 'डैशबोर्ड',
        'Profile': 'प्रोफ़ाइल',
        'Home': 'होम',
        'Search': 'खोजें',
        'Book Now': 'अभी बुक करें',
        'Send': 'भेजें',
        'Cancel': 'रद्द करें',
        'Save': 'सहेजें',
        'Loading...': 'लोड हो रहा है...',
        'Verified': 'सत्यापित',
        'Available': 'उपलब्ध',
        'Select Language': 'भाषा चुनें',
        'Voice Input': 'आवाज़ इनपुट',
        'Speak in your language': 'अपनी भाषा में बोलें',
        'Panic Button': 'आपातकालीन बटन',
        'Emergency legal help': 'आपातकालीन कानूनी सहायता',
        'Get Legal Help': 'कानूनी सहायता प्राप्त करें',
        'Your Personal Legal Guide': 'आपका व्यक्तिगत कानूनी मार्गदर्शक',
        'Justice for Everyone': 'सभी के लिए न्याय',
        'Family Law': 'पारिवारिक कानून',
        'Criminal Law': 'आपराधिक कानून',
        'Corporate Law': 'कॉर्पोरेट कानून',
        'Property Law': 'संपत्ति कानून',
        'Tax Law': 'कर कानून',
        'Civil Law': 'सिविल कानून',
        'Consumer Law': 'उपभोक्ता कानून',
        'About Us': 'हमारे बारे में',
        'Contact': 'संपर्क',
        'Help': 'सहायता',
        'Privacy Policy': 'गोपनीयता नीति',
        'Terms of Service': 'सेवा की शर्तें',
        'All': 'सभी',
        'Filter': 'फ़िल्टर',
        'reviews': 'समीक्षाएँ',
        'per consultation': 'प्रति परामर्श',
        'years experience': 'वर्षों का अनुभव',
        'Select Date': 'तारीख चुनें',
        'Select Time': 'समय चुनें',
        'Confirm Booking': 'बुकिंग की पुष्टि करें',
        'Pay Now': 'अभी भुगतान करें',
        'Listening...': 'सुन रहा है...',
        'Tap to start speaking': 'बोलना शुरू करने के लिए टैप करें',
        'Real-Time Features': 'रियल-टाइम सुविधाएं',
        'AI Judge Simulator': 'AI न्यायाधीश सिम्युलेटर',
        'Case outcome prediction': 'केस परिणाम पूर्वानुमान',
        'Pro Bono Crowdfunding': 'प्रो बोनो क्राउडफंडिंग',
        'Fund legal aid': 'कानूनी सहायता कोष',
        'Legal Triage': 'कानूनी ट्राइएज',
        'Leaderboard': 'लीडरबोर्ड',
        'Type your legal question...': 'अपना कानूनी सवाल लिखें...',
        'Ask AI': 'AI से पूछें',
        'Speak': 'बोलें',
        'Stop': 'रुकें',
        'Clear': 'साफ करें',
        'New Chat': 'नई चैट',
        'Welcome': 'स्वागत है',
        'Hello': 'नमस्ते',
        'What is your legal question?': 'आपका कानूनी सवाल क्या है?',
        'I need help with': 'मुझे इसमें मदद चाहिए',
        'Back': 'वापस',
        'Next': 'अगला',
        'Submit': 'जमा करें',
        'Success': 'सफलता',
        'Error': 'त्रुटि',
        'Warning': 'चेतावनी',
        'Please wait...': 'कृपया प्रतीक्षा करें...',
        'No results found': 'कोई परिणाम नहीं मिला',
        'View Details': 'विवरण देखें',
        'Read More': 'और पढ़ें',
        'View All': 'सभी देखें',
        'Upload Document': 'दस्तावेज़ अपलोड करें',
        'Analyze': 'विश्लेषण करें',
        'Download': 'डाउनलोड',
        'Share': 'साझा करें',
        'Print': 'प्रिंट',
        'Copy': 'कॉपी',
        'Start Consultation': 'परामर्श शुरू करें',
        'Schedule Appointment': 'अपॉइंटमेंट शेड्यूल करें',
        'View Profile': 'प्रोफ़ाइल देखें',
        'Chat Now': 'अभी चैट करें',
        'Video Call': 'वीडियो कॉल',
        # Home page translations
        'Access': 'प्राप्त करें',
        'Justice': 'न्याय',
        'Made Simple': 'आसान बनाया',
        'AI-Powered Legal Solutions for Everyone': 'सभी के लिए AI-संचालित कानूनी समाधान',
        'Connect with': 'से जुड़ें',
        'verified advocates': 'सत्यापित वकीलों',
        'mediators, and legal experts.': 'मध्यस्थों और कानूनी विशेषज्ञों से।',
        'Get': 'प्राप्त करें',
        'AI-powered': 'AI-संचालित',
        'document analysis and': 'दस्तावेज़ विश्लेषण और',
        'instant legal guidance': 'तत्काल कानूनी मार्गदर्शन',
        'Find a Lawyer': 'वकील खोजें',
        'Analyze Document': 'दस्तावेज़ विश्लेषण',
        'Verified Lawyers': 'सत्यापित वकील',
        'Secure Payments': 'सुरक्षित भुगतान',
        '24/7 Support': '24/7 सहायता',
        'Scroll to explore': 'अन्वेषण करने के लिए स्क्रॉल करें',
        'Practice Areas': 'अभ्यास क्षेत्र',
        'Legal Services': 'कानूनी सेवाएं',
        'Categories': 'श्रेणियां',
        'Find experts specialized in your area of legal need': 'अपनी कानूनी जरूरत के क्षेत्र में विशेषज्ञों को खोजें',
        'Explore': 'अन्वेषण करें',
        'Simple Process': 'सरल प्रक्रिया',
        'How It': 'यह कैसे',
        'Works': 'काम करता है',
        'Get legal help in three simple steps': 'तीन सरल चरणों में कानूनी सहायता प्राप्त करें',
        'Describe Your Need': 'अपनी आवश्यकता बताएं',
        'Use our smart triage system or search for specific legal services you require': 'हमारी स्मार्ट ट्राइएज प्रणाली का उपयोग करें या अपनी आवश्यक कानूनी सेवाओं को खोजें',
        'Get Matched': 'मिलान प्राप्त करें',
        'Browse verified providers with ratings, reviews, and transparent pricing': 'रेटिंग, समीक्षाओं और पारदर्शी मूल्य निर्धारण के साथ सत्यापित प्रदाताओं को ब्राउज़ करें',
        'Book & Connect': 'बुक करें और जुड़ें',
        'Schedule consultations and securely communicate with your provider': 'परामर्श शेड्यूल करें और अपने प्रदाता के साथ सुरक्षित रूप से संवाद करें',
        'Top Rated': 'शीर्ष रेटेड',
        'Featured Legal': 'विशेष रुप से प्रदर्शित कानूनी',
        'Experts': 'विशेषज्ञ',
        'Top-rated professionals ready to help you': 'आपकी मदद के लिए तैयार शीर्ष रेटेड पेशेवर',
        'View All Lawyers': 'सभी वकील देखें',
        'Ready to Get Started?': 'शुरू करने के लिए तैयार?',
        'Join thousands who trust us': 'हजारों लोगों से जुड़ें जो हम पर भरोसा करते हैं',
        'Get Started Free': 'मुफ्त शुरू करें',
        'Book Consultation': 'परामर्श बुक करें',
        'Legal Platform - Connect with Verified Legal Professionals': 'लीगल प्लेटफॉर्म - सत्यापित कानूनी पेशेवरों से जुड़ें',
        # AI Assistant
        'AI Legal Assistant': 'AI कानूनी सहायक',
        'Online': 'ऑनलाइन',
        'Your Personal': 'आपका व्यक्तिगत',
        'Legal Guide': 'कानूनी मार्गदर्शक',
        'Ask questions about Indian law, procedures, or get clarification on legal terms. Powered by AI.': 'भारतीय कानून, प्रक्रियाओं के बारे में सवाल पूछें, या कानूनी शब्दों पर स्पष्टीकरण प्राप्त करें। AI द्वारा संचालित।',
        'Legal AI Assistant': 'कानूनी AI सहायक',
        'Ultra-Fast': 'अल्ट्रा-फास्ट',
        'Clear chat': 'चैट साफ करें',
        'Refresh AI Status': 'AI स्थिति रिफ्रेश करें',
        'Case Predictor': 'केस प्रेडिक्टर',
        'Welcome to Legal AI Assistant': 'कानूनी AI सहायक में आपका स्वागत है',
        'I can help you understand Indian law, legal procedures, and answer your legal questions.': 'मैं आपको भारतीय कानून, कानूनी प्रक्रियाओं को समझने और आपके कानूनी सवालों के जवाब देने में मदद कर सकता हूं।',
        'Try asking about:': 'इसके बारे में पूछने का प्रयास करें:',
        'Tenant Rights': 'किराएदार अधिकार',
        'Consumer Complaint': 'उपभोक्ता शिकायत',
        'What are my rights as a tenant in India?': 'भारत में किराएदार के रूप में मेरे क्या अधिकार हैं?',
        'How do I file a consumer complaint?': 'उपभोक्ता शिकायत कैसे दर्ज करें?',
        'Smart Escrow': 'स्मार्ट एस्क्रो',
        'Secure payments released on completion': 'पूर्ण होने पर जारी सुरक्षित भुगतान',
        "Whether you need legal advice, document review, or representation, we're here to help you navigate the legal system with confidence.": 'चाहे आपको कानूनी सलाह, दस्तावेज़ समीक्षा, या प्रतिनिधित्व की आवश्यकता हो, हम आत्मविश्वास के साथ कानूनी प्रणाली को नेविगेट करने में आपकी मदद करने के लिए यहां हैं।',
        'Start Legal Triage': 'कानूनी ट्राइएज शुरू करें',
        'Become a Provider': 'प्रदाता बनें',
        # Login/Signup page translations
        'Welcome Back': 'वापसी पर स्वागत है',
        'Sign in to access your legal dashboard': 'अपने कानूनी डैशबोर्ड तक पहुंचने के लिए साइन इन करें',
        'Username': 'उपयोगकर्ता नाम',
        'Password': 'पासवर्ड',
        'Enter your username': 'अपना उपयोगकर्ता नाम दर्ज करें',
        'Enter your password': 'अपना पासवर्ड दर्ज करें',
        'Remember me': 'मुझे याद रखें',
        'Forgot password?': 'पासवर्ड भूल गए?',
        'Sign In': 'साइन इन करें',
        'or continue with': 'या इसके साथ जारी रखें',
        "Don't have an account?": 'खाता नहीं है?',
        'Sign Up Free': 'मुफ्त साइन अप करें',
        'Secure Login': 'सुरक्षित लॉगिन',
        '256-bit Encryption': '256-बिट एन्क्रिप्शन',
        'Create Account': 'खाता बनाएं',
        'Join our legal services platform': 'हमारे कानूनी सेवा मंच से जुड़ें',
        'First Name': 'पहला नाम',
        'Last Name': 'अंतिम नाम',
        'Email': 'ईमेल',
        'Phone': 'फोन',
        '(optional)': '(वैकल्पिक)',
        'Confirm Password': 'पासवर्ड की पुष्टि करें',
        'OR': 'या',
        'Already have an account?': 'पहले से खाता है?',
        # Providers page translations
        'Find Legal Experts': 'कानूनी विशेषज्ञ खोजें',
        'Browse and connect with verified legal professionals across India': 'पूरे भारत में सत्यापित कानूनी पेशेवरों से जुड़ें और खोजें',
        'Search by name, specialization...': 'नाम, विशेषज्ञता से खोजें...',
        'All Categories': 'सभी श्रेणियां',
        'All Types': 'सभी प्रकार',
        'Advocate': 'वकील',
        'Mediator': 'मध्यस्थ',
        'Notary': 'नोटरी',
        'Arbitrator': 'पंच',
        'Top Rated': 'शीर्ष रेटेड',
        'Most Experienced': 'सबसे अनुभवी',
        'Price: Low to High': 'मूल्य: कम से अधिक',
        'Price: High to Low': 'मूल्य: अधिक से कम',
        'All Prices': 'सभी मूल्य',
        'Under': 'अंतर्गत',
        'hr': 'घंटा',
        'Above': 'ऊपर',
        'All Languages': 'सभी भाषाएं',
        'providers found': 'प्रदाता मिले',
        'Available now': 'अभी उपलब्ध',
        'years exp': 'वर्षों का अनुभव',
        'more': 'और',
        'View Profile': 'प्रोफ़ाइल देखें',
        'No providers found': 'कोई प्रदाता नहीं मिला',
        'Try adjusting your filters or search criteria': 'अपने फ़िल्टर या खोज मानदंड समायोजित करने का प्रयास करें',
        'Clear all filters': 'सभी फ़िल्टर साफ़ करें',
        # Document Analyzer translations
        'Document': 'दस्तावेज़',
        'Analyzer': 'विश्लेषक',
        'AI-Powered Analysis': 'AI-संचालित विश्लेषण',
        'NEW': 'नया',
        'Upload your legal documents and get instant AI-powered analysis with risk assessment, plain language summaries, and actionable recommendations.': 'अपने कानूनी दस्तावेज़ अपलोड करें और जोखिम मूल्यांकन, सरल भाषा सारांश और कार्रवाई योग्य सिफारिशों के साथ तत्काल AI-संचालित विश्लेषण प्राप्त करें।',
        'Risk Detection': 'जोखिम पहचान',
        'Plain Summary': 'सरल सारांश',
        'Smart Tips': 'स्मार्ट टिप्स',
        'Legal Platform': 'लीगल प्लेटफॉर्म',
        # Emergency page translations
        'Legal Emergency': 'कानूनी आपातकाल',
        'Panic Button': 'आपातकालीन बटन',
        'Emergency Legal Help': 'आपातकालीन कानूनी सहायता',
        'Legal': 'कानूनी',
        'Emergency': 'आपातकाल',
        'Press the button below in case of unlawful detention, raids, or any legal emergency. Nearby criminal defense lawyers will be alerted immediately.': 'गैरकानूनी हिरासत, छापे, या किसी भी कानूनी आपातकाल में नीचे दिए गए बटन को दबाएं। आस-पास के आपराधिक वकीलों को तुरंत सूचित किया जाएगा।',
        'PRESS FOR': 'दबाएं',
        'HELP': 'मदद',
        'Alert Broadcasted Successfully': 'अलर्ट सफलतापूर्वक प्रसारित',
        'Your location has been shared with nearby criminal defense lawyers. Stay calm, help is on the way.': 'आपका स्थान आस-पास के आपराधिक वकीलों के साथ साझा किया गया है। शांत रहें, मदद रास्ते में है।',
        'Criminal Defense Lawyer': 'आपराधिक रक्षा वकील',
        '5.0 rating': '5.0 रेटिंग',
        'RESPONDING': 'प्रतिसाद दे रहा है',
        # Legal Triage translations
        'Legal Triage': 'कानूनी ट्राइएज',
        'Smart Matching': 'स्मार्ट मिलान',
        "Answer a few questions and we'll match you with the right legal experts for your needs.": 'कुछ सवालों के जवाब दें और हम आपकी जरूरतों के लिए सही कानूनी विशेषज्ञों से मिलान करेंगे।',
        'Question': 'सवाल',
        'of': 'का',
        'Previous': 'पिछला',
        'Next': 'अगला',
        # Voice Input translations
        'Voice Support': 'आवाज़ सहायता',
        'Voice to Text Legal Help': 'आवाज़ से टेक्स्ट कानूनी सहायता',
        'Speak in your language and get legal help. We support Hindi, Tamil, Telugu, Bengali, Marathi, Kannada, and more!': 'अपनी भाषा में बोलें और कानूनी सहायता प्राप्त करें। हम हिंदी, तमिल, तेलुगु, बंगाली, मराठी, कन्नड़ और अधिक का समर्थन करते हैं!',
        'Select Your Language': 'अपनी भाषा चुनें',
        'Speech recognition works best in Chrome browser': 'स्पीच रिकॉग्निशन Chrome ब्राउज़र में सबसे अच्छा काम करता है',
        'Your Speech': 'आपका भाषण',
        # Crowdfunding translations
        'Crowdfunding': 'क्राउडफंडिंग',
        'Pro Bono Legal Aid': 'निःशुल्क कानूनी सहायता',
        'Crowd-Justice Initiative': 'क्राउड-जस्टिस पहल',
        'Legal Aid Crowdfunding': 'कानूनी सहायता क्राउडफंडिंग',
        "Help citizens who can't afford legal representation. Fund public interest cases and support justice for all.": 'उन नागरिकों की मदद करें जो कानूनी प्रतिनिधित्व का खर्च वहन नहीं कर सकते। जनहित के मामलों को वित्त पोषित करें और सभी के लिए न्याय का समर्थन करें।',
        'Active Campaigns': 'सक्रिय अभियान',
        'Total Raised': 'कुल संग्रह',
        'Cases Funded': 'वित्त पोषित मामले',
        'Start a Campaign': 'अभियान शुरू करें',
        'Browse Campaigns': 'अभियान ब्राउज़ करें',
        'How Crowd-Justice Works': 'क्राउड-जस्टिस कैसे काम करता है',
        'Submit Case': 'केस जमा करें',
        'User submits their case details and income proof': 'उपयोगकर्ता अपने केस विवरण और आय प्रमाण जमा करता है',
        'Verification': 'सत्यापन',
        'Our team verifies the case and eligibility': 'हमारी टीम केस और पात्रता की पुष्टि करती है',
        'Crowdfund': 'क्राउडफंड',
        'Public and NGOs donate to fund legal fees': 'जनता और NGO कानूनी शुल्क के लिए दान करते हैं',
        'Pro-bono lawyers take the case (2x incentive points!)': 'प्रो-बोनो वकील मामला लेते हैं (2x प्रोत्साहन अंक!)',
        # Leaderboard translations
        'Provider Leaderboard': 'प्रदाता लीडरबोर्ड',
        'Celebrating excellence in legal service delivery. See where you rank among the best.': 'कानूनी सेवा वितरण में उत्कृष्टता का जश्न। देखें कि आप सर्वश्रेष्ठ में कहां हैं।',
        'points': 'अंक',
        'Rank': 'रैंक',
        # About page translations
        'About Us': 'हमारे बारे में',
        'About Legal Platform': 'लीगल प्लेटफॉर्म के बारे में',
        'Making legal services accessible to every citizen of India': 'भारत के हर नागरिक के लिए कानूनी सेवाओं को सुलभ बनाना',
        'Our Mission': 'हमारा मिशन',
        'Legal Platform is dedicated to bridging the gap between citizens and legal professionals in India. We believe that access to justice should not be a privilege but a right for every individual.': 'लीगल प्लेटफॉर्म भारत में नागरिकों और कानूनी पेशेवरों के बीच की खाई को पाटने के लिए समर्पित है। हम मानते हैं कि न्याय तक पहुंच एक विशेषाधिकार नहीं बल्कि हर व्यक्ति का अधिकार होना चाहिए।',
        'Our platform leverages cutting-edge AI technology to provide instant document analysis, smart matching with verified legal experts, and accessible legal guidance to millions of Indians.': 'हमारा मंच करोड़ों भारतीयों को तत्काल दस्तावेज़ विश्लेषण, सत्यापित कानूनी विशेषज्ञों के साथ स्मार्ट मिलान और सुलभ कानूनी मार्गदर्शन प्रदान करने के लिए अत्याधुनिक AI तकनीक का उपयोग करता है।',
        'Trust & Security': 'विश्वास और सुरक्षा',
        'All providers are verified and payments are secured through escrow protection': 'सभी प्रदाता सत्यापित हैं और भुगतान एस्क्रो सुरक्षा के माध्यम से सुरक्षित हैं',
        'AI-Powered': 'AI-संचालित',
        'Instant document analysis and legal guidance using Google Gemini AI': 'Google Gemini AI का उपयोग करके तत्काल दस्तावेज़ विश्लेषण और कानूनी मार्गदर्शन',
        'Made for India': 'भारत के लिए बनाया गया',
        'Designed specifically for Indian legal framework and multilingual support': 'भारतीय कानूनी ढांचे और बहुभाषी समर्थन के लिए विशेष रूप से डिज़ाइन किया गया',
        # Additional translations
        'Quick Links': 'त्वरित लिंक',
        'For Providers': 'प्रदाताओं के लिए',
        'Stay Connected': 'जुड़े रहें',
        'Subscribe to our newsletter for legal updates and tips.': 'कानूनी अपडेट और टिप्स के लिए हमारे न्यूज़लेटर की सदस्यता लें।',
        'Enter your email': 'अपना ईमेल दर्ज करें',
        'All rights reserved.': 'सर्वाधिकार सुरक्षित।',
        'All systems operational': 'सभी सिस्टम चालू हैं',
        'Made with': 'के साथ बनाया गया',
        'in India': 'भारत में',
        'Emergency SOS': 'आपातकालीन SOS',
        'Emergency help': 'आपातकालीन सहायता',
        'Predict outcomes': 'परिणाम की भविष्यवाणी करें',
        'Connecting citizens with verified legal professionals across India. Making legal services accessible, affordable, and transparent.': 'पूरे भारत में नागरिकों को सत्यापित कानूनी पेशेवरों से जोड़ना। कानूनी सेवाओं को सुलभ, सस्ती और पारदर्शी बनाना।',
        'Pro Bono Cases': 'निःशुल्क मामले',
    },
    'ta': {
        'Find Lawyers': 'வழக்கறிஞர்களைக் கண்டறியுங்கள்',
        'Document Analyzer': 'ஆவண பகுப்பாய்வி',
        'AI Assistant': 'AI உதவியாளர்',
        'Features': 'அம்சங்கள்',
        'Login': 'உள்நுழைவு',
        'Sign Up': 'பதிவு செய்க',
        'Logout': 'வெளியேறு',
        'Dashboard': 'டாஷ்போர்டு',
        'Profile': 'சுயவிவரம்',
        'Home': 'முகப்பு',
        'Search': 'தேடு',
        'Book Now': 'இப்போது புக் செய்',
        'Send': 'அனுப்பு',
        'Cancel': 'ரத்து செய்',
        'Save': 'சேமி',
        'Loading...': 'ஏற்றுகிறது...',
        'Verified': 'சரிபார்க்கப்பட்டது',
        'Available': 'கிடைக்கும்',
        'Select Language': 'மொழியைத் தேர்ந்தெடுக்கவும்',
        'Voice Input': 'குரல் உள்ளீடு',
        'Get Legal Help': 'சட்ட உதவி பெறுங்கள்',
        'Justice for Everyone': 'அனைவருக்கும் நீதி',
        'Family Law': 'குடும்ப சட்டம்',
        'Criminal Law': 'குற்றவியல் சட்டம்',
        'Property Law': 'சொத்து சட்டம்',
        'Real-Time Features': 'நிகழ்நேர அம்சங்கள்',
        'Panic Button': 'அவசர பொத்தான்',
        'Emergency legal help': 'அவசர சட்ட உதவி',
        'AI Judge Simulator': 'AI நீதிபதி உருவகப்படுத்தி',
        'Case outcome prediction': 'வழக்கு முடிவு கணிப்பு',
        'Pro Bono Crowdfunding': 'இலவச நிதி திரட்டல்',
        'Fund legal aid': 'சட்ட உதவி நிதி',
        'Speak in your language': 'உங்கள் மொழியில் பேசுங்கள்',
        'Legal Triage': 'சட்ட டிரையேஜ்',
        'Leaderboard': 'தலைவர் பலகை',
        # Home page translations
        'Access': 'அணுகல்',
        'Justice': 'நீதி',
        'Made Simple': 'எளிமையாக்கப்பட்டது',
        'AI-Powered Legal Solutions for Everyone': 'அனைவருக்கும் AI-இயங்கும் சட்ட தீர்வுகள்',
        'Connect with': 'உடன் இணையுங்கள்',
        'verified advocates': 'சரிபார்க்கப்பட்ட வழக்கறிஞர்கள்',
        'Find a Lawyer': 'வழக்கறிஞரைக் கண்டறியுங்கள்',
        'Analyze Document': 'ஆவணத்தை பகுப்பாய்வு செய்',
        'Verified Lawyers': 'சரிபார்க்கப்பட்ட வழக்கறிஞர்கள்',
        'Secure Payments': 'பாதுகாப்பான பணம்',
        '24/7 Support': '24/7 ஆதரவு',
        'Scroll to explore': 'ஆராய்வதற்கு உருட்டவும்',
        'Practice Areas': 'பயிற்சி பகுதிகள்',
        'Legal Services': 'சட்ட சேவைகள்',
        'Categories': 'வகைகள்',
        'Find experts specialized in your area of legal need': 'உங்கள் சட்டத் தேவையின் பகுதியில் நிபுணர்களைக் கண்டறியுங்கள்',
        'Explore': 'ஆராயுங்கள்',
        'Simple Process': 'எளிய செயல்முறை',
        'How It': 'இது எப்படி',
        'Works': 'வேலை செய்கிறது',
        'Get legal help in three simple steps': 'மூன்று எளிய படிகளில் சட்ட உதவி பெறுங்கள்',
        'Describe Your Need': 'உங்கள் தேவையை விவரிக்கவும்',
        'Get Matched': 'பொருத்தம் பெறுங்கள்',
        'Book & Connect': 'புக் & இணைக்கவும்',
        'Top Rated': 'உயர் மதிப்பீடு',
        'Featured Legal': 'சிறப்பு சட்ட',
        'Experts': 'நிபுணர்கள்',
        'Ready to Get Started?': 'தொடங்க தயாரா?',
        'Start Legal Triage': 'சட்ட டிரையேஜ் தொடங்கு',
        'Become a Provider': 'வழங்குநராக ஆகுங்கள்',
        # Login/Signup translations
        'Welcome Back': 'மீண்டும் வருக',
        'Sign in to access your legal dashboard': 'உங்கள் சட்ட டாஷ்போர்டை அணுக உள்நுழையவும்',
        'Username': 'பயனர்பெயர்',
        'Password': 'கடவுச்சொல்',
        'Enter your username': 'உங்கள் பயனர்பெயரை உள்ளிடவும்',
        'Enter your password': 'உங்கள் கடவுச்சொல்லை உள்ளிடவும்',
        'Remember me': 'என்னை நினைவில் வை',
        'Forgot password?': 'கடவுச்சொல் மறந்துவிட்டதா?',
        'Sign In': 'உள்நுழைக',
        'or continue with': 'அல்லது தொடரவும்',
        "Don't have an account?": 'கணக்கு இல்லையா?',
        'Sign Up Free': 'இலவச பதிவு',
        'Secure Login': 'பாதுகாப்பான உள்நுழைவு',
        '256-bit Encryption': '256-பிட் குறியாக்கம்',
        'Create Account': 'கணக்கை உருவாக்கு',
        'Join our legal services platform': 'எங்கள் சட்ட சேவை தளத்தில் சேரவும்',
        'First Name': 'முதல் பெயர்',
        'Last Name': 'கடைசி பெயர்',
        'Email': 'மின்னஞ்சல்',
        'Phone': 'தொலைபேசி',
        '(optional)': '(விரும்பினால்)',
        'Confirm Password': 'கடவுச்சொல்லை உறுதிப்படுத்து',
        'OR': 'அல்லது',
        'Already have an account?': 'ஏற்கனவே கணக்கு உள்ளதா?',
        # Providers page
        'Find Legal Experts': 'சட்ட நிபுணர்களைக் கண்டறியுங்கள்',
        'Browse and connect with verified legal professionals across India': 'இந்தியா முழுவதும் சரிபார்க்கப்பட்ட சட்ட நிபுணர்களுடன் இணையுங்கள்',
        'All Categories': 'அனைத்து வகைகள்',
        'All Types': 'அனைத்து வகைகள்',
        'Advocate': 'வழக்கறிஞர்',
        'Mediator': 'மத்தியஸ்தர்',
        'Notary': 'நோட்டரி',
        'Arbitrator': 'நடுவர்',
        'Most Experienced': 'மிகவும் அனுபவமுள்ள',
        'Price: Low to High': 'விலை: குறைவு முதல் அதிகம்',
        'Price: High to Low': 'விலை: அதிகம் முதல் குறைவு',
        'All Prices': 'அனைத்து விலைகள்',
        'Under': 'கீழ்',
        'hr': 'மணி',
        'Above': 'மேலே',
        'All Languages': 'அனைத்து மொழிகள்',
        'providers found': 'வழங்குநர்கள் கண்டுபிடிக்கப்பட்டனர்',
        'Available now': 'இப்போது கிடைக்கும்',
        'years exp': 'ஆண்டுகள் அனுபவம்',
        'more': 'மேலும்',
        'View Profile': 'சுயவிவரத்தைக் காண்க',
        'No providers found': 'வழங்குநர்கள் கிடைக்கவில்லை',
        'Try adjusting your filters or search criteria': 'உங்கள் வடிகட்டிகளை மாற்றி முயற்சிக்கவும்',
        'Clear all filters': 'அனைத்து வடிகட்டிகளையும் அழி',
        # Document Analyzer
        'Document': 'ஆவணம்',
        'Analyzer': 'பகுப்பாய்வி',
        'AI-Powered Analysis': 'AI-இயக்கப்படும் பகுப்பாய்வு',
        'NEW': 'புதியது',
        'Risk Detection': 'ஆபத்து கண்டறிதல்',
        'Plain Summary': 'எளிய சுருக்கம்',
        'Smart Tips': 'ஸ்மார்ட் குறிப்புகள்',
        'Legal Platform': 'சட்ட தளம்',
    },
    'te': {
        'Find Lawyers': 'న్యాయవాదులను కనుగొనండి',
        'Document Analyzer': 'డాక్యుమెంట్ ఎనలైజర్',
        'AI Assistant': 'AI సహాయకుడు',
        'Login': 'లాగిన్',
        'Sign Up': 'సైన్ అప్',
        'Logout': 'లాగ్అవుట్',
        'Dashboard': 'డాష్‌బోర్డ్',
        'Home': 'హోమ్',
        'Search': 'వెతకండి',
        'Book Now': 'ఇప్పుడు బుక్ చేయండి',
        'Send': 'పంపండి',
        'Loading...': 'లోడ్ అవుతోంది...',
        'Verified': 'ధృవీకరించబడింది',
        'Get Legal Help': 'న్యాయ సహాయం పొందండి',
        'Justice for Everyone': 'అందరికీ న్యాయం',
        'Features': 'ఫీచర్లు',
        'Voice Input': 'వాయిస్ ఇన్‌పుట్',
        'Panic Button': 'పానిక్ బటన్',
        'Emergency legal help': 'అత్యవసర న్యాయ సహాయం',
        'Speak in your language': 'మీ భాషలో మాట్లాడండి',
        'Real-Time Features': 'రియల్-టైమ్ ఫీచర్లు',
        'AI Judge Simulator': 'AI న్యాయమూర్తి సిమ్యులేటర్',
        'Pro Bono Crowdfunding': 'ఉచిత క్రౌడ్‌ఫండింగ్',
        'Legal Triage': 'లీగల్ ట్రయాజ్',
        'Leaderboard': 'లీడర్‌బోర్డ్',
        'Select Language': 'భాషను ఎంచుకోండి',
    },
    'bn': {
        'Find Lawyers': 'উকিল খুঁজুন',
        'Document Analyzer': 'ডকুমেন্ট বিশ্লেষক',
        'AI Assistant': 'AI সহায়ক',
        'Login': 'লগইন',
        'Sign Up': 'সাইন আপ',
        'Logout': 'লগআউট',
        'Dashboard': 'ড্যাশবোর্ড',
        'Home': 'হোম',
        'Search': 'অনুসন্ধান',
        'Book Now': 'এখনই বুক করুন',
        'Send': 'পাঠান',
        'Loading...': 'লোড হচ্ছে...',
        'Verified': 'যাচাইকৃত',
        'Get Legal Help': 'আইনি সাহায্য পান',
        'Justice for Everyone': 'সবার জন্য ন্যায়বিচার',
        'Features': 'বৈশিষ্ট্য',
        'Voice Input': 'ভয়েস ইনপুট',
        'Panic Button': 'প্যানিক বাটন',
        'Emergency legal help': 'জরুরি আইনি সাহায্য',
        'Speak in your language': 'আপনার ভাষায় বলুন',
        'Real-Time Features': 'রিয়েল-টাইম বৈশিষ্ট্য',
        'AI Judge Simulator': 'AI বিচারক সিমুলেটর',
        'Pro Bono Crowdfunding': 'বিনামূল্যে ক্রাউডফান্ডিং',
        'Legal Triage': 'আইনি ট্রায়াজ',
        'Leaderboard': 'লিডারবোর্ড',
        'Select Language': 'ভাষা নির্বাচন করুন',
    },
    'mr': {
        'Find Lawyers': 'वकील शोधा',
        'Document Analyzer': 'दस्तऐवज विश्लेषक',
        'AI Assistant': 'AI सहाय्यक',
        'Login': 'लॉगिन',
        'Sign Up': 'साइन अप',
        'Logout': 'लॉगआउट',
        'Dashboard': 'डॅशबोर्ड',
        'Home': 'होम',
        'Search': 'शोधा',
        'Book Now': 'आता बुक करा',
        'Send': 'पाठवा',
        'Loading...': 'लोड होत आहे...',
        'Verified': 'सत्यापित',
        'Get Legal Help': 'कायदेशीर मदत मिळवा',
        'Justice for Everyone': 'सर्वांसाठी न्याय',
        'Features': 'वैशिष्ट्ये',
        'Voice Input': 'व्हॉइस इनपुट',
        'Panic Button': 'पॅनिक बटण',
        'Emergency legal help': 'आपत्कालीन कायदेशीर मदत',
        'Speak in your language': 'तुमच्या भाषेत बोला',
        'Real-Time Features': 'रिअल-टाइम वैशिष्ट्ये',
        'AI Judge Simulator': 'AI न्यायाधीश सिम्युलेटर',
        'Pro Bono Crowdfunding': 'मोफत क्राउडफंडिंग',
        'Legal Triage': 'कायदेशीर ट्रायज',
        'Leaderboard': 'लीडरबोर्ड',
        'Select Language': 'भाषा निवडा',
    },
    'gu': {
        'Find Lawyers': 'વકીલો શોધો',
        'AI Assistant': 'AI સહાયક',
        'Login': 'લોગિન',
        'Sign Up': 'સાઇન અપ',
        'Home': 'હોમ',
        'Search': 'શોધો',
        'Book Now': 'હમણાં બુક કરો',
        'Send': 'મોકલો',
        'Loading...': 'લોડ થઈ રહ્યું છે...',
        'Justice for Everyone': 'બધા માટે ન્યાય',
        'Features': 'વિશેષતાઓ',
        'Dashboard': 'ડેશબોર્ડ',
        'Logout': 'લોગઆઉટ',
        'Profile': 'પ્રોફાઇલ',
        'Voice Input': 'વોઇસ ઇનપુટ',
        'Panic Button': 'પેનિક બટન',
        'Emergency legal help': 'કટોકટી કાનૂની મદદ',
        'Speak in your language': 'તમારી ભાષામાં બોલો',
        'Select Language': 'ભાષા પસંદ કરો',
        'Document Analyzer': 'દસ્તાવેજ વિશ્લેષક',
    },
    'kn': {
        'Find Lawyers': 'ವಕೀಲರನ್ನು ಹುಡುಕಿ',
        'AI Assistant': 'AI ಸಹಾಯಕ',
        'Login': 'ಲಾಗಿನ್',
        'Sign Up': 'ಸೈನ್ ಅಪ್',
        'Home': 'ಮುಖಪುಟ',
        'Search': 'ಹುಡುಕಿ',
        'Book Now': 'ಈಗ ಬುಕ್ ಮಾಡಿ',
        'Send': 'ಕಳುಹಿಸಿ',
        'Loading...': 'ಲೋಡ್ ಆಗುತ್ತಿದೆ...',
        'Justice for Everyone': 'ಎಲ್ಲರಿಗೂ ನ್ಯಾಯ',
    },
    'ml': {
        'Find Lawyers': 'അഭിഭാഷകരെ കണ്ടെത്തുക',
        'AI Assistant': 'AI സഹായി',
        'Login': 'ലോഗിൻ',
        'Sign Up': 'സൈൻ അപ്പ്',
        'Home': 'ഹോം',
        'Search': 'തിരയുക',
        'Book Now': 'ഇപ്പോൾ ബുക്ക് ചെയ്യുക',
        'Send': 'അയയ്ക്കുക',
        'Loading...': 'ലോഡ് ചെയ്യുന്നു...',
        'Justice for Everyone': 'എല്ലാവർക്കും നീതി',
    },
    'pa': {
        'Find Lawyers': 'ਵਕੀਲ ਲੱਭੋ',
        'AI Assistant': 'AI ਸਹਾਇਕ',
        'Login': 'ਲਾਗਇਨ',
        'Sign Up': 'ਸਾਈਨ ਅੱਪ',
        'Home': 'ਹੋਮ',
        'Search': 'ਖੋਜੋ',
        'Book Now': 'ਹੁਣੇ ਬੁੱਕ ਕਰੋ',
        'Send': 'ਭੇਜੋ',
        'Loading...': 'ਲੋਡ ਹੋ ਰਿਹਾ ਹੈ...',
        'Justice for Everyone': 'ਸਭ ਲਈ ਨਿਆਂ',
    },
}


def get_static_translation(text: str, lang_code: str) -> str:
    """Get translation from static dictionary (fast, no API call)."""
    if lang_code == 'en':
        return text
    
    lang_translations = STATIC_TRANSLATIONS.get(lang_code, {})
    return lang_translations.get(text, None)


def translate_with_ai(text: str, target_lang: str) -> str:
    """
    Translate text using AI (Groq/Gemini).
    This is used for dynamic content that isn't in the static dictionary.
    """
    from .groq_service import get_groq_client, is_groq_available
    
    if not is_groq_available():
        return text  # Fallback to original
    
    # Language names for AI prompt
    lang_names = {
        'hi': 'Hindi',
        'ta': 'Tamil', 
        'te': 'Telugu',
        'bn': 'Bengali',
        'mr': 'Marathi',
        'gu': 'Gujarati',
        'kn': 'Kannada',
        'ml': 'Malayalam',
        'pa': 'Punjabi',
    }
    
    target_name = lang_names.get(target_lang)
    if not target_name:
        return text
    
    try:
        client = get_groq_client()
        if not client:
            return text
        
        response = client.chat.completions.create(
            model='llama-3.1-8b-instant',
            messages=[
                {
                    "role": "system",
                    "content": f"You are a translator. Translate the following text to {target_name}. Only output the translation, nothing else. Keep it natural and use the appropriate script."
                },
                {
                    "role": "user", 
                    "content": text
                }
            ],
            temperature=0.3,
            max_tokens=500,
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return text


def translate_text(text: str, lang_code: str) -> str:
    """
    Main translation function with caching.
    1. Check static translations first (fastest)
    2. Check cache
    3. Use AI translation as fallback
    """
    if not text or lang_code == 'en':
        return text
    
    # Normalize language code
    if '-' in lang_code:
        lang_code = lang_code.split('-')[0]
    
    # Try static translation first
    static_result = get_static_translation(text, lang_code)
    if static_result:
        return static_result
    
    # Check cache
    cache_key = f"trans_{lang_code}_{hashlib.md5(text.encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Use AI translation
    translated = translate_with_ai(text, lang_code)
    
    # Cache the result
    if translated != text:
        cache.set(cache_key, translated, CACHE_TIMEOUT)
    
    return translated


def bulk_translate(texts: list, lang_code: str) -> dict:
    """Translate multiple texts at once (more efficient for pages)."""
    results = {}
    
    for text in texts:
        results[text] = translate_text(text, lang_code)
    
    return results


# Template tag helper
def get_translations_for_template(lang_code: str) -> dict:
    """Get all common UI translations for JavaScript."""
    if lang_code == 'en':
        # Return English keys as values
        return {k: k for k in STATIC_TRANSLATIONS.get('hi', {}).keys()}
    
    return STATIC_TRANSLATIONS.get(lang_code, {})
