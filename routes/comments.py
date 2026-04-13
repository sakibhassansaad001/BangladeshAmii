from flask import Blueprint, redirect, url_for, request
from flask_login import login_required, current_user
from models import db, Comment, CommentVote, Campaign, Notification

comments_bp = Blueprint('comments', __name__)


def create_notification(user_id, title, message, category, campaign_id=None):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        category=category,
        campaign_id=campaign_id
    )
    db.session.add(notification)


@comments_bp.route('/campaign/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    content = request.form.get('content', '').strip()
    if not content:
        return redirect(url_for('campaign_details_route', id=id))

    comment = Comment(
        content=content,
        user_id=current_user.id,
        campaign_id=id,
        parent_id=None
    )
    db.session.add(comment)

    campaign = Campaign.query.get_or_404(id)
    if campaign.user_id != current_user.id:
        create_notification(
            user_id=campaign.user_id,
            title="New comment on your campaign",
            message=f"{current_user.name} commented on '{campaign.title}'.",
            category="comment",
            campaign_id=id
        )

    db.session.commit()
    return redirect(url_for('campaign_details_route', id=id))


@comments_bp.route('/comment/<int:comment_id>/reply', methods=['POST'])
@login_required
def reply_comment(comment_id):
    parent = Comment.query.get_or_404(comment_id)
    content = request.form.get('content', '').strip()
    if not content:
        return redirect(url_for('campaign_details_route', id=parent.campaign_id))

    reply = Comment(
        content=content,
        user_id=current_user.id,
        campaign_id=parent.campaign_id,
        parent_id=comment_id
    )
    db.session.add(reply)

    campaign = Campaign.query.get_or_404(parent.campaign_id)

    if parent.user_id != current_user.id:
        create_notification(
            user_id=parent.user_id,
            title="New reply to your comment",
            message=f"{current_user.name} replied to your comment on '{campaign.title}'.",
            category="comment",
            campaign_id=parent.campaign_id
        )

    if campaign.user_id not in [current_user.id, parent.user_id]:
        create_notification(
            user_id=campaign.user_id,
            title="New reply on your campaign",
            message=f"{current_user.name} replied in the discussion of '{campaign.title}'.",
            category="comment",
            campaign_id=parent.campaign_id
        )

    db.session.commit()
    return redirect(url_for('campaign_details_route', id=parent.campaign_id))


@comments_bp.route('/comment/<int:comment_id>/vote', methods=['POST'])
@login_required
def vote_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    vote_type = request.form.get('vote_type')

    if vote_type not in ['up', 'down']:
        return redirect(url_for('campaign_details_route', id=comment.campaign_id))

    existing_vote = CommentVote.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()

    if existing_vote:
        if existing_vote.vote_type == vote_type:
            db.session.delete(existing_vote)
        else:
            existing_vote.vote_type = vote_type
    else:
        db.session.add(CommentVote(user_id=current_user.id, comment_id=comment_id, vote_type=vote_type))

    db.session.commit()
    return redirect(url_for('campaign_details_route', id=comment.campaign_id))


@comments_bp.route('/comment/<int:comment_id>/pin', methods=['POST'])
@login_required
def pin_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    campaign = Campaign.query.get_or_404(comment.campaign_id)

    if current_user.id == campaign.user_id or current_user.role == 'admin':
        comment.is_pinned = not comment.is_pinned
        db.session.commit()

    return redirect(url_for('campaign_details_route', id=comment.campaign_id))


@comments_bp.route('/comment/<int:comment_id>/edit', methods=['POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != current_user.id:
        return redirect(url_for('campaign_details_route', id=comment.campaign_id))

    new_content = request.form.get('content', '').strip()
    if new_content:
        comment.content = new_content
        comment.is_edited = True
        db.session.commit()

    return redirect(url_for('campaign_details_route', id=comment.campaign_id))


@comments_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    campaign_id = comment.campaign_id

    if comment.user_id == current_user.id or current_user.role == 'admin':
        for reply in Comment.query.filter_by(parent_id=comment_id).all():
            db.session.delete(reply)
        db.session.delete(comment)
        db.session.commit()

    return redirect(url_for('campaign_details_route', id=campaign_id))