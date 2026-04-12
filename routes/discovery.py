from flask import Blueprint, jsonify, request
from models import Campaign
from constants import CATEGORIES

discovery_bp = Blueprint('discovery', __name__)


@discovery_bp.route('/api/suggestions')
def suggestions():
    query = request.args.get('q', '').strip().lower()

    if len(query) < 2:
        return jsonify([])

    matching_campaigns = Campaign.query.filter(
        Campaign.status == 'approved',
        Campaign.title.ilike(f'%{query}%')
    ).limit(5).all()

    matching_categories = [c for c in CATEGORIES if query in c.lower()][:3]

    suggestions_list = []

    for c in matching_campaigns:
        suggestions_list.append({'type': 'campaign', 'text': c.title, 'id': c.id})

    for cat in matching_categories:
        suggestions_list.append({'type': 'category', 'text': cat})

    return jsonify(suggestions_list)