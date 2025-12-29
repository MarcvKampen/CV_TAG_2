"""
AI Prompt Module for CV Analysis.

Contains the master prompt and processing logic for extracting structured data from CVs.
"""

import json
from datetime import datetime

from mistralai import Mistral

from config import LLM_MODEL


def get_master_prompt() -> str:
    """Get the main prompt for CV data extraction."""
    current_year = datetime.now().year
    return f"""
TASK: Extract structured information from CV documents with high precision and consistency.

IMPORTANT INSTRUCTIONS:
- Process each CV separately, identifying clear boundaries between different individuals.
- For each person, extract EXACTLY the 7 fields specified below.
- Double-check all extracted information for accuracy.
- Only include information that appears at least twice in the document or has strong supporting evidence.
- If information cannot be verified with high confidence or values don't match across checks, use "N/A" instead of guessing.
- Return the result as a valid Python dictionary.
- Do NOT include any explanatory text, headers, or additional formatting beyond valid JSON.

EXTRACTION FIELDS (7 required fields):

1. GENDER
   - Assign the candidate to "Male" or "Female".

2. EDUCATION_LEVEL
   - STRICT HIERARCHY: ManaMa > Master > BanaBa > Academic Bachelor > Professional Bachelor > Secondary level.
   - "ManaMa" - ANY master's degree (ongoing or completed) followed after another completed master's degree. ManaMa should be explicitly stated in the CV text (ManaMa is not the same as a second master's degree). If not, then use "Master", since this is the most common type of degree we see.
   - "Master" - ANY master's degree (ongoing or completed).
   - "BanaBa" - ANY bachelor's degree followed after another completed bachelor's degree. Most of the time, BanaBa is explicitly stated in the CV text.
   - "Academic Bachelor" - ONLY university bachelor's degrees.
   - "Professional Bachelor" - Non-university bachelor's degrees (colleges, institutes).
   - "Secondary level" - High school or equivalent.
   - Double-check educational institutions to correctly classify university vs. non-university.
   - DO NOT assign a tag "Master" if the term is not used in the CV text.
   - Beware that sometimes the master thesis is explained in other section of the CV and should not count as an additional master.
    - Pay special attention to abbreviations: M.Sc., M.A., M.Eng. for Masters; B.Sc., B.A., B.Eng. for Bachelors.

3. GRADUATION_YEAR
   - Format: "GY" followed by a 4-digit year (e.g., "GY {current_year}").
   - ONLY for the most recent educational program (ManaMa, Master, BanaBa, Academic Bachelor, Professional Bachelor, Secondary level). SO not for trainings, internships, courses, language courses, etc.
   - Use the year of the expected graduation, so the latest year of the program.
   - Must be EXPLICITLY stated in the document.
   - Sometimes, month abbreviations may be used in the text followed by 2-digits for the year (e.g. "Jul 24" would imply a tag "GY 2024").
   - IMPORTANT: When you see "Present", "Now", "Current", "In progress", "Ongoing", or any variation (like "2023 - Present")
     for the last degree, use "GY {current_year}" as the expected graduation year.
   - For standard educational programs with "current" or "present" status:
     * Bachelor's programs: typically add 3 years from the start date.
     * Master's programs: typically add 1-2 years from the start date.
   - If no information is found, use "N/A".

4. EXPERIENCE
   - Assign the candidate to one of the categories of years of experience (from 0 to over 20 years of experience).
   - Categories: "0-0.5y exp", "0.5-1y exp", "1-1.5y exp", "1.5-2y exp", "2-2.5y exp", "2.5-3y exp", "3-3.5y exp", "3.5-4y exp", ">4y exp", ">5y exp", ">6y-10 exp", "10y-15y exp", "15y-20y exp", ">20y exp".
   - If no information is found, use "0-0.5y exp".
   - Experience can relate to any field and be full-time or part-time, but no student jobs, internships, trainings, or else can be counted in the year of experience.
   - Look out for month abbreviations or years given with the last 2 digits ("Jan 24 - Sep 25" after studies gives an experience of "1.5-2y exp").

5. MOTHER_TONGUE
   - Location: Focus on the "Skills" or "Languages" section of the CV.
   - Indicators: Look for terms like "Mother tongue," "Native," or "C2 level" to identify the native language.
   - Acceptable Languages: "Dutch", "French", "Spanish", "Italian", "Portuguese","Romanian","English","German","Swedish","Danish","Norwegian","Russian","Polish","Ukrainian","Czech","Slovak","Mandarin Chinese","Japanese","Korean","Vietnamese","Indonesian","Thai","Arabic","Icelandic","Finnish","Lithuanian","Latvian","Turkish","Persian (Farsi)","Greek","Hebrew","Telugu","Albanian","Tagalog","Chinese","Bulgarian","Amazigh","Nepali","Bangla","Kazakh","Catalan","Azerbaijani","Afrikaans","Punjabi","Kabyle"
   - Proficiency Level: Note that C1 level is not sufficient for native classification; only C2 or explicit terms like "Native" or "Mother tongue" are acceptable.
   - If 2 languages could be considered as mother tongue, then give priority to the language that is NOT "English" and give priority to the language that is either "Dutch" or "French".
     - E.G. "Arabic (Native)", "French (C2)" and "English (C2)" should be "French"
   - Because of the nature of the data, it is possible that the languages are not always correctly identified because of image recognition errors. If the text only displays languages names, but no proficiency level, then use the first language in the list. since people tend to list their mother tongue first.

6. SCHOOL
   - Pick the school from the allowed lists that best fits the CV's latest educational program.
   - Based on the 'EDUCATION_LEVEL' you identify, choose a school from the appropriate list below.
   - You MUST copy the field name EXACTLY as spelled in the allowed values.
   - If the school is not on the list or is outside Belgium, use "Abroad".
   - If no school information can be found, use "N/A".

   Allowed Values for 'Schools (Master)':
   - Katholieke Universiteit Leuven
   - Université Catholique Louvain
   - Louvain School Management
   - Vrije Universiteit Brussel
   - Université Libre Bruxelles
   - Vlerick Business School
   - Solvay Brussels School - Economics & Management
   - ICHEC Brussels Management School
   - Brussels School Ihecs Journalism & Communication
   - Université Saint-Louis
   - Haute Ecole Francisco Ferrer
   - European Communication School
   - EHSAL Management School Brussel
   - HEC Liège
   - Université de Liège
   - Université de Mons
   - Université de Namur
   - Antwerp Management School
   - Universiteit Antwerpen
   - Universiteit Gent
   - Universiteit Hasselt
   - College of Europe
   - Economic School of Louvain
   - École polytechnique de Louvain
   - ECAM Brussels Engineering School
   - United International Business Schools
   - Antwerp Maritime Academy

   Allowed Values for 'Schools (Bachelor)':
   - PXL Hasselt
   - Thomas More
   - UCLL (UC Leuven-Limburg)
   - Odisee
   - Kedge Business School Bordeaux
   - Katholieke Hogeschool Sint-Lieven
   - ECS - European Communication School
   - Haute Ecole Libre de Bruxelles Ilya Prigogine
   - EPFC
   - Artevelde
   - Haute Ecole Ephec
   - HoGent
   - Erasmus Hogeschool Brussel
   - Haute Ecole en Hainaut
   - HE2B ESI
   - EPFL
   - ECSEDI - ISALT Galilée
   - ESA Saint-Luc
   - Howest
   - Hogeschool VIVES
   - Henallux
   - Sint Lucas Antwerpen

7. FIELD_OF_STUDY
   - Identify the field of study for the candidate's latest educational program from the mandatory list below.
   - Use the 'Degree' examples to help you match the CV content to the correct 'Field of Study'.
   - You MUST return the value from the 'Field of Study' column EXACTLY as spelled.
   - If no match is possible, use "Other".

   Allowed Values for 'Field of Study' (use 'Degree' for matching):
   ---
   Faculty: Arts & Philosophy
   - Field of Study: Urban Planning (Degree: Bachelor/Master in City & Regional Planning, Urbanism, Spatial Planning, Transportation sciences, Urban Studies)
   - Field of Study: Architecture (Degree: Bachelor/Master in Architecture, Human Settlements)
   - Field of Study: Design (Degree: Bachelor/Master in Design & Production Technology, Fine Arts, Graphic & Digital Media, Industrial Design, Web Design)
   - Field of Study: History (Degree: Bachelor/Master in History, Art History, Musicology, Theatre Studies, Global Studies, African Studies, Archaeology, Medieval and Renaissance Studies)
   - Field of Study: Linguistics & Literature (Degree: Bachelor/Master in African Languages, Applied Languages, East European Languages, Linguistics and Literature, Interpreting, Multilingual Communication, Oriental Languages, Digital Text Analysis, Translation, Clinical Linguistics, Comparative Modern Literature)
   - Field of Study: Media & Entertainment (Degree: Bachelor in Audiovisual techniques, Creative Media & Game Technologies, Digital Arts & Entertainment, International Media & Entertainment Business, Sound Engineering, Multimedia & Creative Technologies)
   - Field of Study: Music & Film (Degree: Bachelor in Film, Music)
   - Field of Study: Philosophy (Degree: Bachelor/Master in Philosophy, Moral Sciences, Bioethics)
   ---
   Faculty: Economics & Business
   - Field of Study: Business (Degree: Bachelor/Master in Business Administration, Business Engineering, Business Management, E-Business, Entrepreneurship and Technology)
   - Field of Study: Data in business (Degree: Bachelor/Master in Advanced Business Management: Data & Analytics, Business Data Analysis, Data Science for Business, Statistics and Data Science for Business, Business Analytics, Management: Business Analytics & AI)
   - Field of Study: Economics (Degree: Bachelor/Master in Economics, Applied Economics, Business Economics, Social and Economic Sciences)
   - Field of Study: Finance (Degree: Bachelor/Master in Accountancy, Finance & Insurance, Actuarial and Financial Engineering, Banking & Finance, Financial Economics, Financial Management, Quantitative Finance)
   - Field of Study: Human Resources Management (Degree: Bachelor/Master in Human Resources, Human Resource Management, Learning and Development in Organisations)
   - Field of Study: International Business (Degree: Bachelor/Master in European Policies, International Business, International Organisation & Management, International Relations & Affairs, International Business Economics and Management, International Management and Strategy, International Trade)
   - Field of Study: IT in business (Degree: Bachelor/Master in IT Management, Digital Business, Business & Information Systems Engineering, Business Informatics, Information Management, Artificial Intelligence in Business and Industry)
   - Field of Study: Marketing (Degree: Bachelor/Master in Marketing, International Strategic Marketing, Marketing and Digital Transformation)
   - Field of Study: Sales & Marketing (Degree: Bachelor/Master in Real Estate, Retail Management, Marketing, Marketing Analytics, Marketing Management, Sales Management)
   - Field of Study: Supply Chain (Degree: Bachelor/Master in Mobility and Supply Chain Engineering, Operations Research, Supply Chain Management, Maritime and Air Transport Management, Transport Management and Logistics)
   - Field of Study: Sustainability (Degree: Master in Sustainable Development)
   ---
   Faculty: Engineering & Technology
   - Field of Study: Aerospace Engineering (Degree: Bachelor/Master in Aviation, Aeronautical Engineering, Aerospace Engineering, Space Studies)
   - Field of Study: Bioscience Engineering (Degree: Bachelor/Master in Biomedical Engineering, labtechnology, Biochemical Engineering, Bioinformatics, Clinical Scientific Research, Agro- and Ecosystems Engineering, Cellular and Genetic Engineering, Human Health Engineering, Nanoscience, Plant Biotechnology, Forest and Nature Management)
   - Field of Study: Chemical Engineering (Degree: Master in Chemical Engineering, Chemical Engineering Technology)
   - Field of Study: Civil Engineering (Degree: Bachelor/Master in Construction, Civil Engineering, Civil Engineering Technology, Architectural Engineering)
   - Field of Study: Computer Science (Degree: Bachelor/Master in Applied Computer Science, Artificial Intelligence, Computer Engineering, Computer Science, Software Engineering)
   - Field of Study: Data Science (Degree: Bachelor/Master in Data Science & AI, Information and Data Science, Statistical Data Analysis, Statistics and Data Science, Biometrics, Industry, Social, Behavioural and Educational Sciences)
   - Field of Study: Electrical Engineering (Degree: Bachelor/Master in Electrical Engineering, Electronics and Telecommunication, Electrical Engineering Technology, Electronics and ICT Engineering Technology, Photonics Engineering)
   - Field of Study: Environmental Engineering (Degree: Bachelor/Master in Energy technology, Environmental Engineering & Sciences, Engineering: Energy, Safety Engineering)
   - Field of Study: Food Technology (Degree: Master in Food Science, Technology and Business, Sustainable Food Systems, Food Technology, Nutrition and Food systems)
   - Field of Study: Industrial Engineering (Degree: Bachelor/Master in Industrial Engineering, Industrial Design Engineering Technology, Industrial Engineering and Operations Research, Smart Operations and Maintenance in Industry)
   - Field of Study: Information Technology (Degree: Bachelor/Master in Electronics & ICT, ICT, Information and Technology, Information Management, Applied Informatics, Cybersecurity, Information Engineering Technology)
   - Field of Study: Mechanical Engineering (Degree: Bachelor/Master in Automotive Engineering, Automotive Technology, Electromechanics, Mechanical Engineering, Electromechanical Engineering Technology, Machine Production Automation, Materials Engineering, Product Development, Welding Engineering)
   - Field of Study: Nuclear Engineering (Degree: Master in Nuclear Engineering)
   ---
   Faculty: Health Sciences
   - Field of Study: Audiology (Degree: Bachelor/Master in Audiology, Speech Therapy, Deglutology, Logopaedic and Audiological Sciences)
   - Field of Study: Dentistry (Degree: Bachelor in Dental Care)
   - Field of Study: Health Technology (Degree: Master in Innovative Health Technology)
   - Field of Study: Medicine (Degree: Bachelor/Master in Eye Care, Medical Imaging & Radiotherapy, Medicine, Veterinary Medicine)
   - Field of Study: Nutritional Sciences (Degree: Master in Human Nutrition)
   - Field of Study: Life Sciences (Degree: Bachelor in Life Sciences)
   - Field of Study: Occupational Therapy (Degree: Bachelor/Master in Ergotherapy, Osteopathy)
   - Field of Study: Orthotics and Prosthetics (Degree: Bachelor/Master in Orthopaedic Technology, Orthopedagogy, Clinical Orthopedagogy)
   - Field of Study: Pharmaceutical Sciences (Degree: Master in Drug Development, Pharmaceutical Engineering, Pharmaceutical Sciences)
   - Field of Study: Physiotherapy (Degree: Master in Rehabilitation Sciences and Physiotherapy)
   - Field of Study: Sport Sciences (Degree: Bachelor/Master in Adapted Physical Activity, Movement Science, Sports)
   ---
   Faculty: Law & Criminology
   - Field of Study: Criminology (Degree: Master in Criminology)
   - Field of Study: Law (Degree: Bachelor/Master in Applied Law, Law, Canon Law, Intellectual Property and ICT Law, Society, Law and Religion)
   ---
   Faculty: Management
   - Field of Study: Business Management (Degree: Bachelor/Master in KMO Management, Organisation & Management, Business Management, General Management, Global Management, Management)
   - Field of Study: Engineering & Technology (Degree: Master in Engineering Management, Management Engineering, Management of Technology)
   - Field of Study: Events & Facility (Degree: Bachelor/Master in Event Management, Facility Management, Real Estate Management, Office Management)
   - Field of Study: Healthcare (Degree: Bachelor/Master in Health Care Management and Policy, Healthcare Management)
   - Field of Study: Hospitality (Degree: Bachelor/Master in Hospitality Management, Hotelmanagement, Tourism & Hospitality Management, Tourism)
   - Field of Study: Other (Degree: Master in Art Management, Bachelor in Idea & Innovation Management, Master in Management - Innovation & Entrepreneurship, Master in Luxury Management)
   - Field of Study: Sport & Culture (Degree: Bachelor/Master in Sport Management, Sport & Cultural Management, Cultural Management)
   ---
   Faculty: Psychology and Educational Sciences
   - Field of Study: Psychology (Degree: Bachelor/Master in Human Decision Science, Labour Sciences, Psychology, Theory and Research, Business Psychology, Brain and Cognitive Sciences)
   - Field of Study: Education Sciences (Degree: Bachelor/Master in Education, Educational Studies, Instructional and Educational Sciences, Pedagogical Sciences)
   ---
   Faculty: Science
   - Field of Study: Biology (Degree: Bachelor/Master in Molecular Biology, Biochemistry and Biotechnology, Biology, Marine Biological Resources, Biophysics, Biomedical Sciences, Neurosciences)
   - Field of Study: Chemistry (Degree: Master in Chemistry)
   - Field of Study: Environmental Sciences (Degree: Bachelor/Master in Sustainable Land Management, Sustainability, Agro- & Biotechnology, Aquaculture, Environmental Technology, Physical Land Resources (Soil Science), Rural Development, Water Resources Engineering, Agro- and Enviromental Nematology, Marine and Lacustrine Science and Management)
   - Field of Study: Mathematics (Degree: Bachelor/Master in Statistics, Mathematical Engineering, Mathematics, Actuarial Science)
   - Field of Study: Physics (Degree: Bachelor/Master in Physics, Physics and Astronomy, Astrophysics, Medical Physics)
   ---
   Faculty: Social Sciences
   - Field of Study: Anthropology (Degree: Master in Cultural Anthropology and Development Studies, Social and Cultural Anthropology)
   - Field of Study: Archaelogy (Degree: Bachelor in Archaeology)
   - Field of Study: Communication (Degree: Bachelor/Master in Journalism, Public Relations, Information and Communication Sciences and Technologies, Communication and Media Science, Communication Management, International Communication, Business Communication, Communication Studies: Digital Media in Europe)
   - Field of Study: Cultural Studies (Degree: Master in Digital Humanities)
   - Field of Study: Geography (Degree: Bachelor/Master in Geography, Population and Development Studies, Geology, Geomatics)
   - Field of Study: International Relations (Degree: Bachelor/Master in International Relations & European Studies, European Studies)
   - Field of Study: Political Science (Degree: Bachelor/Master in Development Policy & Governance, Conflict and Development Studies, Public Sector Innovation and eGovernance, International Politics, International Relations and Diplomacy, Political Science, Gender and Diversity, Global Security and Strategy, Comparative sciences of culture, Cultural Studies, European Studies: Transnational and Global Perspectives, Liberal Studies)
   - Field of Study: Public Relations (Degree: Bachelor/Master in Public Relations, Public Administration and Management, Global Health, Public Affairs)
   - Field of Study: Social Work (Degree: Bachelor/Master in European Social Security, Social Work and Welfare Studies, Social Work)
   - Field of Study: Sociology (Degree: Master in Sociology)
   - Field of Study: Theology (Degree: Bachelor/Master in Theology and Religious Studies)

OUTPUT FORMAT:
Return a Python dictionary with these 7 keys:
- gender
- education_level
- graduation_year
- experience
- mother_tong
- school
- field_of_study

Example:
{{
    "gender": "Female",
    "education_level": "Master",
    "graduation_year": "GY 2023",
    "experience": "0-0.5y exp",
    "mother_tong": "French",
    "school": "Katholieke Universiteit Leuven",
    "field_of_study": "Finance"
}}

Rules:
- Return a Python dictionary as valid JSON.
- If not sure, return "N/A" for the specific field.
- Only output raw JSON. No explanations.
- Always prioritize explicit information over assumptions or interpretations.
"""


def process_cv(client, ocr_text: str, master_prompt_text: str) -> dict | None:
    """
    Process OCR text with the Mistral LLM to extract structured data.

    Args:
        client: Mistral client
        ocr_text: Extracted text from the CV
        master_prompt_text: The evaluation prompt

    Returns:
        Dictionary of extracted fields, or None on error
    """
    model_to_use = LLM_MODEL
    try:
        full_prompt = f"{master_prompt_text}\n\n--- CV CONTENT ---\n{ocr_text}"

        response = client.chat.complete(
            model=model_to_use,
            messages=[
                {"role": "user", "content": full_prompt},
            ],
            response_format={"type": "json_object"},
        )
        response_content = str(response.choices[0].message.content)
        return json.loads(response_content)

    except Exception as e:
        print(f"Error processing CV: {e}")
        return None
