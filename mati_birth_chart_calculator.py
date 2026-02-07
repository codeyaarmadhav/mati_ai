"""
Mati Birth Chart Calculator - Core Module
AstroNexus Platform

This module handles the core astrological calculations combining
Vedic and Western astrology principles.
"""

import swisseph as swe
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
import os


class BirthChartCalculator:
    """
    Handles astronomical calculations for birth charts using Swiss Ephemeris
    """
    
    # Planet IDs from Swiss Ephemeris
    PLANETS = {
        'Sun': swe.SUN,
        'Moon': swe.MOON,
        'Mercury': swe.MERCURY,
        'Venus': swe.VENUS,
        'Mars': swe.MARS,
        'Jupiter': swe.JUPITER,
        'Saturn': swe.SATURN,
        'Rahu': swe.MEAN_NODE,  # North Node
        'Uranus': swe.URANUS,
        'Neptune': swe.NEPTUNE,
        'Pluto': swe.PLUTO
    }
    
    ZODIAC_SIGNS = [
        'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
        'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ]
    
    NAKSHATRAS = [
        'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
        'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 
        'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 
        'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha',
        'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 
        'Uttara Bhadrapada', 'Revati'
    ]
    
    def __init__(self, ephemeris_path: str = None):
        """
        Initialize calculator with ephemeris path
        
        Args:
            ephemeris_path: Path to Swiss Ephemeris data files
                          Download from: https://www.astro.com/ftp/swisseph/ephe/
        """
        if ephemeris_path:
            swe.set_ephe_path(ephemeris_path)
        else:
            # Default path - you may need to adjust this
            swe.set_ephe_path('/usr/share/ephe')
    
    def calculate_birth_chart(
        self,
        birth_date: datetime,
        latitude: float,
        longitude: float,
        timezone_offset: float = 0
    ) -> Dict:
        """
        Calculate complete birth chart with both Vedic and Western positions
        
        Args:
            birth_date: Date and time of birth (in local time)
            latitude: Birth location latitude (-90 to 90)
            longitude: Birth location longitude (-180 to 180)
            timezone_offset: Timezone offset from UTC in hours
            
        Returns:
            Dictionary containing complete chart data
        """
        # Convert to UTC
        utc_date = birth_date - timedelta(hours=timezone_offset)
        
        # Calculate Julian Day Number
        jd = swe.julday(
            utc_date.year,
            utc_date.month,
            utc_date.day,
            utc_date.hour + utc_date.minute / 60.0 + utc_date.second / 3600.0
        )
        
        # Get Ayanamsa (precession difference between tropical and sidereal)
        # Using Lahiri (most common in Vedic astrology)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        ayanamsa = swe.get_ayanamsa_ut(jd)
        
        # Calculate planetary positions
        planets_data = self._calculate_planets(jd, ayanamsa)
        
        # Calculate houses
        houses_data = self._calculate_houses(jd, latitude, longitude, ayanamsa)
        
        # Calculate aspects (Western)
        aspects = self._calculate_aspects(planets_data)
        
        # Calculate Vimshottari Dasha (Vedic planetary periods)
        dashas = self._calculate_vimshottari_dasha(
            planets_data['Moon']['sidereal']['longitude'],
            birth_date
        )
        
        return {
            'birth_data': {
                'date': birth_date.isoformat(),
                'latitude': latitude,
                'longitude': longitude,
                'timezone_offset': timezone_offset,
                'julian_day': jd,
                'ayanamsa': ayanamsa
            },
            'planets': planets_data,
            'houses': houses_data,
            'aspects': aspects,
            'dashas': dashas,
            'metadata': {
                'calculated_at': datetime.utcnow().isoformat(),
                'ephemeris_version': 'Swiss Ephemeris',
                'ayanamsa_type': 'Lahiri'
            }
        }
    
    def _calculate_planets(self, jd: float, ayanamsa: float) -> Dict:
        """Calculate positions for all planets in both systems"""
        planets_data = {}
        
        for planet_name, planet_id in self.PLANETS.items():
            # Calculate position
            pos, ret = swe.calc_ut(jd, planet_id)
            
            tropical_long = pos[0]  # Tropical longitude
            sidereal_long = (tropical_long - ayanamsa) % 360  # Sidereal
            
            # For Ketu (South Node), add 180 degrees to Rahu
            if planet_name == 'Rahu':
                ketu_tropical = (tropical_long + 180) % 360
                ketu_sidereal = (sidereal_long + 180) % 360
                planets_data['Ketu'] = {
                    'tropical': self._get_position_details(ketu_tropical),
                    'sidereal': self._get_position_details(ketu_sidereal),
                    'is_retrograde': False  # Nodes are always retrograde
                }
            
            planets_data[planet_name] = {
                'tropical': self._get_position_details(tropical_long),
                'sidereal': self._get_position_details(sidereal_long),
                'is_retrograde': ret[0] < 0 if len(ret) > 0 else False,
                'speed': pos[3] if len(pos) > 3 else None
            }
        
        return planets_data
    
    def _get_position_details(self, longitude: float) -> Dict:
        """Get detailed position information from longitude"""
        sign_num = int(longitude / 30)
        degree_in_sign = longitude % 30
        
        # Calculate nakshatra (27 divisions of 13°20' each)
        nakshatra_num = int(longitude / 13.333333)
        nakshatra_pada = int((longitude % 13.333333) / 3.333333) + 1
        
        return {
            'longitude': round(longitude, 6),
            'sign': self.ZODIAC_SIGNS[sign_num],
            'sign_number': sign_num + 1,
            'degree': int(degree_in_sign),
            'minute': int((degree_in_sign % 1) * 60),
            'second': int(((degree_in_sign % 1) * 60 % 1) * 60),
            'degree_in_sign': round(degree_in_sign, 6),
            'nakshatra': self.NAKSHATRAS[nakshatra_num],
            'nakshatra_pada': nakshatra_pada,
            'formatted': f"{int(degree_in_sign)}°{int((degree_in_sign % 1) * 60)}' {self.ZODIAC_SIGNS[sign_num]}"
        }
    
    def _calculate_houses(
        self,
        jd: float,
        latitude: float,
        longitude: float,
        ayanamsa: float
    ) -> Dict:
        """Calculate house cusps for both systems"""
        
        # Placidus houses (Western)
        houses_placidus = swe.houses(jd, latitude, longitude, b'P')
        
        # Whole Sign houses (Vedic) - based on ascendant
        asc_tropical = houses_placidus[1][0]
        asc_sidereal = (asc_tropical - ayanamsa) % 360
        
        # Create whole sign houses (each sign = one house)
        asc_sign = int(asc_sidereal / 30)
        whole_sign_houses = [(asc_sign + i) % 12 for i in range(12)]
        
        houses_data = {
            'western': {
                'system': 'Placidus',
                'ascendant': self._get_position_details(asc_tropical),
                'midheaven': self._get_position_details(houses_placidus[1][9]),
                'cusps': [
                    self._get_position_details(houses_placidus[1][i])
                    for i in range(12)
                ]
            },
            'vedic': {
                'system': 'Whole Sign',
                'ascendant': self._get_position_details(asc_sidereal),
                'houses': [
                    {
                        'house_number': i + 1,
                        'sign': self.ZODIAC_SIGNS[whole_sign_houses[i]],
                        'sign_number': whole_sign_houses[i] + 1
                    }
                    for i in range(12)
                ]
            }
        }
        
        return houses_data
    
    def _calculate_aspects(self, planets_data: Dict) -> List[Dict]:
        """Calculate major aspects between planets (Western)"""
        aspects = []
        aspect_types = {
            0: ('Conjunction', 8),      # 0° ± 8°
            60: ('Sextile', 6),          # 60° ± 6°
            90: ('Square', 8),           # 90° ± 8°
            120: ('Trine', 8),           # 120° ± 8°
            180: ('Opposition', 8)       # 180° ± 8°
        }
        
        planet_names = list(planets_data.keys())
        
        for i, planet1 in enumerate(planet_names):
            for planet2 in planet_names[i + 1:]:
                long1 = planets_data[planet1]['tropical']['longitude']
                long2 = planets_data[planet2]['tropical']['longitude']
                
                # Calculate angular separation
                diff = abs(long1 - long2)
                if diff > 180:
                    diff = 360 - diff
                
                # Check for aspects
                for aspect_angle, (aspect_name, orb) in aspect_types.items():
                    if abs(diff - aspect_angle) <= orb:
                        aspects.append({
                            'planet1': planet1,
                            'planet2': planet2,
                            'aspect': aspect_name,
                            'angle': aspect_angle,
                            'orb': round(abs(diff - aspect_angle), 2),
                            'applying': self._is_applying(
                                planets_data[planet1],
                                planets_data[planet2],
                                diff
                            )
                        })
        
        return aspects
    
    def _is_applying(self, planet1: Dict, planet2: Dict, current_angle: float) -> bool:
        """Determine if aspect is applying or separating"""
        # Simplified - would need more complex logic for accurate determination
        speed1 = planet1.get('speed', 0)
        speed2 = planet2.get('speed', 0)
        return abs(speed1) > abs(speed2)
    
    def _calculate_vimshottari_dasha(
        self,
        moon_longitude: float,
        birth_date: datetime
    ) -> Dict:
        """
        Calculate Vimshottari Dasha (120-year planetary period system)
        
        Dasha order: Ketu(7) -> Venus(20) -> Sun(6) -> Moon(10) -> Mars(7) ->
                     Rahu(18) -> Jupiter(16) -> Saturn(19) -> Mercury(17)
        """
        # Dasha sequence with years
        dasha_sequence = [
            ('Ketu', 7), ('Venus', 20), ('Sun', 6), ('Moon', 10),
            ('Mars', 7), ('Rahu', 18), ('Jupiter', 16), ('Saturn', 19),
            ('Mercury', 17)
        ]
        
        # Determine starting Dasha based on Moon's nakshatra
        nakshatra_num = int(moon_longitude / 13.333333)
        start_dasha_index = nakshatra_num % 9
        
        # Calculate balance of first Dasha
        nakshatra_lord = dasha_sequence[start_dasha_index][0]
        nakshatra_portion = (moon_longitude % 13.333333) / 13.333333
        years_completed = nakshatra_portion * dasha_sequence[start_dasha_index][1]
        years_remaining = dasha_sequence[start_dasha_index][1] - years_completed
        
        # Build Dasha timeline
        current_date = birth_date
        dasha_timeline = []
        
        for i in range(9):
            index = (start_dasha_index + i) % 9
            planet, total_years = dasha_sequence[index]
            
            if i == 0:
                years = years_remaining
            else:
                years = total_years
            
            end_date = current_date + timedelta(days=years * 365.25)
            
            dasha_timeline.append({
                'planet': planet,
                'start_date': current_date.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_years': round(years, 2)
            })
            
            current_date = end_date
        
        # Determine current Dasha
        now = datetime.now()
        current_dasha = None
        for dasha in dasha_timeline:
            start = datetime.fromisoformat(dasha['start_date'])
            end = datetime.fromisoformat(dasha['end_date'])
            if start <= now <= end:
                current_dasha = dasha
                break
        
        return {
            'system': 'Vimshottari Dasha',
            'birth_nakshatra_lord': nakshatra_lord,
            'timeline': dasha_timeline,
            'current_dasha': current_dasha
        }


class ChartAnalyzer:
    """
    Analyzes birth chart to identify yogas, strengths, and patterns
    """
    
    def __init__(self, chart_data: Dict):
        self.chart = chart_data
        self.planets = chart_data['planets']
        self.houses = chart_data['houses']
    
    def analyze_personality(self) -> Dict:
        """Analyze core personality based on Sun, Moon, Ascendant"""
        sun = self.planets['Sun']['sidereal']
        moon = self.planets['Moon']['sidereal']
        ascendant = self.houses['vedic']['ascendant']
        
        return {
            'sun_sign': {
                'sign': sun['sign'],
                'influence': 'Core identity, life purpose, ego'
            },
            'moon_sign': {
                'sign': moon['sign'],
                'nakshatra': moon['nakshatra'],
                'influence': 'Emotions, mind, inner self'
            },
            'ascendant': {
                'sign': ascendant['sign'],
                'influence': 'Outer personality, physical body, life approach'
            },
            'element_balance': self._analyze_elements(),
            'modality_balance': self._analyze_modalities()
        }
    
    def _analyze_elements(self) -> Dict:
        """Count planets in each element"""
        elements = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}
        element_map = {
            0: 'Fire', 1: 'Earth', 2: 'Air', 3: 'Water',  # Aries, Taurus, Gemini, Cancer
            4: 'Fire', 5: 'Earth', 6: 'Air', 7: 'Water',  # Leo, Virgo, Libra, Scorpio
            8: 'Fire', 9: 'Earth', 10: 'Air', 11: 'Water' # Sag, Cap, Aquarius, Pisces
        }
        
        for planet_data in self.planets.values():
            sign_num = planet_data['sidereal']['sign_number'] - 1
            element = element_map[sign_num]
            elements[element] += 1
        
        return elements
    
    def _analyze_modalities(self) -> Dict:
        """Count planets in each modality (Cardinal, Fixed, Mutable)"""
        modalities = {'Cardinal': 0, 'Fixed': 0, 'Mutable': 0}
        modality_map = {
            0: 'Cardinal', 1: 'Fixed', 2: 'Mutable', 3: 'Cardinal',
            4: 'Fixed', 5: 'Mutable', 6: 'Cardinal', 7: 'Fixed',
            8: 'Mutable', 9: 'Cardinal', 10: 'Fixed', 11: 'Mutable'
        }
        
        for planet_data in self.planets.values():
            sign_num = planet_data['sidereal']['sign_number'] - 1
            modality = modality_map[sign_num]
            modalities[modality] += 1
        
        return modalities
    
    def identify_yogas(self) -> List[Dict]:
        """
        Identify important Vedic yogas (planetary combinations)
        This is simplified - real implementation would be much more complex
        """
        yogas = []
        
        # Check for Gaja Kesari Yoga (Jupiter-Moon conjunction/aspect)
        jupiter_sign = self.planets['Jupiter']['sidereal']['sign_number']
        moon_sign = self.planets['Moon']['sidereal']['sign_number']
        
        # If Jupiter is in a kendra (1,4,7,10) from Moon
        diff = abs(jupiter_sign - moon_sign)
        if diff in [0, 3, 6, 9]:
            yogas.append({
                'name': 'Gaja Kesari Yoga',
                'description': 'Auspicious combination of Jupiter and Moon',
                'effects': 'Intelligence, wisdom, prosperity, good reputation'
            })
        
        # Add more yoga checks here...
        # - Raja Yoga (lords of kendras and trikonas together)
        # - Dhana Yoga (wealth combinations)
        # - Pancha Mahapurusha Yogas
        # etc.
        
        return yogas
    
    def get_career_indicators(self) -> Dict:
        """Analyze career and professional indicators"""
        # 10th house (career), 2nd house (wealth), 6th house (work)
        return {
            '10th_house_analysis': 'Career, profession, public image',
            '2nd_house_analysis': 'Wealth, resources, family business',
            '6th_house_analysis': 'Daily work, service, competition',
            'saturn_placement': self.planets['Saturn']['sidereal']['sign'],
            'jupiter_placement': self.planets['Jupiter']['sidereal']['sign'],
            'mercury_placement': self.planets['Mercury']['sidereal']['sign']
        }


# Example usage
if __name__ == "__main__":
    # Initialize calculator
    calculator = BirthChartCalculator()
    
    # Example birth data
    birth_datetime = datetime(1990, 5, 15, 14, 30)  # May 15, 1990, 2:30 PM
    latitude = 28.6139  # New Delhi
    longitude = 77.2090
    timezone_offset = 5.5  # IST (UTC+5:30)
    
    # Calculate chart
    chart = calculator.calculate_birth_chart(
        birth_datetime,
        latitude,
        longitude,
        timezone_offset
    )
    
    # Print results (pretty formatted)
    print(json.dumps(chart, indent=2))
    
    # Analyze chart
    analyzer = ChartAnalyzer(chart)
    personality = analyzer.analyze_personality()
    yogas = analyzer.identify_yogas()
    
    print("\n=== PERSONALITY ANALYSIS ===")
    print(json.dumps(personality, indent=2))
    
    print("\n=== YOGAS IDENTIFIED ===")
    print(json.dumps(yogas, indent=2))
