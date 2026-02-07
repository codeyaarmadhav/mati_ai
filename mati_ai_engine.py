"""
Mati AI Engine - Report Generation Module
AstroNexus Platform

This module handles AI-powered report generation using Claude API
"""

import os
import json
from typing import Dict, List, Optional
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# =========================================================
# ✅ ADDED: Chart Adapter (NEW API → OLD FORMAT)
# =========================================================

def adapt_chart_if_needed(chart_data: Dict) -> Dict:
    """
    Accepts either:
    1) Old AstroNexus chart format (already supported)
    2) New Birth Chart API format (with birth_details, planets, houses, etc.)

    Returns chart in OLD format so MatiAI works unchanged.
    """

    # If already old format, return as-is
    if "birth_data" in chart_data and "planets" in chart_data:
        return chart_data

    # Otherwise assume NEW API FORMAT
    birth_details = chart_data.get("birth_details", {})
    planets_api = chart_data.get("planets", {})
    houses_api = chart_data.get("houses", {})
    asc_api = chart_data.get("ascendant", {})

    # --- birth_data ---
    birth_data = {
        "date": birth_details.get("utc_time"),
        "latitude": birth_details.get("latitude"),
        "longitude": birth_details.get("longitude"),
        "place": birth_details.get("place_of_birth"),
        "timezone": birth_details.get("timezone"),
    }

    # --- planets ---
    planets = {}
    for name, p in planets_api.items():
        if name == "Ascendant":
            continue

        longitude = p.get("longitude", 0)

        planets[name] = {
            "sidereal": {
                "sign": p.get("sign"),
                "degree_in_sign": round(longitude % 30, 2),
                "nakshatra": p.get("nakshatra") or None
            },
            "house": p.get("house")
        }

    # --- houses ---
    houses_list = []
    for house_no, h in houses_api.items():
        houses_list.append({
            "house": int(house_no),
            "sign": h.get("sign"),
            "planets": h.get("planets", [])
        })

    # --- ascendant ---
    ascendant = {
        "sign": asc_api.get("sign"),
        "degree_in_sign": round((asc_api.get("longitude", 0)) % 30, 2)
    }

    return {
        "birth_data": birth_data,
        "planets": planets,
        "houses": {
            "vedic": {
                "ascendant": ascendant,
                "houses": houses_list
            }
        },
        "dashas": chart_data.get("dashas", {
            "current_dasha": {
                "planet": None,
                "start_date": None,
                "end_date": None,
                "duration_years": None
            }
        }),
        "aspects": []
    }

class MatiAI:
    """
    Mati's AI brain - generates personalized astrological insights
    """
    
    # Mati's personality and guidelines
    SYSTEM_PROMPT = """You are Mati, the AI astrology guide for AstroNexus. You combine ancient Vedic and Western astrological wisdom with modern AI capabilities to provide deep, personalized life guidance.

YOUR PERSONALITY:
- Wise and compassionate, like a knowledgeable mentor
- Culturally sensitive to both Indian and American audiences
- Balanced between traditional wisdom and practical modern advice
- Encouraging and empowering, never fatalistic or fear-mongering
- Clear communicator who explains complex concepts simply
- Respectful of both Vedic (Jyotish) and Western astrology traditions

YOUR APPROACH:
- Provide DETAILED, comprehensive analysis (not quick soundbites)
- Always cite specific astrological factors (planets, houses, aspects, yogas)
- Acknowledge both challenges and opportunities in a balanced way
- Emphasize free will - astrology shows tendencies and timing, not fixed destiny
- Connect ancient wisdom to modern life contexts
- Be specific about timing when relevant (dashas, transits)

LANGUAGE GUIDELINES:
- Write primarily in English
- Use Sanskrit/Hindi terms when appropriate (e.g., Kundli, Graha, Dasha, Nakshatra)
- Always provide brief English translations for Sanskrit terms
- Avoid fortune-teller clichés and dramatic language
- Use "you" to address the person directly and personally

CULTURAL SENSITIVITY:
- Honor both Vedic and Western traditions without favoritism
- Understand that Indian users may be more familiar with Vedic concepts
- American users may need more explanation of Vedic principles
- Be inclusive of all backgrounds, beliefs, and life situations

ETHICAL BOUNDARIES:
- Never make absolute predictions about death, divorce, or disasters
- Frame challenges as opportunities for growth
- Encourage professional help for serious issues (health, mental health)
- Respect that astrology is guidance, not a replacement for medical/legal/financial advice

YOUR MISSION:
Help people understand themselves better, make informed decisions, and navigate life with cosmic awareness and personal empowerment."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Mati AI with Groq API
        
        Args:
            api_key: Groq API key (or uses GROQ_API_KEY env variable)
        """
        self.client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
    
    def generate_birth_chart_report(
        self,
        chart_data: Dict,
        analysis: Dict,
        user_name: Optional[str] = None,
        language: str = "english"
    ) -> str:
        """
        Generate comprehensive birth chart analysis report
        
        Args:
            chart_data: Complete birth chart data from calculator
            analysis: Analyzed patterns, yogas, etc.
            user_name: Optional user's name for personalization
            language: "english" or "hindi"
            
        Returns:
            Detailed birth chart report (2500-3500 words)
        """
        
        # Prepare structured data for the prompt
        chart_summary = self._prepare_chart_summary(chart_data, analysis)
        
        prompt = f"""Generate a comprehensive birth chart analysis report.

{f"USER NAME: {user_name}" if user_name else ""}

BIRTH CHART DATA:
{json.dumps(chart_summary, indent=2)}

Create a detailed, personalized birth chart report with these sections:

1. WELCOME & INTRODUCTION (100-150 words)
   - Warm greeting{f" addressing {user_name}" if user_name else ""}
   - Brief explanation of what birth chart reveals
   - Set empowering, non-fatalistic tone

2. YOUR COSMIC BLUEPRINT (200-300 words)
   - Overview of chart's unique features
   - Balance of elements and modalities
   - Notable planetary placements
   - Overall chart strength and themes

3. SOUL & PERSONALITY (400-500 words)
   - Sun Sign (tropical and sidereal): Core identity, life purpose
   - Moon Sign and Nakshatra: Emotional nature, inner self, mind
   - Ascendant (Lagna): Outer personality, physical tendencies, life approach
   - How these three work together to create your unique self

4. LIFE PURPOSE & DHARMA (300-400 words)
   - Analysis of 9th house and Jupiter (dharma, wisdom, philosophy)
   - Sun's placement for soul mission
   - North Node (Rahu) for karmic direction
   - Spiritual inclinations and growth path

5. CAREER & VOCATION (350-450 words)
   - 10th house analysis (career, public image, achievements)
   - 2nd house (wealth, resources, values)
   - 6th house (daily work, service)
   - Mercury, Saturn, Jupiter placements for work style
   - Suitable career paths based on planetary strengths

6. RELATIONSHIPS & LOVE (350-450 words)
   - 7th house analysis (partnerships, marriage)
   - Venus placement (love, relationships, values)
   - Mars placement (passion, energy, drive)
   - Relationship patterns and compatibility needs
   - Timing of relationships (if relevant from dashas)

7. CURRENT LIFE CHAPTER (300-400 words)
   - Vimshottari Dasha period explanation
   - What the current Maha Dasha planet represents
   - Themes and opportunities in this period
   - Timeline of upcoming Dasha changes

8. YOUR STRENGTHS & GIFTS (250-350 words)
   - Positive yogas identified
   - Strong planetary placements
   - Natural talents and abilities
   - How to leverage these gifts

9. CHALLENGES & GROWTH AREAS (250-350 words)
   - Difficult placements or aspects (framed constructively)
   - Areas requiring conscious effort
   - Karmic lessons to work through
   - Practical remedial suggestions (gemstones, mantras, behavioral changes)

10. YEAR AHEAD PREVIEW (200-300 words)
   - Major transits affecting the chart
   - Opportunities to watch for
   - Timing for important initiatives
   - Months to be cautious or proactive

11. EMPOWERING CONCLUSION (150-200 words)
   - Summarize key themes
   - Reinforce free will and personal power
   - Encouragement for the journey ahead
   - Invitation to explore specific questions

WRITING GUIDELINES:
- Total length: 2500-3500 words
- Use "you" to speak directly to the person
- Cite specific astrological placements (e.g., "Your Sun in Taurus in the 10th house...")
- Explain Sanskrit terms briefly (e.g., "Dasha (planetary period)")
- Balance optimism with realism
- Make it feel personal, not generic
- Use paragraphs, not bullet points
- {f"Write in {language.capitalize()}" if language == "hindi" else "Write in clear English"}

Begin the report now:"""

        # Generate report using Groq
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        
        report = response.choices[0].message.content
        
        return report
    
    def generate_compatibility_report(
        self,
        chart1_data: Dict,
        chart2_data: Dict,
        compatibility_analysis: Dict,
        names: Optional[tuple] = None
    ) -> str:
        """
        Generate relationship compatibility analysis
        
        Args:
            chart1_data: First person's birth chart
            chart2_data: Second person's birth chart
            compatibility_analysis: Ashtakoot scores, synastry aspects
            names: Optional tuple of (name1, name2)
        """
        
        name1, name2 = names if names else ("Person 1", "Person 2")
        
        prompt = f"""Generate a detailed relationship compatibility analysis between {name1} and {name2}.

CHART 1 ({name1}):
{json.dumps(self._prepare_chart_summary(chart1_data), indent=2)}

CHART 2 ({name2}):
{json.dumps(self._prepare_chart_summary(chart2_data), indent=2)}

COMPATIBILITY ANALYSIS:
{json.dumps(compatibility_analysis, indent=2)}

Create a comprehensive compatibility report with these sections:

1. INTRODUCTION (100-150 words)
   - Overview of compatibility analysis approach
   - Both Vedic and Western perspectives

2. VEDIC COMPATIBILITY (ASHTAKOOT) (300-400 words)
   - Guna Milan score and interpretation
   - Analysis of 8 kutas (Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi)
   - Manglik Dosha consideration if present
   - Overall Vedic compatibility assessment

3. PERSONALITY DYNAMICS (350-450 words)
   - How your Sun, Moon, and Ascendant interact
   - Complementary vs. challenging traits
   - Communication styles (Mercury)
   - Emotional compatibility (Moon signs)

4. LOVE & ATTRACTION (300-400 words)
   - Venus-Mars synastry
   - Romantic chemistry indicators
   - Physical and emotional attraction patterns
   - How you express and receive love differently

5. PARTNERSHIP STRENGTHS (250-350 words)
   - Harmonious aspects and placements
   - Natural areas of agreement
   - Shared values and goals
   - Ways you support each other's growth

6. GROWTH AREAS & CHALLENGES (250-350 words)
   - Challenging aspects to be aware of
   - Potential conflict zones
   - Different needs or approaches
   - How to navigate differences constructively

7. LONG-TERM POTENTIAL (200-300 words)
   - Composite chart themes (if calculated)
   - Shared life path indicators
   - Timing of relationship (dashas)
   - Marriage and commitment indicators

8. RELATIONSHIP GUIDANCE (200-250 words)
   - Practical advice for harmony
   - Communication tips based on Mercury placements
   - Honoring each other's needs
   - Making the most of your cosmic connection

TONE: Balanced, honest, constructive, hopeful
LENGTH: 2000-2800 words
Address both people as "you" collectively

Begin the compatibility report:"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    
    def generate_transit_report(
        self,
        natal_chart: Dict,
        current_transits: Dict,
        time_period: str = "monthly"
    ) -> str:
        """
        Generate transit predictions for specified time period
        
        Args:
            natal_chart: User's birth chart
            current_transits: Current planetary positions
            time_period: "daily", "weekly", "monthly", or "yearly"
        """
        
        period_config = {
            "daily": ("Today's", "today", 300, 500),
            "weekly": ("This Week's", "this week", 500, 700),
            "monthly": ("This Month's", "this month", 800, 1200),
            "yearly": ("This Year's", "this year", 1500, 2000)
        }
        
        period_name, period_phrase, min_words, max_words = period_config.get(
            time_period,
            period_config["monthly"]
        )
        
        prompt = f"""Generate a {period_name.lower()} transit forecast.

NATAL CHART:
{json.dumps(self._prepare_chart_summary(natal_chart), indent=2)}

CURRENT TRANSITS:
{json.dumps(current_transits, indent=2)}

Create a {period_name} transit report with these sections:

1. OVERVIEW ({int(min_words * 0.15)}-{int(max_words * 0.15)} words)
   - General energy of {period_phrase}
   - Most significant transits
   - Overall themes

2. MAJOR TRANSITS ({int(min_words * 0.25)}-{int(max_words * 0.25)} words)
   - Key planetary movements
   - How they affect your natal planets
   - Opportunities and challenges
   - Specific dates to note

3. AREAS OF LIFE AFFECTED ({int(min_words * 0.30)}-{int(max_words * 0.30)} words)
   - Career & Professional Life
   - Relationships & Social Connections
   - Personal Growth & Spirituality
   - Health & Well-being
   - Finances & Resources
   (Focus on areas most affected by current transits)

4. CURRENT DASHA PERIOD ({int(min_words * 0.15)}-{int(max_words * 0.15)} words)
   - Ongoing Vimshottari Dasha influence
   - How transits interact with Dasha
   - Cumulative effect

5. GUIDANCE & RECOMMENDATIONS ({int(min_words * 0.15)}-{int(max_words * 0.15)} words)
   - Best times for important actions
   - What to be mindful of
   - How to make the most of energies
   - Dates for special attention

TONE: Practical, encouraging, specific
LENGTH: {min_words}-{max_words} words
Be concrete about timing and actionable advice

Begin the transit report:"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    
    def answer_life_question(
        self,
        question: str,
        chart_data: Dict,
        context: Optional[str] = None
    ) -> str:
        """
        Answer specific life question using astrological guidance
        
        Args:
            question: User's specific question
            chart_data: User's birth chart
            context: Optional additional context about the person
        """
        
        chart_summary = self._prepare_chart_summary(chart_data)
        
        prompt = f"""A person has asked you a specific question about their life. Provide astrological guidance.

QUESTION: {question}

{f"CONTEXT: {context}" if context else ""}

BIRTH CHART:
{json.dumps(chart_summary, indent=2)}

Guidelines for your answer:
IMPORTANT: Base your answer ONLY on the provided birth chart data. Do not assume or invent placements.

1. Address the question directly and specifically, be a chatbot give answers informally too (3-5 sentences maximum, 100 words maximum)
2. Reference relevant astrological factors:
   - Relevant houses (e.g., 7th for relationships, 10th for career)
   - Planetary placements and strengths
   - Current Dasha period influence
   - Relevant transits if timing-related
   - Any yogas or special combinations
3. Provide practical, actionable guidance
4. Acknowledge timing if the question is about "when"
5. Be specific, not generic
6. If the question is unclear, ask for clarification
- Give a clear guidance (yes / wait / be careful / favorable)
- If timing is unclear, say “this period” or “the coming weeks”
- End with one practical suggestion

FORMAT RULE:
- Write as a single paragraph.
- No line breaks.

Remember:
- You're a guide, not a fortune teller
- Frame challenges as growth opportunities
- Suggest practical steps alongside astrological insights
- Be honest and compassionate

Provide your astrological guidance:"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=180,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    
    def _prepare_chart_summary(self, chart_data: Dict, analysis: Optional[Dict] = None) -> Dict:
        """
        Prepare concise chart summary for AI prompts
        """
        summary = {
            "birth_info": chart_data.get("birth_data", {}),
            "key_placements": {
                "sun": chart_data.get("planets", {}).get("Sun", {}).get("sidereal", {}),
                "moon": chart_data.get("planets", {}).get("Moon", {}).get("sidereal", {}),
                "ascendant": chart_data.get("houses", {}).get("vedic", {}).get("ascendant", {}),
                "mercury": chart_data.get("planets", {}).get("Mercury", {}).get("sidereal", {}),
                "venus": chart_data.get("planets", {}).get("Venus", {}).get("sidereal", {}),
                "mars": chart_data.get("planets", {}).get("Mars", {}).get("sidereal", {}),
                "jupiter": chart_data.get("planets", {}).get("Jupiter", {}).get("sidereal", {}),
                "saturn": chart_data.get("planets", {}).get("Saturn", {}).get("sidereal", {})
            },
            "houses": chart_data.get("houses", {}).get("vedic", {}).get("houses", []),
            "current_dasha": chart_data.get("dashas", {}).get("current_dasha", {})
        }
        
        if analysis:
            summary["analysis"] = {
                "yogas": analysis.get("yogas", []),
                "element_balance": analysis.get("personality", {}).get("element_balance", {}),
                "modality_balance": analysis.get("personality", {}).get("modality_balance", {})
            }
        
        if "aspects" in chart_data:
            # Only include major aspects
            major_aspects = [
                asp for asp in chart_data["aspects"]
                if asp["orb"] < 5  # Tight orbs only
            ]
            summary["major_aspects"] = major_aspects[:10]  # Top 10
        
        return summary


# # Example usage
# if __name__ == "__main__":
#     # Initialize Mati AI
#     mati = MatiAI()
    
#     # Example: Load a calculated chart
#     # In real implementation, this would come from your database
#     example_chart = adapt_chart_if_needed({
#         "birth_data": {
#             "date": "2004-03-06T07:20:00",
#             "latitude": 26.50881,
#             "longitude": 90.913178,
#             "place": "Barnagar",
#             "timezone": "Asia/Kolkata"
#         },

#         "planets": {
#             "Sun": {
#                 "sidereal": {
#                     "sign": "Aquarius",
#                     "degree_in_sign": round(321.92 % 30, 2),
#                     "nakshatra": "Purva Bhadrapada"
#                 },
#                 "house": 11
#             },
#             "Moon": {
#                 "sidereal": {
#                     "sign": "Leo",
#                     "degree_in_sign": round(130.81 % 30, 2),
#                     "nakshatra": "Magha"
#                 },
#                 "house": 5
#             },
#             "Mercury": {
#                 "sidereal": {
#                     "sign": "Aquarius",
#                     "degree_in_sign": round(323.74 % 30, 2),
#                     "nakshatra": "Purva Bhadrapada"
#                 },
#                 "house": 11
#             },
#             "Venus": {
#                 "sidereal": {
#                     "sign": "Aries",
#                     "degree_in_sign": round(6.44 % 30, 2),
#                     "nakshatra": "Ashwini"
#                 },
#                 "house": 1
#             },
#             "Mars": {
#                 "sidereal": {
#                     "sign": "Aries",
#                     "degree_in_sign": round(26.32 % 30, 2),
#                     "nakshatra": "Bharani"
#                 },
#                 "house": 1
#             },
#             "Jupiter": {
#                 "sidereal": {
#                     "sign": "Leo",
#                     "degree_in_sign": round(139.81 % 30, 2),
#                     "nakshatra": "Purva Phalguni"
#                 },
#                 "house": 5
#             },
#             "Saturn": {
#                 "sidereal": {
#                     "sign": "Gemini",
#                     "degree_in_sign": round(72.38 % 30, 2),
#                     "nakshatra": "Ardra"
#                 },
#                 "house": 3
#             },
#             "Rahu": {
#                 "sidereal": {
#                     "sign": "Aries",
#                     "degree_in_sign": round(20.34 % 30, 2),
#                     "nakshatra": "Bharani"
#                 },
#                 "house": 1
#             },
#             "Ketu": {
#                 "sidereal": {
#                     "sign": "Libra",
#                     "degree_in_sign": round(200.34 % 30, 2),
#                     "nakshatra": "Vishakha"
#                 },
#                 "house": 7
#             }
#         },

#         "houses": {
#             "vedic": {
#                 "ascendant": {
#                     "sign": "Pisces",
#                     "degree_in_sign": round(353.4 % 30, 2)
#                 },
#                 "houses": [
#                     {"house": 1, "sign": "Aries", "planets": ["Venus", "Mars", "Rahu"]},
#                     {"house": 2, "sign": "Taurus", "planets": []},
#                     {"house": 3, "sign": "Gemini", "planets": ["Saturn"]},
#                     {"house": 4, "sign": "Cancer", "planets": []},
#                     {"house": 5, "sign": "Leo", "planets": ["Moon", "Jupiter"]},
#                     {"house": 6, "sign": "Virgo", "planets": []},
#                     {"house": 7, "sign": "Libra", "planets": ["Ketu"]},
#                     {"house": 8, "sign": "Scorpio", "planets": ["Pluto"]},
#                     {"house": 9, "sign": "Sagittarius", "planets": []},
#                     {"house": 10, "sign": "Capricorn", "planets": ["Neptune"]},
#                     {"house": 11, "sign": "Aquarius", "planets": ["Sun", "Mercury", "Uranus"]},
#                     {"house": 12, "sign": "Pisces", "planets": []}
#                 ]
#             }
#         },

#         "dashas": {
#             "current_dasha": {
#                 "planet": "Sun",   # placeholder
#                 "start_date": None,
#                 "end_date": None,
#                 "duration_years": None
#             }
#         },

#         "aspects": []
#     })

#     # Generate birth chart report
#     print("Generating birth chart report...")
#     report = mati.generate_birth_chart_report(
#         chart_data=example_chart,
#         analysis={},
#         user_name="Madhav"
#     )

#     print("\n" + "=" * 80)
#     print("💬 MATI CHAT STARTED")
#     print("Type 'exit', 'quit', or 'bye' to end the chat.")
#     print("=" * 80)

#     while True:
#         question = input("\nYou: ").strip()

#         if question.lower() in {"exit", "quit", "bye"}:
#             print("\nMati: May the stars guide you well 🌙✨")
#             break

#         if not question:
#             print("Mati: Please ask a clear question.")
#             continue

#         answer = mati.answer_life_question(
#             question=question,
#             chart_data=example_chart
#         )

#         print(f"\nMati: {answer}")
