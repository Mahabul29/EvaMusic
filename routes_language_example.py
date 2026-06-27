"""
EvaMusic — Language Switch Route (add to your main Flask app)

This shows how to wire the language.py module into your existing app.
"""

from flask import Flask, session, request, make_response, redirect, url_for
from language import register_lang_helpers, SUPPORTED_LANGUAGES, get_text

app = Flask(__name__)
app.secret_key = "your-secret-key-here"  # change this!

# ═══════════════════════════════════════════════════════════════════════════════
# REGISTER LANGUAGE SUPPORT (call this once after creating app)
# ═══════════════════════════════════════════════════════════════════════════════
register_lang_helpers(app)

# ═══════════════════════════════════════════════════════════════════════════════
# LANGUAGE SWITCH ROUTE
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/switch-language/<lang>')
def switch_language(lang):
    """
    Switch the app language and redirect back.
    Usage: /switch-language/hi  → switches to Hindi
    """
    lang = lang.lower().strip()
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"  # fallback

    # Save to session
    session["lang"] = lang

    # Also set a cookie that persists across sessions
    resp = make_response(redirect(request.referrer or url_for("settings")))
    resp.set_cookie("evamusic_lang", lang, max_age=60*60*24*365)  # 1 year

    return resp


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE: Settings route (update your existing one)
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/settings')
def settings():
    # The language is automatically injected into templates via context processor
    # You just need to pass your normal data
    return render_template('settings.html',
        title=get_text("Settings"),
        # ... your other template variables
    )


@app.route('/profile')
def profile():
    # Same for profile page — language is auto-injected
    return render_template('profile.html',
        title=get_text("Profile"),
        profile={...},  # your profile data
        stats={...},     # your stats data
        # ... your other template variables
    )


# ═══════════════════════════════════════════════════════════════════════════════
# OPTIONAL: API endpoint for JS to get translations
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/translations')
def api_translations():
    """Return all translations for the current language as JSON (for JS use)."""
    from flask import g, jsonify
    from language import TRANSLATIONS

    lang = getattr(g, "lang", "en")
    result = {}
    for key, values in TRANSLATIONS.items():
        result[key] = values.get(lang, values.get("en", key))

    return jsonify({"lang": lang, "translations": result})
