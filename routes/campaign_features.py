from flask import Blueprint, redirect, url_for, render_template, request
from flask_login import login_required, current_user
from models import db, Campaign, Wishlist

campaign_bp = Blueprint('campaign', __name__)


@campaign_bp.route('/wishlist/toggle/<int:id>', methods=['POST'])
@login_required
def toggle_wishlist(id):
    existing = Wishlist.query.filter_by(user_id=current_user.id, campaign_id=id).first()

    if existing:
        db.session.delete(existing)
    else:
        db.session.add(Wishlist(user_id=current_user.id, campaign_id=id))

    db.session.commit()
    return redirect(url_for('campaign_details_route', id=id))


@campaign_bp.route('/success')
def success():
    campaign_id = request.args.get('campaign_id', type=int)
    amount = request.args.get('amount', type=float)
    is_anonymous = request.args.get('anonymous') == 'true'
    campaign = Campaign.query.get_or_404(campaign_id)
    return render_template('success.html', campaign=campaign, amount=amount, is_anonymous=is_anonymous)