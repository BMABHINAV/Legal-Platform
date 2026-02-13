"""
Incentive rules and reward tiers for providers
"""

INCENTIVE_RULES = [
    # Quality Incentives
    {
        'id': 'high-rating',
        'name': 'High Rating Maintained',
        'description': 'Maintain 4.5+ rating for a month',
        'points_awarded': 100,
        'category': 'quality',
    },
    {
        'id': 'perfect-rating',
        'name': 'Perfect Rating',
        'description': 'Receive a 5-star review',
        'points_awarded': 20,
        'category': 'quality',
    },
    {
        'id': 'case-completed',
        'name': 'Case Completed Successfully',
        'description': 'Successfully complete a case',
        'points_awarded': 50,
        'category': 'quality',
    },
    {
        'id': 'client-retention',
        'name': 'Repeat Client',
        'description': 'Client books you again',
        'points_awarded': 75,
        'category': 'quality',
    },
    
    # Responsiveness Incentives
    {
        'id': 'quick-response',
        'name': 'Quick Responder',
        'description': 'Respond within 1 hour',
        'points_awarded': 15,
        'category': 'responsiveness',
    },
    {
        'id': 'fast-acceptance',
        'name': 'Fast Booking Acceptance',
        'description': 'Accept booking within 2 hours',
        'points_awarded': 25,
        'category': 'responsiveness',
    },
    {
        'id': 'availability-streak',
        'name': 'Availability Streak',
        'description': 'Maintain availability for 7 consecutive days',
        'points_awarded': 50,
        'category': 'responsiveness',
    },
    
    # Volume Incentives
    {
        'id': 'milestone-10',
        'name': '10 Cases Milestone',
        'description': 'Complete 10 cases',
        'points_awarded': 200,
        'category': 'volume',
    },
    {
        'id': 'milestone-50',
        'name': '50 Cases Milestone',
        'description': 'Complete 50 cases',
        'points_awarded': 500,
        'category': 'volume',
    },
    {
        'id': 'milestone-100',
        'name': '100 Cases Milestone',
        'description': 'Complete 100 cases',
        'points_awarded': 1000,
        'category': 'volume',
    },
    {
        'id': 'monthly-leader',
        'name': 'Monthly Leader',
        'description': 'Most cases completed in a month',
        'points_awarded': 300,
        'category': 'volume',
    },
    
    # Social Impact Incentives
    {
        'id': 'pro-bono',
        'name': 'Pro Bono Service',
        'description': 'Complete a pro bono case',
        'points_awarded': 150,
        'category': 'social',
    },
    {
        'id': 'legal-aid',
        'name': 'Legal Aid Support',
        'description': 'Provide free legal consultation',
        'points_awarded': 50,
        'category': 'social',
    },
    {
        'id': 'community-service',
        'name': 'Community Service',
        'description': 'Participate in legal awareness program',
        'points_awarded': 100,
        'category': 'social',
    },
]

REWARD_TIERS = [
    {
        'name': 'Bronze',
        'min_points': 0,
        'benefits': ['Basic profile listing', 'Standard support', 'Access to platform features'],
        'color': 'bronze',
        'badge_class': 'bg-amber-100 text-amber-700',
    },
    {
        'name': 'Silver',
        'min_points': 500,
        'benefits': [
            'Priority profile placement',
            'Featured in search results',
            'Priority support',
            '5% commission discount',
        ],
        'color': 'silver',
        'badge_class': 'bg-gray-100 text-gray-700',
    },
    {
        'name': 'Gold',
        'min_points': 1500,
        'benefits': [
            'Top profile placement',
            'Featured badge on profile',
            'Premium support',
            '10% commission discount',
            'Marketing support',
        ],
        'color': 'gold',
        'badge_class': 'bg-yellow-100 text-yellow-700',
    },
    {
        'name': 'Platinum',
        'min_points': 3000,
        'benefits': [
            'Exclusive profile showcase',
            'Premium featured badge',
            'Dedicated account manager',
            '15% commission discount',
            'Priority in all categories',
            'Invitations to exclusive events',
        ],
        'color': 'platinum',
        'badge_class': 'bg-blue-100 text-blue-700',
    },
]


def get_provider_tier(points):
    """Get the reward tier based on points"""
    sorted_tiers = sorted(REWARD_TIERS, key=lambda x: x['min_points'], reverse=True)
    for tier in sorted_tiers:
        if points >= tier['min_points']:
            return tier
    return REWARD_TIERS[0]


def get_next_tier(current_points):
    """Get the next tier and points needed"""
    current_tier = get_provider_tier(current_points)
    for tier in REWARD_TIERS:
        if tier['min_points'] > current_points:
            return {
                'tier': tier,
                'points_needed': tier['min_points'] - current_points
            }
    return None
