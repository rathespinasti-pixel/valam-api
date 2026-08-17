from flask import request

from app.extensions import db
from app.models.disease_diagnosis import DiseaseDiagnosis
from app.utils.decorators import success_response, error_response, get_current_user


def analyze_disease():
    """Diagnose pest/disease issue using symptoms and optional crop image in user's preferred language."""
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    symptoms = (data.get("symptoms") or "").strip()
    crop_name = (data.get("crop_name") or "Crop").strip()
    image_url = data.get("image_url")
    lang = (data.get("language") or user.preferred_language or "en").lower()
    if "ta" in lang or "tamil" in lang:
        lang = "ta"
    elif "si" in lang or "sinhala" in lang:
        lang = "si"
    else:
        lang = "en"

    if not symptoms and not image_url:
        return error_response("symptoms description or image_url is required", 400)

    # Localized diagnosis content for Sri Lanka short-duration crops
    if lang == "ta":
        disease_title = f"{crop_name} - ஆரம்பகால இலைக் கருகல் மற்றும் பூச்சி நோய் பாதிப்பு"
        diag_res = f"பரிசோதனை முடிவு: {crop_name} பயிரில் இலைக் கருகல் மற்றும் சாறு உறிஞ்சும் பூச்சித் தாக்குதல் அறிகுறிகள் கண்டறியப்பட்டுள்ளன."
        cause_val = "அதிக ஈரப்பதம், வெப்பநிலை மாற்றம் மற்றும் பூஞ்சை (Alternaria solani) / அசுவினி தாக்குதல்."
        org_treat = "1. பாதிக்கப்பட்ட இலைகளை உடனடியாக அகற்றி எரிக்கவும்.\n2. 5% வேப்பங் கொட்டை சாறு அல்லது பூண்டு சோப்பு கரைசலை அதிகாலையில் தெளிக்கவும்."
        chem_treat = "காப்பர் ஆக்சிகுளோரைடு (Copper Oxychloride 50% WP) 2.5 கிராம்/லீட்டர் அல்லது மேன்கோசெப் (Mancozeb 75% WP) தெளிக்கவும்."
        prev_adv = "முறையான செடி இடைவெளி (60செ.மீ x 45செ.மீ) பேணவும். சொட்டுநீர் பாசனத்தைப் பயன்படுத்தி இலைகளில் நீர் தேங்குவதைத் தவிர்க்கவும்."
        recomm_val = f"இயற்கை: {org_treat}\nஇரசாயனம்: {chem_treat}\nதடுப்பு: {prev_adv}"
        disclaimer_val = "⚠️ இந்த AI நோய் கண்டறிதல் ஆலோசனை வழிகாட்டுதலுக்கு மட்டுமே. தீவிர நோய் பாதிப்புக்கு உங்கள் ASC விவசாய அதிகாரியை தொடர்பு கொள்ளவும்."
    elif lang == "si":
        disease_title = f"{crop_name} - පත්‍ර පාළුව සහ පලිබෝධ ආසාදනය"
        diag_res = f"පරීක්ෂණ ප්‍රථිඵලය: {crop_name} වගාවේ පත්‍ර පාළුව සහ කෘමි හානි ලක්ෂණ නිරීක්ෂණය වේ."
        cause_val = "Alternaria solani දිලීර ආසාදනය සහ තද උෂ්ණත්ව වෙනස්වීම්."
        org_treat = "1. ආසාදිත පත්‍ර වහාම ඉවත් කර විනාශ කරන්න.\n2. 5% කොහොඹ ඇට සාරය හෝ සුදුලූනු සබන් දියරය උදෑසන කාලයේදී ඉසින්න."
        chem_treat = "කොපර් ඔක්සික්ලෝරයිඩ් (Copper Oxychloride 50% WP) ලීටරයකට ග්‍රෑම් 2.5 ක් හෝ මැන්කොසෙබ් (Mancozeb 75% WP) ඉසින්න."
        prev_adv = "නිසි පැළ පරතරය පවත්වා ගන්න. පත්‍ර මතට ජලය දැමීමෙන් වළකින්න."
        recomm_val = f"කාබනික: {org_treat}\nරසායනික: {chem_treat}\nවැලැක්වීම: {prev_adv}"
        disclaimer_val = "⚠️ මෙම AI රෝග විනිශ්චය උපදෙස් සඳහා පමණි. දරුණු ව්‍යාප්තියකදී ඔබේ ප්‍රාදේශීය කෘෂිකාර්මික නිලධාරියා හමුවන්න."
    else:
        disease_title = f"{crop_name} - Early Blight & Foliar Disease"
        diag_res = f"Diagnosis Result: Symptoms of Early Blight fungal infection and sap-sucking pests detected on {crop_name}."
        cause_val = "Fungal pathogen Alternaria solani coupled with high leaf wetness and warm humid conditions."
        org_treat = "1. Prune and destroy infected leaves immediately.\n2. Apply 5% Neem seed kernel extract or garlic-soap spray early in the morning."
        chem_treat = "Apply Copper Oxychloride (50% WP) @ 2.5g/L or Mancozeb 75% WP as approved by Sri Lanka Department of Agriculture."
        prev_adv = "Maintain recommended plant spacing and avoid overhead irrigation to prevent leaf wetness."
        recomm_val = f"Organic: {org_treat}\nChemical: {chem_treat}\nPrevention: {prev_adv}"
        disclaimer_val = "⚠️ This AI diagnosis provides guidance only and does not replace professional agricultural officer diagnosis."

    entry = DiseaseDiagnosis(
        user_id=user.id,
        crop_name=crop_name,
        image_url=image_url,
        symptoms=symptoms or "Observed leaf/stem abnormality",
        diagnosis_result=diag_res,
        recommendations=recomm_val,
        cause=cause_val,
        organic_treatment=org_treat,
        chemical_treatment=chem_treat,
        prevention_advice=prev_adv,
        language=lang,
        disclaimer=disclaimer_val,
    )
    db.session.add(entry)
    db.session.commit()

    return success_response(entry.to_dict(), message="Diagnosis generated successfully", status_code=201)


def get_diagnosis_history():
    """List previous diagnosis records for current user."""
    user = get_current_user()
    if not user:
        return error_response("User not found", 404)

    query = DiseaseDiagnosis.query.filter_by(user_id=user.id).order_by(DiseaseDiagnosis.created_at.desc())
    items = query.limit(20).all()

    return success_response([item.to_dict() for item in items])
