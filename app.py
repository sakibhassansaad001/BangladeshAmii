from flask import Flask, render_template, redirect, url_for, request, flash
from models import (
    db, User, Campaign, Contribution, CampaignUpdate, Media,
    Wishlist, Comment, CommentVote, Notification
)
from config import Config
from constants import CATEGORIES, CROWDFUNDING_TYPES
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "signin"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


from routes.discovery import discovery_bp
from routes.campaign_features import campaign_bp
from routes.comments import comments_bp

app.register_blueprint(discovery_bp)
app.register_blueprint(campaign_bp)
app.register_blueprint(comments_bp)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def create_notification(user_id, title, message, category, campaign_id=None):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        category=category,
        campaign_id=campaign_id
    )
    db.session.add(notification)


@app.context_processor
def inject_notifications():
    if current_user.is_authenticated:
        recent_notifications = Notification.query.filter_by(user_id=current_user.id)\
            .order_by(Notification.created_at.desc())\
            .limit(6).all()

        unread_count = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).count()

        return {
            "recent_notifications": recent_notifications,
            "unread_notification_count": unread_count
        }

    return {
        "recent_notifications": [],
        "unread_notification_count": 0
    }


@app.route('/notifications/read/<int:id>', methods=['POST'])
@login_required
def mark_notification_read(id):
    notification = Notification.query.get_or_404(id)
    if notification.user_id != current_user.id:
        flash("You are not allowed to access that notification.", "error")
        return redirect(url_for('dashboard'))

    notification.is_read = True
    db.session.commit()

    if notification.campaign_id:
        return redirect(url_for('campaign_details_route', id=notification.campaign_id))
    return redirect(url_for('dashboard'))

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_campaign():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        goal = request.form.get('goal', '').strip()
        duration = request.form.get('duration', '').strip()
        category = request.form.get('category', '').strip()
        crowdfunding_type = request.form.get('crowdfunding_type', '').strip()

        if not title or not description or not goal or not duration or not category or not crowdfunding_type:
            flash("All campaign fields are required.", "error")
            return redirect(url_for('create_campaign'))

        try:
            goal_amount = float(goal)
            duration_days = int(duration)
        except ValueError:
            flash("Goal amount and duration must be valid numbers.", "error")
            return redirect(url_for('create_campaign'))

        if goal_amount <= 0:
            flash("Goal amount must be greater than 0.", "error")
            return redirect(url_for('create_campaign'))

        if duration_days <= 0:
            flash("Duration must be greater than 0.", "error")
            return redirect(url_for('create_campaign'))

        if category not in CATEGORIES:
            flash("Please select a valid category.", "error")
            return redirect(url_for('create_campaign'))

        if crowdfunding_type not in CROWDFUNDING_TYPES:
            flash("Please select a valid crowdfunding type.", "error")
            return redirect(url_for('create_campaign'))

        campaign = Campaign(
            title=title,
            description=description,
            goal_amount=goal_amount,
            duration=duration_days,
            category=category,
            crowdfunding_type=crowdfunding_type,
            user_id=current_user.id,
            status="pending"
        )
        db.session.add(campaign)
        db.session.flush()

        files = request.files.getlist('media')
        for file in files:
            if file and file.filename:
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_name = f"{campaign.id}_{int(datetime.utcnow().timestamp())}_{filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
                    ext = filename.rsplit('.', 1)[1].lower()
                    media_type = 'video' if ext in ['mp4', 'webm', 'mov'] else 'image'
                    db.session.add(Media(filename=unique_name, media_type=media_type, campaign_id=campaign.id))
                else:
                    flash(f"Unsupported file type: {file.filename}", "error")
                    return redirect(url_for('create_campaign'))

        admins = User.query.filter_by(role="admin").all()
        for admin in admins:
            create_notification(
                user_id=admin.id,
                title="New campaign submitted",
                message=f"{current_user.name} submitted '{campaign.title}' for review.",
                category="campaign",
                campaign_id=campaign.id
            )

        db.session.commit()
        flash("Campaign submitted successfully for review.", "success")
        return redirect(url_for('dashboard'))

    return render_template(
        "create_campaign.html",
        categories=CATEGORIES,
        crowdfunding_types=CROWDFUNDING_TYPES
    )

@app.route('/cancel/<int:id>')
@login_required
def cancel_campaign(id):
    campaign = Campaign.query.get_or_404(id)
    if campaign.user_id == current_user.id and campaign.status == "pending":
        campaign.status = "cancelled"
        db.session.commit()
        flash("Campaign cancelled.", "success")
    else:
        flash("You cannot cancel this campaign.", "error")
    return redirect(url_for('dashboard'))

@app.route('/campaign/<int:id>/update', methods=['POST'])
@login_required
def add_update(id):
    campaign = Campaign.query.get_or_404(id)
    if campaign.user_id != current_user.id:
        flash("Only the campaign owner can post updates.", "error")
        return redirect(url_for('campaign_details_route', id=id))

    content = request.form.get('content', '').strip()
    if not content:
        flash("Update content is required.", "error")
        return redirect(url_for('campaign_details_route', id=id))

    db.session.add(CampaignUpdate(content=content, campaign_id=id, user_id=current_user.id))

    contributor_ids = db.session.query(Contribution.user_id)\
        .filter(Contribution.campaign_id == id, Contribution.user_id != current_user.id)\
        .distinct().all()

    for (user_id,) in contributor_ids:
        create_notification(
            user_id=user_id,
            title="Campaign updated",
            message=f"{current_user.name} posted a new update on '{campaign.title}'.",
            category="update",
            campaign_id=campaign.id
        )

    admins = User.query.filter_by(role="admin").all()
    for admin in admins:
        if admin.id != current_user.id:
            create_notification(
                user_id=admin.id,
                title="Campaign owner posted an update",
                message=f"{current_user.name} updated '{campaign.title}'.",
                category="alert",
                campaign_id=campaign.id
            )

    db.session.commit()
    flash("Campaign update posted.", "success")
    return redirect(url_for('campaign_details_route', id=id))

# Hridoy
@app.route('/')
def index():
    search_query = request.args.get('q', '').strip()
    selected_category = request.args.get('category', '')
    selected_type = request.args.get('type', '')

    query = Campaign.query.filter_by(status="approved")

    if search_query:
        query = query.filter(Campaign.title.ilike(f'%{search_query}%'))
    if selected_category:
        query = query.filter_by(category=selected_category)
    if selected_type:
        query = query.filter_by(crowdfunding_type=selected_type)

    campaigns = query.order_by(Campaign.created_at.desc()).all()

    for campaign in campaigns:
        if campaign.goal_amount and campaign.goal_amount > 0:
            campaign.percent = min((campaign.current_amount / campaign.goal_amount) * 100, 100)
        else:
            campaign.percent = 0

        first_media = Media.query.filter_by(campaign_id=campaign.id).first()
        campaign.cover_media = first_media

    total_raised = sum(c.current_amount or 0 for c in Campaign.query.filter_by(status="approved").all())
    total_backers = Contribution.query.count()

    return render_template(
        "index.html",
        campaigns=campaigns,
        categories=CATEGORIES,
        crowdfunding_types=CROWDFUNDING_TYPES,
        selected_category=selected_category,
        selected_type=selected_type,
        search_query=search_query,
        total_raised=total_raised,
        total_backers=total_backers
    )

# HRIDOY
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        university = request.form.get('university', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not name or not university or not email or not password:
            flash("All signup fields are required.", "error")
            return redirect(url_for('signup'))

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
            return redirect(url_for('signup'))

        hashed_pw = generate_password_hash(password)
        user = User(
            name=name,
            email=email,
            password=hashed_pw,
            university_name=university
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully. Please sign in.", "success")
        return redirect(url_for('signin'))

    return render_template("signup.html")

# HRIDOY
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for('signin'))

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Signed in successfully.", "success")
            return redirect(url_for('dashboard'))

        flash("Invalid email or password.", "error")
        return redirect(url_for('signin'))

    return render_template("signin.html")

# HRIDOY
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

# HRIDOY
@app.route('/dashboard')
@login_required
def dashboard():
    my_campaigns = Campaign.query.filter_by(user_id=current_user.id).order_by(Campaign.created_at.desc()).all()

    for campaign in my_campaigns:
        if campaign.goal_amount and campaign.goal_amount > 0:
            campaign.percent = min((campaign.current_amount / campaign.goal_amount) * 100, 100)
        else:
            campaign.percent = 0

    my_contributions = Contribution.query.filter_by(user_id=current_user.id).order_by(
        Contribution.contribution_date.desc()
    ).all()
    for contrib in my_contributions:
        contrib.campaign_info = Campaign.query.get(contrib.campaign_id)

    my_wishlist = Wishlist.query.filter_by(user_id=current_user.id).order_by(Wishlist.added_at.desc()).all()
    for w in my_wishlist:
        w.campaign_info = Campaign.query.get(w.campaign_id)

    my_notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).all()

    return render_template(
        "dashboard.html",
        campaigns=my_campaigns,
        my_contributions=my_contributions,
        my_wishlist=my_wishlist,
        my_notifications=my_notifications
    )



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)