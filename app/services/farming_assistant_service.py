import logging
from app.services.gemini_service import GeminiService, GeminiServiceError
from app.services.translation_service import TranslationService

logger = logging.getLogger(__name__)

FARMING_ASSISTANT_SYSTEM_PROMPT = """
You are an expert, friendly AI Agricultural Engineer & Farming Assistant for Valam, specialized in Sri Lankan dry-zone agriculture (especially Vavuniya and Northern/North-Central provinces).
Your role is to provide precise, practical, and highly actionable agricultural calculations and guidance for small, medium, and commercial farmers.

Key Core Capabilities:
1. SEED & DIRECT SEEDING PURCHASE CALCULATIONS:
   - When a farmer mentions their land size (Acres, Hectares, Perches, Sq meters, Sq ft) and whether they are direct seeding or transplanting, ALWAYS calculate:
     a) Exact seed quantity required (kg or grams) including a 15-20% buffer for optimal germination.
     b) Number of standard commercial seed packets/tins to buy (e.g. 50g, 100g, 500g, 1kg, 5kg bags).
     c) Estimated purchase cost in LKR.
     d) Typical direct seeding rates:
        - Maize: 8 - 10 kg / acre
        - Paddy (Direct wet/dry seeding): 30 - 40 kg / acre
        - Tomato (Direct Seeding): 200 - 250 g / acre (vs 120-150 g transplanted)
        - Chilli (Direct Seeding): 400 - 500 g / acre (vs 250-300 g transplanted)
        - Red Onion (Direct Seed): 3.5 - 4.5 kg / acre (or 450 - 500 kg bulb sets)
        - Okra: 3.5 - 4.5 kg / acre
        - Brinjal: 250 - 300 g / acre
        - Bitter Gourd / Snake Gourd: 1.5 - 2.5 kg / acre

2. IRRIGATION & SOLAR PUMP SYSTEM SIZING:
   - For the farmer's land size:
     a) Drip lateral length: 1 acre ≈ 4,000 meters of 16mm lateral tube (assuming 1m row spacing); 0.5 acre ≈ 2,000m.
     b) Daily water requirement (Vavuniya dry zone): 4,000 - 6,000 Liters / acre / day.
     c) Water tank capacity recommended: 5,000L to 10,000L.
     d) Solar Pump Sizing: 1.0 - 1.5 HP DC Submersible/Surface pump with 3-4 solar panels (1.2kW) for up to 1 acre; 2.0 - 3.0 HP for 2+ acres.

3. STAGE-BY-STAGE COMPOST & FERTILIZER ADVICE:
   - Always differentiate between Organic compost/manure and Non-Organic/Chemical fertilizers.
   - Outline the 5 key stages:
     1) Basal / Land Preparation (e.g., 8-10 tons decomposed cow dung/compost + Neem cake / NPK basal)
     2) Vegetative Stage (Vermicompost top-dress, Jeevamrutham 3%, or Urea)
     3) Flowering Stage (Phosphorus-rich wood ash/bone meal or NPK 1:2:1)
     4) Fruiting / Maturation Stage (Potassium-rich organic wash or MOP)
     5) Harvesting Stage

4. TONE & CLARITY:
   - Warm, encouraging, structured with bullet points and bold numbers.
   - Offer safety tips on protective gear when handling any chemical treatments.
   - Mention that farmers can find listed tools, solar pumps, and seeds on Valam Marketplace & Tools Lending!
"""

class FarmingAssistantService:
    """Service handling AI farming queries tailored for Sri Lankan farmers."""

    @classmethod
    def get_advice(cls, question: str, language: str = "English", user_context: dict = None) -> str:
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        context_lines = []
        if user_context and isinstance(user_context, dict):
            profile = user_context.get("profile") or {}
            crops = user_context.get("crops") or []
            page_context = user_context.get("page_context") or {}

            context_lines.append("======================================================================")
            context_lines.append("LIVE FARMER & CROP DATABASE CONTEXT (ALREADY KNOWN - DO NOT RE-ASK):")
            
            if profile:
                context_lines.append(f"• Farmer Profile: {profile.get('full_name', 'Farmer')}")
                context_lines.append(f"  Location: {profile.get('district', 'Vavuniya')}, {profile.get('ds_division', 'Vavuniya Town')} (Sri Lanka)")
                context_lines.append(f"  Category: {profile.get('farming_category', 'Farmer')} | Land Size: {profile.get('land_size', 1.0)} {profile.get('land_size_unit', 'Acres')}")
                context_lines.append(f"  Preferences: Irrigation={profile.get('irrigation_preference', 'Drip Irrigation')} | Fertilizer={profile.get('fertilizer_preference', 'Organic')}")

            if crops and len(crops) > 0:
                context_lines.append(f"\n• Currently Active Cultivated Crops ({len(crops)} crops):")
                for i, c in enumerate(crops, 1):
                    days_str = f", {c['days_after_planting']} days after planting" if c.get('days_after_planting') is not None else ""
                    context_lines.append(
                        f"  [{i}] {c.get('crop_name')} (Variety: {c.get('variety', 'Standard')}{days_str})"
                        f" - Current Stage: {c.get('current_stage', 'Active')}"
                        f" | Method: {c.get('planting_method', 'Direct Seeding')}"
                        f" | Irrigation: {c.get('irrigation_type', 'Drip')}"
                        f" | Fertilizer: {c.get('fertilizer_preference', 'Organic')}"
                        + (f" | Land: {c.get('land_size')} {c.get('land_size_unit')}" if c.get('land_size') else "")
                    )
            else:
                context_lines.append("• Active Crops: None currently registered in crop tracker.")

            if page_context:
                context_lines.append(f"\n• Current User Screen/Page Context: {page_context}")
                focused_crop = page_context.get("focused_crop") if isinstance(page_context, dict) else None
                if focused_crop:
                    context_lines.append("\n• FOCUSED CROP FROM USER CLICK:")
                    context_lines.append(f"  The farmer clicked the AI assistant from the {focused_crop.get('crop_name')} dashboard overview card.")
                    context_lines.append(f"  Focus crop details: {focused_crop}")

            context_lines.append("======================================================================")
            context_lines.append("CRITICAL INSTRUCTIONS FOR CONTEXT-AWARENESS:")
            context_lines.append("1. NEVER ask the farmer what they are growing, when they started, their location, or land size. You ALREADY have their live database records above.")
            context_lines.append("2. Directly tailor your answer to their specific active crop(s), variety, age in days, and current growth stage.")
            context_lines.append("3. If the user asks a general question like 'When do I fertilize?' or 'How much water do I need?', IMMEDIATELY answer for their active crop and current growth stage without asking for clarification.")
            context_lines.append("4. If a focused crop is provided from a dashboard click, answer for that crop first. For example, if the focused crop is Tomato answer tomato questions; if it is Chilli/Chili answer chilli questions.")
            context_lines.append("5. Keep explanations practical, structured, and warm.")
            context_lines.append("======================================================================\n")

        context_block = "\n".join(context_lines) if context_lines else ""

        prompt = f"""{context_block}
Farmer Question: "{question.strip()}"

Please answer as the Valam Agricultural AI Assistant. Follow all instructions and directly use the farmer's active crop context.
Give clear, actionable step-by-step guidance.
"""
        # Get raw response from Gemini
        response_text = GeminiService.generate_content(
            prompt=prompt,
            system_instruction=FARMING_ASSISTANT_SYSTEM_PROMPT,
            temperature=0.5
        )

        # Translate to desired language if needed
        final_answer = TranslationService.translate(response_text, target_language=language)
        return final_answer
