from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, db

shop_profile_bp = Blueprint('shop_profile', __name__)

@shop_profile_bp.route('/verkoper/winkelprofiel/<int:user_id>', methods=['GET', 'POST'])
@login_required
def shop_profile(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        import bleach
        about_shop = request.form.get('about_shop')
        contact_info = request.form.get('contact_info')
        # Sta alleen veilige tags en attributen toe
        allowed_tags = ['b','i','u','a','ul','ol','li','p','br','blockquote','code','h1','h2','h3','strong','em']
        allowed_attrs = {'a': ['href', 'title'], 'img': ['src', 'alt']}
        clean_about = bleach.clean(about_shop, tags=allowed_tags, attributes=allowed_attrs, strip=True)
        clean_contact = bleach.clean(contact_info, tags=allowed_tags, attributes=allowed_attrs, strip=True)
        user.about_shop = clean_about
        user.contact_info = clean_contact
        db.session.commit()
        flash('Winkelprofiel bijgewerkt!', 'success')
        return redirect(url_for('shop_profile.shop_profile', user_id=user.id))
    import os
    tinymce_api_key = os.getenv('TINYMCE_API_KEY')
    return render_template('shop_profile.html', user=user, tinymce_api_key=tinymce_api_key)
