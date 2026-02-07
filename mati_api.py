# """
# Mati API - FastAPI Backend
# AstroNexus Platform

# REST API for birth chart calculations and AI-powered reports
# """

# from fastapi import FastAPI, HTTPException, Depends, status
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from pydantic import BaseModel, Field, validator
# from typing import Optional, List
# from datetime import datetime
# import uvicorn

# # Import our custom modules
# from mati_birth_chart_calculator import BirthChartCalculator, ChartAnalyzer
# from mati_ai_engine import MatiAI

# # Initialize FastAPI app
# app = FastAPI(
#     title="Mati API - AstroNexus",
#     description="AI-powered astrology API combining Vedic and Western traditions",
#     version="1.0.0"
# )

# # CORS configuration
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Configure properly for production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Security
# security = HTTPBearer()

# # Initialize engines
# chart_calculator = BirthChartCalculator()
# mati_ai = MatiAI()


# # ==================== REQUEST MODELS ====================

# class BirthData(BaseModel):
#     """Birth information for chart calculation"""
#     date: str = Field(..., description="Birth date in ISO format (YYYY-MM-DD)")
#     time: str = Field(..., description="Birth time in HH:MM format (24-hour)")
#     latitude: float = Field(..., ge=-90, le=90, description="Birth location latitude")
#     longitude: float = Field(..., ge=-180, le=180, description="Birth location longitude")
#     timezone_offset: float = Field(..., ge=-12, le=14, description="Timezone offset from UTC in hours")
#     location_name: Optional[str] = Field(None, description="City name for reference")
    
#     @validator('date')
#     def validate_date(cls, v):
#         try:
#             datetime.fromisoformat(v)
#         except ValueError:
#             raise ValueError("Date must be in ISO format (YYYY-MM-DD)")
#         return v
    
#     @validator('time')
#     def validate_time(cls, v):
#         try:
#             hour, minute = map(int, v.split(':'))
#             if not (0 <= hour < 24 and 0 <= minute < 60):
#                 raise ValueError
#         except:
#             raise ValueError("Time must be in HH:MM format (24-hour)")
#         return v


# class ChartRequest(BaseModel):
#     """Request for birth chart calculation"""
#     birth_data: BirthData
#     include_analysis: bool = Field(True, description="Include chart analysis")
#     include_yogas: bool = Field(True, description="Identify Vedic yogas")


# class ReportRequest(BaseModel):
#     """Request for AI-generated report"""
#     birth_data: BirthData
#     report_type: str = Field(..., description="Type: 'birth_chart', 'transit', 'yearly'")
#     user_name: Optional[str] = None
#     language: str = Field("english", description="Report language: 'english' or 'hindi'")


# class CompatibilityRequest(BaseModel):
#     """Request for compatibility analysis"""
#     person1: BirthData
#     person2: BirthData
#     name1: Optional[str] = None
#     name2: Optional[str] = None


# class QuestionRequest(BaseModel):
#     """Request for life guidance question"""
#     question: str = Field(..., min_length=10, max_length=500)
#     birth_data: BirthData
#     context: Optional[str] = Field(None, max_length=1000)


# # ==================== HELPER FUNCTIONS ====================

# def parse_birth_datetime(birth_data: BirthData) -> datetime:
#     """Convert BirthData to datetime object"""
#     date_parts = birth_data.date.split('-')
#     time_parts = birth_data.time.split(':')
    
#     return datetime(
#         year=int(date_parts[0]),
#         month=int(date_parts[1]),
#         day=int(date_parts[2]),
#         hour=int(time_parts[0]),
#         minute=int(time_parts[1])
#     )


# def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
#     """
#     Verify JWT token (simplified - implement proper auth)
#     In production, use proper JWT validation
#     """
#     token = credentials.credentials
#     # TODO: Implement proper token validation
#     # For now, just return token
#     return token


# # ==================== API ENDPOINTS ====================

# @app.get("/")
# async def root():
#     """Health check endpoint"""
#     return {
#         "service": "Mati API - AstroNexus",
#         "status": "operational",
#         "version": "1.0.0",
#         "message": "AI-powered astrology combining Vedic and Western traditions"
#     }


# @app.get("/health")
# async def health_check():
#     """Detailed health check"""
#     return {
#         "status": "healthy",
#         "timestamp": datetime.utcnow().isoformat(),
#         "services": {
#             "chart_calculator": "operational",
#             "ai_engine": "operational",
#             "database": "operational"  # TODO: Check actual DB connection
#         }
#     }


# @app.post("/api/v1/chart/calculate")
# async def calculate_chart(request: ChartRequest):
#     """
#     Calculate birth chart with optional analysis
    
#     Returns complete chart data including:
#     - Planetary positions (Vedic and Western)
#     - House cusps
#     - Aspects
#     - Vimshottari Dasha periods
#     - Optional: Yogas and analysis
#     """
#     try:
#         # Parse birth data
#         birth_datetime = parse_birth_datetime(request.birth_data)
        
#         # Calculate chart
#         chart = chart_calculator.calculate_birth_chart(
#             birth_date=birth_datetime,
#             latitude=request.birth_data.latitude,
#             longitude=request.birth_data.longitude,
#             timezone_offset=request.birth_data.timezone_offset
#         )
        
#         # Add location info
#         chart['birth_data']['location_name'] = request.birth_data.location_name
        
#         # Optional analysis
#         response_data = {"chart": chart}
        
#         if request.include_analysis or request.include_yogas:
#             analyzer = ChartAnalyzer(chart)
            
#             analysis = {}
#             if request.include_analysis:
#                 analysis['personality'] = analyzer.analyze_personality()
#                 analysis['career'] = analyzer.get_career_indicators()
            
#             if request.include_yogas:
#                 analysis['yogas'] = analyzer.identify_yogas()
            
#             response_data['analysis'] = analysis
        
#         return {
#             "success": True,
#             "data": response_data,
#             "message": "Chart calculated successfully"
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Chart calculation failed: {str(e)}"
#         )


# @app.post("/api/v1/report/generate")
# async def generate_report(request: ReportRequest):
#     """
#     Generate AI-powered astrological report
    
#     Report types:
#     - birth_chart: Comprehensive natal chart analysis
#     - transit: Current transit predictions
#     - yearly: Year-ahead forecast
#     """
#     try:
#         # Calculate chart first
#         birth_datetime = parse_birth_datetime(request.birth_data)
#         chart = chart_calculator.calculate_birth_chart(
#             birth_date=birth_datetime,
#             latitude=request.birth_data.latitude,
#             longitude=request.birth_data.longitude,
#             timezone_offset=request.birth_data.timezone_offset
#         )
        
#         # Analyze chart
#         analyzer = ChartAnalyzer(chart)
#         analysis = {
#             'personality': analyzer.analyze_personality(),
#             'yogas': analyzer.identify_yogas(),
#             'career': analyzer.get_career_indicators()
#         }
        
#         # Generate report based on type
#         if request.report_type == "birth_chart":
#             report = mati_ai.generate_birth_chart_report(
#                 chart_data=chart,
#                 analysis=analysis,
#                 user_name=request.user_name,
#                 language=request.language
#             )
#         elif request.report_type == "transit":
#             # TODO: Calculate current transits
#             current_transits = {}  # Placeholder
#             report = mati_ai.generate_transit_report(
#                 natal_chart=chart,
#                 current_transits=current_transits,
#                 time_period="monthly"
#             )
#         else:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=f"Invalid report type: {request.report_type}"
#             )
        
#         return {
#             "success": True,
#             "data": {
#                 "report": report,
#                 "report_type": request.report_type,
#                 "generated_at": datetime.utcnow().isoformat(),
#                 "chart_summary": {
#                     "sun_sign": chart["planets"]["Sun"]["sidereal"]["sign"],
#                     "moon_sign": chart["planets"]["Moon"]["sidereal"]["sign"],
#                     "ascendant": chart["houses"]["vedic"]["ascendant"]["sign"],
#                     "current_dasha": chart["dashas"]["current_dasha"]["planet"]
#                 }
#             },
#             "message": "Report generated successfully"
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Report generation failed: {str(e)}"
#         )


# @app.post("/api/v1/compatibility/analyze")
# async def analyze_compatibility(request: CompatibilityRequest):
#     """
#     Analyze compatibility between two birth charts
    
#     Includes:
#     - Vedic Ashtakoot (Guna Milan)
#     - Western synastry aspects
#     - Relationship dynamics
#     - Strengths and challenges
#     """
#     try:
#         # Calculate both charts
#         birth1 = parse_birth_datetime(request.person1)
#         chart1 = chart_calculator.calculate_birth_chart(
#             birth_date=birth1,
#             latitude=request.person1.latitude,
#             longitude=request.person1.longitude,
#             timezone_offset=request.person1.timezone_offset
#         )
        
#         birth2 = parse_birth_datetime(request.person2)
#         chart2 = chart_calculator.calculate_birth_chart(
#             birth_date=birth2,
#             latitude=request.person2.latitude,
#             longitude=request.person2.longitude,
#             timezone_offset=request.person2.timezone_offset
#         )
        
#         # TODO: Implement actual compatibility calculations
#         # For now, placeholder analysis
#         compatibility_analysis = {
#             "ashtakoot_score": 28,  # Out of 36
#             "guna_milan_percentage": 77.8,
#             "key_factors": [
#                 "Strong Moon connection",
#                 "Venus-Mars harmony",
#                 "Complementary ascendants"
#             ]
#         }
        
#         # Generate AI report
#         report = mati_ai.generate_compatibility_report(
#             chart1_data=chart1,
#             chart2_data=chart2,
#             compatibility_analysis=compatibility_analysis,
#             names=(request.name1, request.name2)
#         )
        
#         return {
#             "success": True,
#             "data": {
#                 "report": report,
#                 "compatibility_score": compatibility_analysis["guna_milan_percentage"],
#                 "ashtakoot_score": compatibility_analysis["ashtakoot_score"],
#                 "person1_summary": {
#                     "sun_sign": chart1["planets"]["Sun"]["sidereal"]["sign"],
#                     "moon_sign": chart1["planets"]["Moon"]["sidereal"]["sign"]
#                 },
#                 "person2_summary": {
#                     "sun_sign": chart2["planets"]["Sun"]["sidereal"]["sign"],
#                     "moon_sign": chart2["planets"]["Moon"]["sidereal"]["sign"]
#                 }
#             },
#             "message": "Compatibility analysis completed"
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Compatibility analysis failed: {str(e)}"
#         )


# @app.post("/api/v1/guidance/ask")
# async def ask_question(request: QuestionRequest):
#     """
#     Get AI-powered astrological guidance for specific life question
    
#     Example questions:
#     - "Should I change my career now?"
#     - "What's the best time for marriage?"
#     - "How can I improve my relationships?"
#     """
#     try:
#         # Calculate chart
#         birth_datetime = parse_birth_datetime(request.birth_data)
#         chart = chart_calculator.calculate_birth_chart(
#             birth_date=birth_datetime,
#             latitude=request.birth_data.latitude,
#             longitude=request.birth_data.longitude,
#             timezone_offset=request.birth_data.timezone_offset
#         )
        
#         # Get AI guidance
#         guidance = mati_ai.answer_life_question(
#             question=request.question,
#             chart_data=chart,
#             context=request.context
#         )
        
#         return {
#             "success": True,
#             "data": {
#                 "question": request.question,
#                 "guidance": guidance,
#                 "answered_at": datetime.utcnow().isoformat(),
#                 "relevant_placements": {
#                     "current_dasha": chart["dashas"]["current_dasha"]["planet"],
#                     "moon_sign": chart["planets"]["Moon"]["sidereal"]["sign"],
#                     "moon_nakshatra": chart["planets"]["Moon"]["sidereal"]["nakshatra"]
#                 }
#             },
#             "message": "Guidance provided"
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Question answering failed: {str(e)}"
#         )


# @app.get("/api/v1/zodiac/signs")
# async def get_zodiac_info():
#     """Get information about zodiac signs"""
#     return {
#         "success": True,
#         "data": {
#             "signs": BirthChartCalculator.ZODIAC_SIGNS,
#             "count": 12,
#             "description": "12 zodiac signs used in both Vedic and Western astrology"
#         }
#     }


# @app.get("/api/v1/vedic/nakshatras")
# async def get_nakshatra_info():
#     """Get information about Vedic nakshatras (lunar mansions)"""
#     return {
#         "success": True,
#         "data": {
#             "nakshatras": BirthChartCalculator.NAKSHATRAS,
#             "count": 27,
#             "description": "27 lunar mansions in Vedic astrology"
#         }
#     }


# # ==================== RUN SERVER ====================

# if __name__ == "__main__":
#     # Run development server
#     # For production, use: gunicorn -w 4 -k uvicorn.workers.UvicornWorker mati_api:app
#     uvicorn.run(
#         "mati_api:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True,  # Auto-reload on code changes
#         log_level="info"
#     )
