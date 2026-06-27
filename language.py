"""
EvaMusic — Language / i18n Module
Supports: English (en), Hindi (hi), Bengali (bn), Assamese (as)
No external dependencies — pure Python dictionary-based translations.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# SUPPORTED LANGUAGES
# ═══════════════════════════════════════════════════════════════════════════════

SUPPORTED_LANGUAGES = {
    "en": {
        "name": "English",
        "native": "English",
        "flag": "🇬🇧",
        "dir": "ltr"
    },
    "hi": {
        "name": "Hindi",
        "native": "हिन्दी",
        "flag": "🇮🇳",
        "dir": "ltr"
    },
    "bn": {
        "name": "Bengali",
        "native": "বাংলা",
        "flag": "🇧🇩",
        "dir": "ltr"
    },
    "as": {
        "name": "Assamese",
        "native": "অসমীয়া",
        "flag": "🇮🇳",
        "dir": "ltr"
    }
}

DEFAULT_LANGUAGE = "en"

# ═══════════════════════════════════════════════════════════════════════════════
# TRANSLATION DICTIONARY
# ═══════════════════════════════════════════════════════════════════════════════

TRANSLATIONS = {
    # ── Common / Shared ──
    "Settings": {
        "en": "Settings",
        "hi": "सेटिंग्स",
        "bn": "সেটিংস",
        "as": "ছেটিংছ"
    },
    "Profile": {
        "en": "Profile",
        "hi": "प्रोफ़ाइल",
        "bn": "প্রোফাইল",
        "as": "প্ৰফাইল"
    },
    "Home": {
        "en": "Home",
        "hi": "होम",
        "bn": "হোম",
        "as": "হোম"
    },
    "Search": {
        "en": "Search",
        "hi": "खोजें",
        "bn": "অনুসন্ধান",
        "as": "সন্ধান"
    },
    "Back": {
        "en": "Back",
        "hi": "वापस",
        "bn": "পিছনে",
        "as": "পিছলৈ"
    },
    "Cancel": {
        "en": "Cancel",
        "hi": "रद्द करें",
        "bn": "বাতিল",
        "as": "বাতিল"
    },
    "Save": {
        "en": "Save",
        "hi": "सहेजें",
        "bn": "সংরক্ষণ",
        "as": "সাঁচি থ’ব"
    },
    "Done": {
        "en": "Done",
        "hi": "हो गया",
        "bn": "সম্পন্ন",
        "as": "সম্পন্ন"
    },
    "Close": {
        "en": "Close",
        "hi": "बंद करें",
        "bn": "বন্ধ",
        "as": "বন্ধ"
    },
    "Loading": {
        "en": "Loading…",
        "hi": "लोड हो रहा है…",
        "bn": "লোড হচ্ছে…",
        "as": "লোড হৈ আছে…"
    },
    "Error": {
        "en": "Error",
        "hi": "त्रुटि",
        "bn": "ত্রুটি",
        "as": "ত্ৰুটি"
    },
    "Success": {
        "en": "Success",
        "hi": "सफल",
        "bn": "সফল",
        "as": "সফল"
    },

    # ── Settings Page ──
    "Account": {
        "en": "Account",
        "hi": "खाता",
        "bn": "অ্যাকাউন্ট",
        "as": "একাউণ্ট"
    },
    "Log In with Google": {
        "en": "Log In with Google",
        "hi": "Google से लॉग इन करें",
        "bn": "Google দিয়ে লগ ইন করুন",
        "as": "Google-ৰ সৈতে লগ ইন কৰক"
    },
    "Edit Profile": {
        "en": "Edit Profile",
        "hi": "प्रोफ़ाइल संपादित करें",
        "bn": "প্রোফাইল সম্পাদনা",
        "as": "প্ৰফাইল সম্পাদনা"
    },
    "Name, avatar, bio": {
        "en": "Name, avatar, bio",
        "hi": "नाम, अवतार, बायो",
        "bn": "নাম, অবতার, বায়ো",
        "as": "নাম, অৱতাৰ, বায়ো"
    },
    "Log Out": {
        "en": "Log Out",
        "hi": "लॉग आउट",
        "bn": "লগ আউট",
        "as": "লগ আউট"
    },
    "Sign out of your account": {
        "en": "Sign out of your account",
        "hi": "अपने खाते से साइन आउट करें",
        "bn": "আপনার অ্যাকাউন্ট থেকে সাইন আউট করুন",
        "as": "আপোনাৰ একাউণ্টৰ পৰা ছাইন আউট কৰক"
    },
    "Appearance": {
        "en": "Appearance",
        "hi": "दिखावट",
        "bn": "অ্যাপিয়ারেন্স",
        "as": "ৰূপ"
    },
    "Theme": {
        "en": "Theme",
        "hi": "थीम",
        "bn": "থিম",
        "as": "থীম"
    },
    "Dark, Light, AMOLED": {
        "en": "Dark, Light, AMOLED",
        "hi": "डार्क, लाइट, AMOLED",
        "bn": "ডার্ক, লাইট, AMOLED",
        "as": "ডাৰ্ক, লাইট, AMOLED"
    },
    "Accent Color": {
        "en": "Accent Color",
        "hi": "एक्सेंट रंग",
        "bn": "অ্যাকসেন্ট রঙ",
        "as": "এক্সেণ্ট ৰং"
    },
    "App highlight color": {
        "en": "App highlight color",
        "hi": "ऐप हाइलाइट रंग",
        "bn": "অ্যাপ হাইলাইট রঙ",
        "as": "এপ হাইলাইট ৰং"
    },
    "Display Language": {
        "en": "Display Language",
        "hi": "प्रदर्शन भाषा",
        "bn": "প্রদর্শনের ভাষা",
        "as": "প্ৰদৰ্শনৰ ভাষা"
    },
    "App interface language": {
        "en": "App interface language",
        "hi": "ऐप इंटरफ़ेस भाषा",
        "bn": "অ্যাপ ইন্টারফেস ভাষা",
        "as": "এপ ইণ্টাৰফেচ ভাষা"
    },
    "Playback": {
        "en": "Playback",
        "hi": "प्लेबैक",
        "bn": "প্লেব্যাক",
        "as": "প্লেবেক"
    },
    "Skip Duration": {
        "en": "Skip Duration",
        "hi": "स्किप अवधि",
        "bn": "স্কিপ সময়কাল",
        "as": "স্কিপ সময়সীমা"
    },
    "Seek forward/backward time": {
        "en": "Seek forward/backward time",
        "hi": "आगे/पीछे खोजने का समय",
        "bn": "এগিয়ে/পিছনে যাওয়ার সময়",
        "as": "আগলৈ/পিছলৈ যোৱাৰ সময়"
    },
    "Music Server": {
        "en": "Music Server",
        "hi": "म्यूजिक सर्वर",
        "bn": "মিউজিক সার্ভার",
        "as": "মিউজিক চাৰ্ভাৰ"
    },
    "Server": {
        "en": "Server",
        "hi": "सर्वर",
        "bn": "সার্ভার",
        "as": "চাৰ্ভাৰ"
    },
    "Select streaming server": {
        "en": "Select streaming server",
        "hi": "स्ट्रीमिंग सर्वर चुनें",
        "bn": "স্ট্রিমিং সার্ভার নির্বাচন করুন",
        "as": "ষ্ট্ৰীমিং চাৰ্ভাৰ বাছনি কৰক"
    },
    "Music Language": {
        "en": "Music Language",
        "hi": "म्यूजिक भाषा",
        "bn": "মিউজিক ভাষা",
        "as": "মিউজিক ভাষা"
    },
    "Preferred song languages": {
        "en": "Preferred song languages",
        "hi": "पसंदीदा गाने की भाषाएँ",
        "bn": "পছন্দের গানের ভাষা",
        "as": "পচন্দৰ গানৰ ভাষা"
    },
    "Quality": {
        "en": "Quality",
        "hi": "गुणवत्ता",
        "bn": "গুণমান",
        "as": "গুণমান"
    },
    "Streaming Quality": {
        "en": "Streaming Quality",
        "hi": "स्ट्रीमिंग गुणवत्ता",
        "bn": "স্ট্রিমিং গুণমান",
        "as": "ষ্ট্ৰীমিং গুণমান"
    },
    "Wi-Fi streaming": {
        "en": "Wi-Fi streaming",
        "hi": "Wi-Fi स्ट्रीमिंग",
        "bn": "Wi-Fi স্ট্রিমিং",
        "as": "Wi-Fi ষ্ট্ৰীমিং"
    },
    "Download Quality": {
        "en": "Download Quality",
        "hi": "डाउनलोड गुणवत्ता",
        "bn": "ডাউনলোড গুণমান",
        "as": "ডাউনলোড গুণমান"
    },
    "Offline music quality": {
        "en": "Offline music quality",
        "hi": "ऑफलाइन म्यूजिक गुणवत्ता",
        "bn": "অফলাইন মিউজিক গুণমান",
        "as": "অফলাইন মিউজিক গুণমান"
    },
    "Help & Support": {
        "en": "Help & Support",
        "hi": "सहायता और समर्थन",
        "bn": "সাহায্য ও সহায়তা",
        "as": "সহায় আৰু সমৰ্থন"
    },
    "Help Center": {
        "en": "Help Center",
        "hi": "सहायता केंद्र",
        "bn": "সাহায্য কেন্দ্র",
        "as": "সহায় কেন্দ্ৰ"
    },
    "FAQs and troubleshooting": {
        "en": "FAQs and troubleshooting",
        "hi": "सामान्य प्रश्न और समस्या निवारण",
        "bn": "FAQ এবং সমস্যা সমাধান",
        "as": "FAQ আৰু সমস্যা সমাধান"
    },
    "Telegram": {
        "en": "Telegram",
        "hi": "टेलीग्राम",
        "bn": "টেলিগ্রাম",
        "as": "টেলিগ্ৰাম"
    },
    "About": {
        "en": "About",
        "hi": "के बारे में",
        "bn": "সম্পর্কে",
        "as": "সম্পৰ্কে"
    },
    "About EvaMusic": {
        "en": "About EvaMusic",
        "hi": "EvaMusic के बारे में",
        "bn": "EvaMusic সম্পর্কে",
        "as": "EvaMusic সম্পৰ্কে"
    },
    "Privacy Policy": {
        "en": "Privacy Policy",
        "hi": "गोपनीयता नीति",
        "bn": "গোপনীয়তা নীতি",
        "as": "গোপনীয়তা নীতি"
    },
    "Version": {
        "en": "Version",
        "hi": "संस्करण",
        "bn": "সংস্করণ",
        "as": "সংস্কৰণ"
    },

    # ── Theme Modal ──
    "Select Theme": {
        "en": "Select Theme",
        "hi": "थीम चुनें",
        "bn": "থিম নির্বাচন করুন",
        "as": "থীম বাছনি কৰক"
    },
    "Dark": {
        "en": "Dark",
        "hi": "डार्क",
        "bn": "ডার্ক",
        "as": "ডাৰ্ক"
    },
    "Light": {
        "en": "Light",
        "hi": "लाइट",
        "bn": "লাইট",
        "as": "লাইট"
    },
    "AMOLED": {
        "en": "AMOLED",
        "hi": "AMOLED",
        "bn": "AMOLED",
        "as": "AMOLED"
    },

    # ── Accent Color Modal ──
    "Accent Color": {
        "en": "Accent Color",
        "hi": "एक्सेंट रंग",
        "bn": "অ্যাকসেন্ট রঙ",
        "as": "এক্সেণ্ট ৰং"
    },
    "Green": {
        "en": "Green",
        "hi": "हरा",
        "bn": "সবুজ",
        "as": "সেউজীয়া"
    },
    "Red": {
        "en": "Red",
        "hi": "लाल",
        "bn": "লাল",
        "as": "ৰঙা"
    },
    "Teal": {
        "en": "Teal",
        "hi": "टील",
        "bn": "টিল",
        "as": "টিল"
    },
    "Blue": {
        "en": "Blue",
        "hi": "नीला",
        "bn": "নীল",
        "as": "নীলা"
    },
    "Mint": {
        "en": "Mint",
        "hi": "पुदीना",
        "bn": "পুদিনা",
        "as": "পুদিনা"
    },
    "Purple": {
        "en": "Purple",
        "hi": "बैंगनी",
        "bn": "বেগুনি",
        "as": "বেঙুনীয়া"
    },
    "Yellow": {
        "en": "Yellow",
        "hi": "पीला",
        "bn": "হলুদ",
        "as": "হালধীয়া"
    },
    "Orange": {
        "en": "Orange",
        "hi": "नारंगी",
        "bn": "কমলা",
        "as": "কমলা"
    },

    # ── Server Modal ──
    "Select Server": {
        "en": "Select Server",
        "hi": "सर्वर चुनें",
        "bn": "সার্ভার নির্বাচন করুন",
        "as": "চাৰ্ভাৰ বাছনি কৰক"
    },
    "Fast": {
        "en": "Fast",
        "hi": "तेज़",
        "bn": "দ্রুত",
        "as": "দ্ৰুত"
    },
    "Backup": {
        "en": "Backup",
        "hi": "बैकअप",
        "bn": "ব্যাকআপ",
        "as": "বেকআপ"
    },

    # ── Skip Duration Modal ──
    "Skip Duration": {
        "en": "Skip Duration",
        "hi": "स्किप अवधि",
        "bn": "স্কিপ সময়কাল",
        "as": "স্কিপ সময়সীমা"
    },
    "seconds": {
        "en": "seconds",
        "hi": "सेकंड",
        "bn": "সেকেন্ড",
        "as": "ছেকেণ্ড"
    },

    # ── Quality Modal ──
    "Streaming Quality": {
        "en": "Streaming Quality",
        "hi": "स्ट्रीमिंग गुणवत्ता",
        "bn": "স্ট্রিমিং গুণমান",
        "as": "ষ্ট্ৰীমিং গুণমান"
    },
    "Download Quality": {
        "en": "Download Quality",
        "hi": "डाउनलोड गुणवत्ता",
        "bn": "ডাউনলোড গুণমান",
        "as": "ডাউনলোড গুণমান"
    },
    "Low": {
        "en": "Low",
        "hi": "कम",
        "bn": "কম",
        "as": "কম"
    },
    "Medium": {
        "en": "Medium",
        "hi": "मध्यम",
        "bn": "মাঝারি",
        "as": "মধ্যম"
    },
    "High": {
        "en": "High",
        "hi": "उच्च",
        "bn": "উচ্চ",
        "as": "উচ্চ"
    },
    "Lossless": {
        "en": "Lossless",
        "hi": "लॉसलेस",
        "bn": "লসলেস",
        "as": "লছলেছ"
    },

    # ── Profile Page ──
    "My Favorites": {
        "en": "My Favorites",
        "hi": "मेरे पसंदीदा",
        "bn": "আমার পছন্দ",
        "as": "মোৰ পচন্দ"
    },
    "Listening History": {
        "en": "Listening History",
        "hi": "सुनने का इतिहास",
        "bn": "শোনার ইতিহাস",
        "as": "শুনাৰ ইতিহাস"
    },
    "My Playlists": {
        "en": "My Playlists",
        "hi": "मेरी प्लेलिस्ट",
        "bn": "আমার প্লেলিস্ট",
        "as": "মোৰ প্লেলিষ্ট"
    },
    "Favorites": {
        "en": "Favorites",
        "hi": "पसंदीदा",
        "bn": "পছন্দ",
        "as": "পচন্দ"
    },
    "Playlists": {
        "en": "Playlists",
        "hi": "प्लेलिस्ट",
        "bn": "প্লেলিস্ট",
        "as": "প্লেলিষ্ট"
    },
    "Plays": {
        "en": "Plays",
        "hi": "प्ले",
        "bn": "প্লে",
        "as": "প্লে"
    },
    "Hours": {
        "en": "Hours",
        "hi": "घंटे",
        "bn": "ঘণ্টা",
        "as": "ঘণ্টা"
    },
    "Recently Played": {
        "en": "Recently Played",
        "hi": "हाल ही में बजाया",
        "bn": "সম্প্রতি বাজানো",
        "as": "শেহতীয়াকৈ বজোৱা"
    },
    "See All": {
        "en": "See All",
        "hi": "सभी देखें",
        "bn": "সব দেখুন",
        "as": "সকলো চাওক"
    },
    "Top Favorites": {
        "en": "Top Favorites",
        "hi": "शीर्ष पसंदीदा",
        "bn": "শীর্ষ পছন্দ",
        "as": "শীৰ্ষ পচন্দ"
    },
    "Music lover": {
        "en": "Music lover",
        "hi": "संगीत प्रेमी",
        "bn": "সংগীত প্রেমী",
        "as": "সংগীত প্ৰেমী"
    },
    "Edit Profile": {
        "en": "Edit Profile",
        "hi": "प्रोफ़ाइल संपादित करें",
        "bn": "প্রোফাইল সম্পাদনা",
        "as": "প্ৰফাইল সম্পাদনা"
    },
    "Share": {
        "en": "Share",
        "hi": "साझा करें",
        "bn": "শেয়ার",
        "as": "শেয়াৰ"
    },
    "songs": {
        "en": "songs",
        "hi": "गाने",
        "bn": "গান",
        "as": "গান"
    },

    # ── Auth / Login ──
    "Please log in to edit your profile": {
        "en": "Please log in to edit your profile",
        "hi": "कृपया अपनी प्रोफ़ाइल संपादित करने के लिए लॉग इन करें",
        "bn": "আপনার প্রোফাইল সম্পাদনা করতে লগ ইন করুন",
        "as": "আপোনাৰ প্ৰফাইল সম্পাদনা কৰিবলৈ লগ ইন কৰক"
    },
    "Are you sure you want to log out?": {
        "en": "Are you sure you want to log out?",
        "hi": "क्या आप लॉग आउट करना चाहते हैं?",
        "bn": "আপনি কি লগ আউট করতে চান?",
        "as": "আপুনি লগ আউট কৰিব বিচাৰেনে?"
    },
    "Logged out successfully": {
        "en": "Logged out successfully",
        "hi": "सफलतापूर्वक लॉग आउट",
        "bn": "সফলভাবে লগ আউট হয়েছে",
        "as": "সফলতাৰে লগ আউট হ’ল"
    },
    "Logout failed": {
        "en": "Logout failed",
        "hi": "लॉग आउट विफल",
        "bn": "লগ আউট ব্যর্থ",
        "as": "লগ আউট বিফল"
    },

    # ── Toast Messages ──
    "Switched to": {
        "en": "Switched to",
        "hi": "पर स्विच किया",
        "bn": "সুইচ করা হয়েছে",
        "as": "সুইচ কৰা হ’ল"
    },
    "Skip duration": {
        "en": "Skip duration",
        "hi": "स्किप अवधि",
        "bn": "স্কিপ সময়কাল",
        "as": "স্কিপ সময়সীমা"
    },
    "Theme": {
        "en": "Theme",
        "hi": "थीम",
        "bn": "থিম",
        "as": "থীম"
    },
    "Accent": {
        "en": "Accent",
        "hi": "एक्सेंट",
        "bn": "অ্যাকসেন্ট",
        "as": "এক্সেণ্ট"
    },
    "Streaming": {
        "en": "Streaming",
        "hi": "स्ट्रीमिंग",
        "bn": "স্ট্রিমিং",
        "as": "ষ্ট্ৰীমিং"
    },
    "Download": {
        "en": "Download",
        "hi": "डाउनलोड",
        "bn": "ডাউনলোড",
        "as": "ডাউনলোড"
    },
    "Select a song first": {
        "en": "Select a song first",
        "hi": "पहले एक गाना चुनें",
        "bn": "প্রথমে একটি গান নির্বাচন করুন",
        "as": "প্ৰথমে এটা গান বাছনি কৰক"
    },
    "Tap to play": {
        "en": "Tap ▶ to play",
        "hi": "बजाने के लिए ▶ दबाएं",
        "bn": "বাজাতে ▶ ট্যাপ করুন",
        "as": "বজাবলৈ ▶ টেপ কৰক"
    },
    "Playback error": {
        "en": "Playback error — try again",
        "hi": "प्लेबैक त्रुटि — पुनः प्रयास करें",
        "bn": "প্লেব্যাক ত্রুটি — আবার চেষ্টা করুন",
        "as": "প্লেবেক ত্ৰুটি — পুনৰ চেষ্টা কৰক"
    },
    "Song unavailable": {
        "en": "Song unavailable",
        "hi": "गाना उपलब्ध नहीं",
        "bn": "গান উপলব্ধ নয়",
        "as": "গান উপলব্ধ নহয়"
    },
    "Playback failed": {
        "en": "Playback failed",
        "hi": "प्लेबैक विफल",
        "bn": "প্লেব্যাক ব্যর্থ",
        "as": "প্লেবেক বিফল"
    },
    "Added to favorites": {
        "en": "❤️ Added to favorites",
        "hi": "❤️ पसंदीदा में जोड़ा गया",
        "bn": "❤️ পছন্দে যোগ করা হয়েছে",
        "as": "❤️ পচন্দত যোগ কৰা হ’ল"
    },
    "Removed from favorites": {
        "en": "💔 Removed from favorites",
        "hi": "💔 पसंदीदा से हटाया गया",
        "bn": "💔 পছন্দ থেকে সরানো হয়েছে",
        "as": "💔 পচন্দৰ পৰা আঁতৰোৱা হ’ল"
    },
    "Network error": {
        "en": "Network error",
        "hi": "नेटवर्क त्रुटि",
        "bn": "নেটওয়ার্ক ত্রুটি",
        "as": "নেটৱৰ্ক ত্ৰুটি"
    },
    "Link copied": {
        "en": "🔗 Link copied!",
        "hi": "🔗 लिंक कॉपी किया!",
        "bn": "🔗 লিঙ্ক কপি করা হয়েছে!",
        "as": "🔗 লিংক কপি কৰা হ’ল!"
    },
    "Loading more songs": {
        "en": "Loading more songs…",
        "hi": "और गाने लोड हो रहे हैं…",
        "bn": "আরও গান লোড হচ্ছে…",
        "as": "আৰু গান লোড হৈ আছে…"
    },
    "Restarting queue": {
        "en": "🔁 Restarting queue",
        "hi": "🔁 कतार पुनः आरंभ",
        "bn": "🔁 কিউ পুনরায় শুরু",
        "as": "🔁 কিউ পুনৰ আৰম্ভ"
    },
    "Shuffle on": {
        "en": "Shuffle on",
        "hi": "शफल चालू",
        "bn": "শাফল চালু",
        "as": "শাফল অন"
    },
    "Shuffle off": {
        "en": "Shuffle off",
        "hi": "शफल बंद",
        "bn": "শাফল বন্ধ",
        "as": "শাফল অফ"
    },
    "Repeat off": {
        "en": "Repeat off",
        "hi": "दोहराना बंद",
        "bn": "রিপিট বন্ধ",
        "as": "ৰিপিট অফ"
    },
    "Repeat all": {
        "en": "Repeat all",
        "hi": "सभी दोहराएं",
        "bn": "সব রিপিট করুন",
        "as": "সকলো ৰিপিট কৰক"
    },
    "Repeat one": {
        "en": "Repeat one",
        "hi": "एक दोहराएं",
        "bn": "একটি রিপিট করুন",
        "as": "এটা ৰিপিট কৰক"
    },
    "Retrying": {
        "en": "Retrying…",
        "hi": "पुनः प्रयास…",
        "bn": "পুনরায় চেষ্টা…",
        "as": "পুনৰ চেষ্টা…"
    },
    "No audio URL available": {
        "en": "No audio URL available",
        "hi": "कोई ऑडियो URL उपलब्ध नहीं",
        "bn": "কোনো অডিও URL উপলব্ধ নয়",
        "as": "কোনো অডিও URL উপলব্ধ নহয়"
    },
    "Song data not found": {
        "en": "Song data not found",
        "hi": "गाने का डेटा नहीं मिला",
        "bn": "গানের ডেটা পাওয়া যায়নি",
        "as": "গানৰ ডেটা পোৱা নগ’ল"
    },

    # ── Player Overlay ──
    "Now Playing": {
        "en": "Now Playing",
        "hi": "अब बज रहा है",
        "bn": "এখন বাজছে",
        "as": "এতিয়া বাজিছে"
    },
    "Queue": {
        "en": "Queue",
        "hi": "कतार",
        "bn": "কিউ",
        "as": "কিউ"
    },
    "Sleep": {
        "en": "Sleep",
        "hi": "नींद",
        "bn": "ঘুম",
        "as": "নিদ্ৰা"
    },
    "Sleep timer coming soon": {
        "en": "Sleep timer coming soon",
        "hi": "स्लीप टाइमर जल्द आ रहा है",
        "bn": "স্লিপ টাইমার শীঘ্রই আসছে",
        "as": "চ্লিপ টাইমাৰ সোনকালে আহিছে"
    },
    "Saved": {
        "en": "Saved!",
        "hi": "सहेजा गया!",
        "bn": "সংরক্ষিত!",
        "as": "সাঁচি থোৱা হ’ল!"
    },
    "Finding related songs": {
        "en": "Finding related songs…",
        "hi": "संबंधित गाने खोज रहे हैं…",
        "bn": "সম্পর্কিত গান খুঁজছে…",
        "as": "সম্পৰ্কিত গান বিচাৰিছে…"
    },
    "Play a song to see related tracks": {
        "en": "Play a song to see related tracks",
        "hi": "संबंधित ट्रैक देखने के लिए एक गाना बजाएं",
        "bn": "সম্পর্কিত ট্র্যাক দেখতে একটি গান বাজান",
        "as": "সম্পৰ্কিত ট্ৰেক চাবলৈ এটা গান বজাওক"
    },
    "No related songs found": {
        "en": "No related songs found",
        "hi": "कोई संबंधित गाना नहीं मिला",
        "bn": "কোনো সম্পর্কিত গান পাওয়া যায়নি",
        "as": "কোনো সম্পৰ্কিত গান পোৱা নগ’ল"
    },
    "Up Next": {
        "en": "Up Next",
        "hi": "अगला",
        "bn": "পরবর্তী",
        "as": "পৰৱৰ্তী"
    },


    # ── Home Page ──
    "Good morning": {
        "en": "Good morning",
        "hi": "शुभ प्रभात",
        "bn": "শুভ সকাল",
        "as": "সুপ্ৰভাত"
    },
    "Good afternoon": {
        "en": "Good afternoon",
        "hi": "शुभ दोपहर",
        "bn": "শুভ অপরাহ্ণ",
        "as": "শুভ অপৰাহ্ণ"
    },
    "Good evening": {
        "en": "Good evening",
        "hi": "शुभ संध्या",
        "bn": "শুভ সন্ধ্যা",
        "as": "শুভ সন্ধ্যা"
    },
    "Discover your next favorite song": {
        "en": "Discover your next favorite song",
        "hi": "अपना अगला पसंदीदा गाना खोजें",
        "bn": "আপনার পরবর্তী প্রিয় গানটি আবিষ্কার করুন",
        "as": "আপোনাৰ পৰৱৰ্তী পচন্দৰ গানটো বিচাৰক"
    },
    "History": {
        "en": "History",
        "hi": "इतिहास",
        "bn": "ইতিহাস",
        "as": "ইতিহাস"
    },
    "Trending Now": {
        "en": "Trending Now",
        "hi": "अभी ट्रेंडिंग",
        "bn": "এখন ট্রেন্ডিং",
        "as": "এতিয়া ট্ৰেণ্ডিং"
    },
    "Top Charts": {
        "en": "Top Charts",
        "hi": "शीर्ष चार्ट",
        "bn": "শীর্ষ চার্ট",
        "as": "শীৰ্ষ চাৰ্ট"
    },
    "New Releases": {
        "en": "New Releases",
        "hi": "नई रिलीज़",
        "bn": "নতুন রিলিজ",
        "as": "নতুন ৰিলিজ"
    },
    "Popular Artists": {
        "en": "Popular Artists",
        "hi": "लोकप्रिय कलाकार",
        "bn": "জনপ্রিয় শিল্পী",
        "as": "জনপ্ৰিয় শিল্পী"
    },
    "Browse by Mood": {
        "en": "Browse by Mood",
        "hi": "मूड के अनुसार ब्राउज़ करें",
        "bn": "মুড অনুযায়ী ব্রাউজ করুন",
        "as": "মুড অনুসৰি ব্ৰাউজ কৰক"
    },
    "Romantic": {
        "en": "Romantic",
        "hi": "रोमांटिक",
        "bn": "রোমান্টিক",
        "as": "ৰোমান্টিক"
    },
    "Party": {
        "en": "Party",
        "hi": "पार्टी",
        "bn": "পার্টি",
        "as": "পাৰ্টি"
    },
    "Sad": {
        "en": "Sad",
        "hi": "उदास",
        "bn": "দুঃখজনক",
        "as": "দুখীয়া"
    },
    "Workout": {
        "en": "Workout",
        "hi": "वर्कआउट",
        "bn": "ওয়ার্কআউট",
        "as": "ৱৰ্কআউট"
    },
    "Focus": {
        "en": "Focus",
        "hi": "फोकस",
        "bn": "ফোকাস",
        "as": "ফোকাছ"
    },
    "Sleep": {
        "en": "Sleep",
        "hi": "नींद",
        "bn": "ঘুম",
        "as": "নিদ্ৰা"
    },
    "Devotional": {
        "en": "Devotional",
        "hi": "भक्ति",
        "bn": "ভক্তিমূলক",
        "as": "ভক্তিমূলক"
    },
    "Classical": {
        "en": "Classical",
        "hi": "शास्त्रीय",
        "bn": "শাস্ত্রীয়",
        "as": "শাস্ত্ৰীয়"
    },
    "Daily Mix": {
        "en": "Daily Mix",
        "hi": "डेली मिक्स",
        "bn": "ডেইলি মিক্স",
        "as": "দৈনিক মিক্স"
    },
    "Made for you": {
        "en": "Made for you",
        "hi": "आपके लिए बनाया गया",
        "bn": "আপনার জন্য তৈরি",
        "as": "আপোনাৰ বাবে নিৰ্মিত"
    },
    "Recommended for You": {
        "en": "Recommended for You",
        "hi": "आपके लिए सुझाव",
        "bn": "আপনার জন্য সুপারিশ",
        "as": "আপোনাৰ বাবে পৰামৰ্শ"
    },

    
    # ── Additional Home Page ──
    "Morning": {
        "en": "Morning",
        "hi": "प्रभात",
        "bn": "সকাল",
        "as": "প্ৰভাত"
    },
    "Afternoon": {
        "en": "Afternoon",
        "hi": "दोपहर",
        "bn": "অপরাহ্ণ",
        "as": "অপৰাহ্ণ"
    },
    "Evening": {
        "en": "Evening",
        "hi": "संध्या",
        "bn": "সন্ধ্যা",
        "as": "সন্ধ্যা"
    },
    "Quick Play": {
        "en": "Quick Play",
        "hi": "क्विक प्ले",
        "bn": "কুইক প্লে",
        "as": "কুইক প্লে"
    },
    "Because You Liked": {
        "en": "Because You Liked",
        "hi": "क्योंकि आपने पसंद किया",
        "bn": "কারণ আপনি পছন্দ করেছেন",
        "as": "কাৰণ আপুনি পচন্দ কৰিছে"
    },
    "Recommended": {
        "en": "Recommended",
        "hi": "सुझाव",
        "bn": "সুপারিশ",
        "as": "পৰামৰ্শ"
    },
    "Artists": {
        "en": "Artists",
        "hi": "कलाकार",
        "bn": "শিল্পী",
        "as": "শিল্পী"
    },
    "Recommended For You": {
        "en": "Recommended For You",
        "hi": "आपके लिए सुझाव",
        "bn": "আপনার জন্য সুপারিশ",
        "as": "আপোনাৰ বাবে পৰামৰ্শ"
    },
    "No artists found": {
        "en": "No artists found",
        "hi": "कोई कलाकार नहीं मिला",
        "bn": "কোনো শিল্পী পাওয়া যায়নি",
        "as": "কোনো শিল্পী পোৱা নগ’ল"
    },
    "Start listening to build your Usuals!": {
        "en": "Start listening to build your Usuals!",
        "hi": "अपने Usuals बनाने के लिए सुनना शुरू करें!",
        "bn": "আপনার Usuals তৈরি করতে শুনতে শুরু করুন!",
        "as": "আপোনাৰ Usuals নিৰ্মাণ কৰিবলৈ শুনা আৰম্ভ কৰক!"
    },
    "Punjabi": {
        "en": "Punjabi",
        "hi": "पंजाबी",
        "bn": "পাঞ্জাবি",
        "as": "পঞ্জাবী"
    },
    "Tamil": {
        "en": "Tamil",
        "hi": "तमिल",
        "bn": "তামিল",
        "as": "তামিল"
    },
    "Telugu": {
        "en": "Telugu",
        "hi": "तेलुगु",
        "bn": "তেলুগু",
        "as": "তেলেগু"
    },
    "Unknown": {
        "en": "Unknown",
        "hi": "अज्ञात",
        "bn": "অজানা",
        "as": "অজ্ঞাত"
    },

        # ── Misc ──
    "All": {
        "en": "All",
        "hi": "सभी",
        "bn": "সব",
        "as": "সকলো"
    },
    "English": {
        "en": "English",
        "hi": "English",
        "bn": "English",
        "as": "English"
    },
    "Hindi": {
        "en": "Hindi",
        "hi": "हिन्दी",
        "bn": "হিন্দি",
        "as": "হিন্দী"
    },
    "Bengali": {
        "en": "Bengali",
        "hi": "বাংলা",
        "bn": "বাংলা",
        "as": "বাংলা"
    },
    "Assamese": {
        "en": "Assamese",
        "hi": "অসমীয়া",
        "bn": "অসমীয়া",
        "as": "অসমীয়া"
    },
    "Made with": {
        "en": "Made with",
        "hi": "के साथ बनाया",
        "bn": "দিয়ে তৈরি",
        "as": "ৰ সৈতে নিৰ্মিত"
    },
    "Tap to view profile": {
        "en": "Tap to view profile",
        "hi": "प्रोफ़ाइल देखने के लिए टैप करें",
        "bn": "প্রোফাইল দেখতে ট্যাপ করুন",
        "as": "প্ৰফাইল চাবলৈ টেপ কৰক"
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_text(key: str, lang: str = None) -> str:
    """
    Get translated text for a given key.
    Falls back to English if translation not found.
    Falls back to the key itself if not in dictionary.
    """
    if not lang:
        lang = DEFAULT_LANGUAGE
    lang = lang.lower().strip()
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    entry = TRANSLATIONS.get(key)
    if not entry:
        return key  # fallback: return the key itself

    return entry.get(lang, entry.get(DEFAULT_LANGUAGE, key))


def get_language_name(lang_code: str) -> str:
    """Get the native name of a language."""
    info = SUPPORTED_LANGUAGES.get(lang_code)
    if info:
        return info.get("native", info.get("name", lang_code))
    return lang_code


def get_all_languages():
    """Return list of all supported languages as dicts."""
    return [
        {"code": code, **data}
        for code, data in SUPPORTED_LANGUAGES.items()
    ]


# Short alias — use this in templates: {{ _("Settings") }}
_ = get_text


# ═══════════════════════════════════════════════════════════════════════════════
# FLASK INTEGRATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_user_language(request_obj=None, session_obj=None):
    """
    Determine the user's preferred language.
    Priority:
      1. Session 'lang' key
      2. Cookie 'evamusic_lang'
      3. Browser Accept-Language header
      4. DEFAULT_LANGUAGE
    """
    # 1. Check session
    if session_obj:
        sess_lang = session_obj.get("lang")
        if sess_lang and sess_lang in SUPPORTED_LANGUAGES:
            return sess_lang

    # 2. Check cookie
    if request_obj:
        cookie_lang = request_obj.cookies.get("evamusic_lang")
        if cookie_lang and cookie_lang in SUPPORTED_LANGUAGES:
            return cookie_lang

        # 3. Check Accept-Language header
        accept = request_obj.accept_languages
        if accept:
            best = accept.best_match(list(SUPPORTED_LANGUAGES.keys()))
            if best:
                return best

    return DEFAULT_LANGUAGE


def register_lang_helpers(app):
    """
    Register Jinja2 globals and context processors for language support.
    Call this in your Flask app factory:
        from language import register_lang_helpers
        register_lang_helpers(app)
    """
    from flask import session, request, g

    @app.before_request
    def _set_language():
        g.lang = get_user_language(request, session)
        g.supported_languages = get_all_languages()

    # Jinja2 global: _("key") → translated string
    app.jinja_env.globals.update({
        "_": get_text,
        "get_language_name": get_language_name,
        "SUPPORTED_LANGUAGES": SUPPORTED_LANGUAGES,
        "DEFAULT_LANGUAGE": DEFAULT_LANGUAGE,
    })

    # Context processor: inject current language into all templates
    @app.context_processor
    def _inject_lang():
        return {
            "current_lang": getattr(g, "lang", DEFAULT_LANGUAGE),
            "current_lang_name": get_language_name(getattr(g, "lang", DEFAULT_LANGUAGE)),
        }
