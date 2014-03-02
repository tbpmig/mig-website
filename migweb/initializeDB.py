# Create your views here.
from datetime import date

from history.models import GoverningDocumentType
from event_cal.models import GoogleCalendar
from mig_main.models  import AcademicTerm, TBPChapter, OfficerPosition, Status, Standing, ShirtSize, Major, OfficerTeam,CurrentTerm
from requirements.models import SemesterType, DistinctionType, EventCategory,Requirement
GOOGLE_CALENDARS = [
    {"name":"Service Events Calendar", "calendar_id":"6837sd9phcm1sajfv1gcp6lnh0@group.calendar.google.com"},
    {"name":"Social Events Calendar", "calendar_id":"m59tp2tusq387h7dk90asckj8c@group.calendar.google.com"},
    {"name":"Corporate Events Calendar", "calendar_id":"d97jlm1l5ihd7qbn1tvncbogfg@group.calendar.google.com"},
    {"name":"Meetings Calendar", "calendar_id":"dnce33j1cc0hfd91g7rb5015dg@group.calendar.google.com"},
    {"name":"Officer Calendar", "calendar_id":"hptph03thj15cnmpr6t3to2e9c@group.calendar.google.com"},
    {"name":"Office Hours Calendar", "calendar_id":"k92tkp473unphdftcqp1m201ok@group.calendar.google.com"},
]
SEMESTER_TYPES = [
    {"name":"Winter"},
    {"name":"Summer"},
    {"name":"Fall"},
]

##Need to allow lowercase letters following greek letters MI-Za,Zb, TX-Dq
TBP_CHAPTERS = [
    {"state":"AL","chapters":[{"letter":"A","school":"Auburn University"},
                              {"letter":"B","school":"The University of Alabama"},
                              {"letter":"G","school":"University of Alabama at Birmingham"},
                              {"letter":"D","school":"University of Alabama in Huntsville"},
                              {"letter":"E","school":"University of South Alabama "},
                              ]},
    {"state":"AK","chapters":[{"letter":"A","school":"University of Alaska Fairbanks"},
                              ]},
    {"state":"AZ","chapters":[{"letter":"A","school":"The University of Arizona"},
                              {"letter":"B","school":"Arizona State Univeristy"},
                              {"letter":"G","school":"Northern Arizona University"},
                             ]},                              
    {"state":"AR","chapters":[{"letter":"A","school":"University of Arkansas"},
                             ]},
    {"state":"CA","chapters":[{"letter":"A","school":"University of California, Berkeley"},
                              {"letter":"B","school":"California Institute of Technology"},
                              {"letter":"G","school":"Stanford University"},
                              {"letter":"D","school":"University of Southern California"},
                              {"letter":"E","school":"University of California, Los Angeles"},
                              {"letter":"Z","school":"Santa Clara University"},
                              {"letter":"H","school":"San Jose State University"},
                              {"letter":"Q","school":"California State University, Long Beach"},
                              {"letter":"I","school":"California State University, Los Angeles"},
                              {"letter":"K","school":"California State University, Northridge"},
                              {"letter":"L","school":"University of California, Davis"},
                              {"letter":"M","school":"California Polytechnic State University, San Luis Obispo"},
                              {"letter":"N","school":"California State Polytechnic University, Pomona"},
                              {"letter":"X","school":"San Diego State University"},
                              {"letter":"O","school":"Loyola Marymount University"},
                              {"letter":"P","school":"Northrop University (inactive)"},
                              {"letter":"R","school":"California State University, Fresno"},
                              {"letter":"S","school":"University of California, Santa Barbara"},
                              {"letter":"T","school":"University of California, Irvine"},
                              {"letter":"U","school":"California State University, Sacramento"},
                              {"letter":"F","school":"University of the Pacific"},
                              {"letter":"C","school":"California State University, Fullerton"},
                              {"letter":"Y","school":"University of California, San Diego"},
                              {"letter":"W","school":"Harvey Mudd College"},
                              {"letter":"AA","school":"California State University, Chico"},
                              {"letter":"AB","school":"University of California, Riverside"},
                              {"letter":"AG","school":"San Fransisco State University"},
                              {"letter":"AD","school":"University of California, Santa Cruz"},
                              {"letter":"AE","school":"University of San Diego"},
                              ]},
    {"state":"CO","chapters":[{"letter":"A","school":"Colorado School of Mines"},
                              {"letter":"B","school":"University of Colorado at Boulder"},
                              {"letter":"G","school":"University of Denver (inactive)"},
                              {"letter":"D","school":"Colorado State University"},
                              {"letter":"E","school":"University of Colorado at Denver"},
                              {"letter":"Z","school":"United States Air Force Academy"},
                              ]},
    {"state":"CT","chapters":[{"letter":"A","school":"Yale University"},
                              {"letter":"B","school":"The University of Connecticut"},
                              {"letter":"G","school":"University of Hartford"},
                             ]},            
    {"state":"DE","chapters":[{"letter":"A","school":"University of Delaware"},
                              ]},
    {"state":"DC","chapters":[{"letter":"A","school":"Howard University"},
                              {"letter":"B","school":"The Catholic University of America"},
                              {"letter":"G","school":"The George Washington University"},
                             ]},
    {"state":"FL","chapters":[{"letter":"A","school":"University of Florida"},
                              {"letter":"B","school":"University of Miami"},
                              {"letter":"G","school":"University of South Florida"},
                              {"letter":"D","school":"The University of Central Florida"},
                              {"letter":"E","school":"Florida Atlantic University"},
                              {"letter":"Z","school":"Florida Institute of Technology"},
                              {"letter":"H","school":"Florida A&M University-Florida State University"},
                              {"letter":"Q","school":"Florida International University"},
                              {"letter":"I","school":"Embry-Riddle Aeronautical University"},
                              ]},   
    {"state":"GA","chapters":[{"letter":"A","school":"Georgia Institute of Technology"},
                              {"letter":"B","school":"Mercer University"},
                             ]},    
    {"state":"ID","chapters":[{"letter":"A","school":"University of Idaho"},
                              {"letter":"B","school":"Idaho State University"},
                              {"letter":"G","school":"Boise State University"},
                             ]},    
    {"state":"IL","chapters":[{"letter":"A","school":"University of Illinois at Urbana-Champaign"},
                              {"letter":"B","school":"Illinois Institute of Technology"},
                              {"letter":"G","school":"Northwestern University Technological Institute"},
                              {"letter":"D","school":"Bradley University"},
                              {"letter":"E","school":"Southern Illinois University at Carbondale"},
                              {"letter":"Z","school":"University of Illinois at Chicago"},
                             ]},    
    {"state":"IN","chapters":[{"letter":"A","school":"Purdue University"},
                              {"letter":"B","school":"Rose-Hulman Institute of Technology"},
                              {"letter":"G","school":"University of Notre Dame"},
                              {"letter":"D","school":"Valparaiso University"},
                              {"letter":"E","school":"Trine University"},
                             ]},    
    {"state":"IA","chapters":[{"letter":"A","school":"Iowa State University"},
                              {"letter":"B","school":"The University of Iowa"},
                             ]},                                 
    {"state":"KS","chapters":[{"letter":"A","school":"The University of Kansas"},
                              {"letter":"B","school":"Wichita State University"},
                              {"letter":"G","school":"Kansas State University"},
                              ]},
    {"state":"KY","chapters":[{"letter":"A","school":"University of Kentucky"},
                              {"letter":"B","school":"University of Louisville"},
                              {"letter":"G","school":"Western Kentucky University"},
                             ]},
    {"state":"LA","chapters":[{"letter":"A","school":"Louisiana State University"},
                              {"letter":"B","school":"Tulane University of Louisiana"},
                              {"letter":"G","school":"Louisiana Tech University"},
                              {"letter":"D","school":"University of Louisiana at Lafayette"},
                              {"letter":"E","school":"University of New Orleans"},
                             ]},                                                         
    {"state":"ME","chapters":[{"letter":"A","school":"University of Maine"},
                            ]},
    {"state":"MD","chapters":[{"letter":"A","school":"The Johns Hopkins University"},
                              {"letter":"B","school":"The University of Maryland"},
                              {"letter":"G","school":"The United States Naval Academy"},
                              {"letter":"D","school":"University of Maryland Baltimore County"},
                              {"letter":"E","school":"Morgan State University"},
                             ]},                            
    {"state":"MA","chapters":[{"letter":"A","school":"Worcester Polytechnic Institute"},
                              {"letter":"B","school":"The Massachusetts Institute of Technology"},
                              {"letter":"G","school":"Harvard University (inactive)"},
                              {"letter":"D","school":"Tufts University"},
                              {"letter":"E","school":"Northeastern University"},
                              {"letter":"Z","school":"University of Massachusetts at Amherst"},
                              {"letter":"H","school":"Boston University"},
                              {"letter":"Q","school":"University of Massachusetts Lowell"},
                              {"letter":"I","school":"Western New England University"},
                             ]},    
    {"state":"MI","chapters":[{"letter":"A","school":"Michigan State University"},
                              {"letter":"B","school":"Michigan Technological University"},
                              {"letter":"G","school":"The University of Michigan"},
                              {"letter":"D","school":"University of Detroit Mercy"},
                              {"letter":"E","school":"Wayne State University"},
                              {"letter":"Za","school":"Kettering University"},
                              {"letter":"Zb","school":"Kettering University"},
                              {"letter":"H","school":"Lawrence Technological University"},
                              {"letter":"Q","school":"Oakland University"},
                              {"letter":"I","school":"The University of Michigan-Dearborn"},
                              {"letter":"K","school":"Western Michigan University"},
                              {"letter":"L","school":"Grand Valley State University"},
                             ]},
    {"state":"MN","chapters":[{"letter":"A","school":"University of Minnesota - Twin Cities"},
                              {"letter":"B","school":"University of Minnesota, Duluth"},
                             ]},        
    {"state":"MS","chapters":[{"letter":"A","school":"Mississippi State University"},
                              {"letter":"B","school":"The University of Mississippi"},
                             ]},                             
    {"state":"MO","chapters":[{"letter":"A","school":"The University of Missouri-Columbia"},
                              {"letter":"B","school":"Missouri Univerisy of Science and Technology"},
                              {"letter":"G","school":"Washington University"},
                              {"letter":"D","school":"The University of Missouri-Kansas City"},
                              {"letter":"E","school":"Saint Louis University"},
                             ]},                        
    {"state":"MT","chapters":[{"letter":"A","school":"Montanta State University"},
                              {"letter":"B","school":"Montana Tech of the University of Montana"},
                             ]},                             
    {"state":"NE","chapters":[{"letter":"A","school":"University of Nebraska-Lincoln"},
                            ]},                         
    {"state":"NV","chapters":[{"letter":"A","school":"University of Nevada, Reno"},
                              {"letter":"B","school":"University of Nevada, Las Vegas"},
                              ]},                           
    {"state":"NH","chapters":[{"letter":"A","school":"University of New Hampshire"},
                              {"letter":"B","school":"Dartmouth College"},
                             ]},
    {"state":"NJ","chapters":[{"letter":"A","school":"Stevens Institute of Technology"},
                              {"letter":"B","school":"Rutgers University"},
                              {"letter":"G","school":"New Jersey Institute of Technology"},
                              {"letter":"D","school":"Princeton University"},
                              {"letter":"E","school":"Rowan University"},
                              {"letter":"Z","school":"The College of New Jersey"},
                             ]},
    {"state":"NM","chapters":[{"letter":"A","school":"New Mexico State University"},
                              {"letter":"B","school":"University of New Mexico"},
                              {"letter":"G","school":"New Mexico Institute of Mining and Technology"},
                            ]},
    {"state":"NY","chapters":[{"letter":"A","school":"Columbia University"},
                              {"letter":"B","school":"Syracuse University"},
                              {"letter":"G","school":"Rensselaer Polytechnic Institute"},
                              {"letter":"D","school":"Cornell University"},
                              {"letter":"E","school":"New York University (inactive)"},
                              {"letter":"Z","school":"Polytechnic Institute of Brooklyn (inactive)"},
                              {"letter":"H","school":"The City College of the City University of New York"},
                              {"letter":"Q","school":"Clarkson University"},
                              {"letter":"I","school":"The Cooper Union School of Engineering"},
                              {"letter":"K","school":"The University of Rochester"},
                              {"letter":"L","school":"Pratt Institute (inactive)"},
                              {"letter":"M","school":"Union College"},
                              {"letter":"N","school":"University at Buffalo"},
                              {"letter":"X","school":"Manhattan College"},
                              {"letter":"O","school":"State University of New York at Stony Brook"},
                              {"letter":"P","school":"Rochester Institute of Technology"},
                              {"letter":"R","school":"Polytechnic Institute of New York University"},
                              {"letter":"S","school":"Alfred University"},
                              {"letter":"T","school":"Binghamton University"},
                              {"letter":"U","school":"United States Military Academy"},
                             ]},                            
    {"state":"NC","chapters":[{"letter":"A","school":"North Carolina State University"},
                              {"letter":"B","school":"The University of North Carolina at Chapel Hill (inactive)"},
                              {"letter":"G","school":"Duke University"},
                              {"letter":"D","school":"University of North Carolina at Charlotte"},
                              {"letter":"E","school":"North Carolina Agricultural and Technical State University"},
                            ]},     
    {"state":"ND","chapters":[{"letter":"A","school":"North Dakota State University"},
                              {"letter":"B","school":"University of North Dakota"},
                            ]}, 
    {"state":"OH","chapters":[{"letter":"A","school":"Case Western Reserve University"},
                              {"letter":"B","school":"University of Cincinatti"},
                              {"letter":"G","school":"The Ohio State University"},
                              {"letter":"D","school":"Ohio University"},
                              {"letter":"E","school":"Cleveland State University"},
                              {"letter":"Z","school":"University of Toledo"},
                              {"letter":"H","school":"Air Force Institute of Technology"},
                              {"letter":"Q","school":"University of Dayton"},
                              {"letter":"I","school":"Ohio Northern University"},
                              {"letter":"K","school":"University of Akron"},
                              {"letter":"L","school":"Youngstown State University"},
                              {"letter":"M","school":"Wright State University"},
                              {"letter":"N","school":"Cedarville University"},
                              {"letter":"X","school":"Miami University"},
                            ]},     
    {"state":"OK","chapters":[{"letter":"A","school":"University of Oklahoma"},
                              {"letter":"B","school":"The University of Tulsa"},
                              {"letter":"G","school":"Oklahoma State University"},
                            ]},
    {"state":"OR","chapters":[{"letter":"A","school":"Oregon State University"},
                              {"letter":"B","school":"Portland State University"},
                              {"letter":"G","school":"University of Portland"},
                            ]},
    {"state":"PA","chapters":[{"letter":"A","school":"Lehigh University"},
                              {"letter":"B","school":"The Pennsylvania State University"},
                              {"letter":"G","school":"Carnegie Mellon"},
                              {"letter":"D","school":"University of Pennsylvania"},
                              {"letter":"E","school":"Lafayette College"},
                              {"letter":"Z","school":"Drexel University"},
                              {"letter":"H","school":"Bucknell University"},
                              {"letter":"Q","school":"Villanova University"},
                              {"letter":"I","school":"Widener University"},
                              {"letter":"K","school":"Swarthmore College"},
                              {"letter":"L","school":"University of Pittsburgh"},
                              {"letter":"M","school":"Penn State Erie, The Behrend College"},
                            ]},
    {"state":"PR","chapters":[{"letter":"A","school":"University of Puerto Rico"},
                            ]},     
    {"state":"RI","chapters":[{"letter":"A","school":"Brown University"},
                              {"letter":"B","school":"University of Rhode Island"},
                            ]},
    {"state":"SC","chapters":[{"letter":"A","school":"Clemson University"},
                              {"letter":"B","school":"University of South Carolina"},
                              {"letter":"G","school":"The Citadel"},
                            ]},
    {"state":"SD","chapters":[{"letter":"A","school":"South Dakota School of Mines & Technology"},
                              {"letter":"B","school":"South Dakota State University"},
                            ]},
    {"state":"TN","chapters":[{"letter":"A","school":"The University of Tennessee"},
                              {"letter":"B","school":"Vanderbilt University"},
                              {"letter":"G","school":"Tennessee Technological University"},
                              {"letter":"D","school":"Christian Brothers University"},
                              {"letter":"E","school":"The University of Memphis"},
                              {"letter":"Z","school":"The University of Tennessee at Chattanooga"},
                            ]},         
    {"state":"TX","chapters":[{"letter":"A","school":"The University of Texas at Austin"},
                              {"letter":"B","school":"Texas Tech University"},
                              {"letter":"G","school":"Rice University"},
                              {"letter":"D","school":"Texas A&M University"},
                              {"letter":"Dq","school":"Texas A&M University at Qatar"},
                              {"letter":"E","school":"University of Houston"},
                              {"letter":"Z","school":"Lamar University"},
                              {"letter":"H","school":"The University of Texas at Arlington"},
                              {"letter":"Q","school":"The University of Texas at El Paso"},
                              {"letter":"I","school":"Southern Methodist Uniersity"},
                              {"letter":"K","school":"Prairie View A&M University"},
                              {"letter":"L","school":"Texas A&M University Kingsville"},
                              {"letter":"M","school":"University of Texas at San Antonio"},
                            ]},
    {"state":"UT","chapters":[{"letter":"A","school":"University of Utah"},
                              {"letter":"B","school":"Brigham Young University"},
                              {"letter":"G","school":"Utah State University"},
                            ]},
    {"state":"VT","chapters":[{"letter":"A","school":"The University of Vermont"},
                              {"letter":"B","school":"Norwich University"},
                            ]},     
    {"state":"VA","chapters":[{"letter":"A","school":"University of Virginia"},
                              {"letter":"B","school":"Virginia Polytechnic Institute & State University"},
                              {"letter":"G","school":"Old Dominion University"},
                              {"letter":"D","school":"Virginia Military Institute"},
                              {"letter":"E","school":"Virginia Commonwealth University"},
                            ]},
    {"state":"WA","chapters":[{"letter":"A","school":"University of Washington"},
                              {"letter":"B","school":"Washington State University"},
                              {"letter":"G","school":"Seattle University"},
                              {"letter":"D","school":"Gonzaga University"},
                            ]},
    {"state":"WV","chapters":[{"letter":"A","school":"West Virginia University"},
                              {"letter":"B","school":"West Virginia University Institute of Technology"},
                            ]},
    {"state":"WI","chapters":[{"letter":"A","school":"The University of Wisconsin-Madison"},
                              {"letter":"B","school":"Marquette University"},
                              {"letter":"G","school":"The University of Wisconsin-Milwaukee"},
                              {"letter":"D","school":"Milwaukee School o Engineering"},
                              {"letter":"E","school":"University of Wisconsin Platteville"},
                            ]},
    {"state":"WY","chapters":[{"letter":"A","school":"University of Wyoming"},
                            ]},                         
    ]

OFFICER_POSITIONS =[
    {"name":"President","description":"Term: 1 Semester, may not run again\nTeam: Executive Committee (lead)\nThe President's primary jobs are to supervise the other officers and to plan and conduct all officer, advisory board, and general meetings. The President is the facilitator; experience as a Tau Beta Pi officer is strongly recommended. The President also acts as the representative of the society in correspondence with other organizations. The President gets to interact with many people on different levels. In addition he or she is instrumental in setting the vision and goals of the chapter. The president additionally: manages the responsibilities of the officers; schedules, plans, organizes, and runs all of the officer and general body meetings; organizes the Mailout; is the official delegate to the National Convention or District 7 Conference and arranges travel plans for other delegates; communicates with Nationals, COE, and the University.",
            "email":"tbp.president@umich.edu"},
    {"name":"Vice President","description":"Term: 1 Semester\nTeam: Executive Committee, Electee and Membership Team (lead)\nThe Vice-President oversees the electee process and acts as second-in-command to the President. The VP gets to know the electees better than anyone else. Knowledge of the electee process and internal workings of TBP is a big plus, and organizational and people skills are a must. The VP gets to meet and work with many new students. Additionally is the contact person for all electees; keeps a close eye on the progress of all electees; organizes the electee material, electee groups, and electee games; organizes and conducts electee interviews;  and works with Secretary to ensure electees have approval from Nationals.",
            "email":"tbp.vicepresident@umich.edu"},
    {"name":"Secretary","description":"Term: Academic Year\nTeam: Executive Committee",
            "email":"tbp.secretary@umich.edu"},
    {"name":"Treasurer","description":"Term: Calendar Year\nTeam: Executive Committee",
            "email":"tbp.treasurer@umich.edu"},
    {"name":"Service Coordinator","description":"Term: 1 Semester\nTeam: Service Team (lead)",
            "email":"tbp.service@umich.edu"},
    {"name":"K-12 Outreach Officer","description":"Term: 2 Offset Yearlong Terms\nTeam: Service Team",
            "email":"tbp.k12outreach@umich.edu"},
    {"name":"Campus Outreach Officer","description":"Term: 1 Semester\nTeam: Service Team",
            "email":"tbp.campusoutreach@umich.edu"},
    {"name":"Operations Officer","description":"Term: 1 Semester\nTeam: Service Team",
            "email":"tbp.operations@umich.edu"},
    {"name":"Corporate Relations Officer","description":"Term: Academic Year\nTeam: Professional Development Team (lead)",
            "email":"tbp-corporate@umich.edu"},
    {"name":"External Vice President","description":"Term: 2 Calendar Year Positions\nTeam: Professional Development Team",
            "email":"careerfair@umich.edu"},
    {"name":"New Initiatives Officer","description":"Term: 1 Semester\nTeam: Chapter Team (lead)",
            "email":"tbp.newinitiatives@umich.edu"},
    {"name":"Historian","description":"Term: 1 Semester\nTeam: Chapter Team",
            "email":"tbp.historian@umich.edu"},
    {"name":"Publicity Officer","description":"Term: 1 Semester\nTeam: Chapter Team",
            "email":"tbp.publicity@umich.edu"},
    {"name":"Website Officer","description":"Term: 1 Semester\nTeam: Chapter Team",
            "email":"tbp.website@umich.edu"},
    {"name":"Activities Officer","description":"Term: 1 Semester\nTeam: Social Team",
            "email":"tbp.activities@umich.edu"},
    {"name":"Intersociety Officer","description":"Term: 1 Semester\nTeam: Social Team",
            "email":"tbp.intersociety@umich.edu"},  
    {"name":"Graduate Student Coordinator","description":"Term: 1 Semester\nTeam: Electee and Membership Team",
            "email":"tbp.gradcoordinator@umich.edu"},
    {"name":"Membership Officer","description":"Term: 1 Semester\nTeam: Electee and Membership Team",
            "email":"tbp.membership@umich.edu"},    
    {"name":"Advisor","description":"Term: Variable,1-6 Semesters (may be reelected)\n",
            "email":"tbp-advisors@umich.edu"},          
]

STANDINGS = [ "Undergraduate", "Graduate", "Alumni"]
STATUSES =["Electee", "Active", "Non-Member"]

SHIRT_SIZES = [
    {"name":"Double Extra Small","acronym":"XXS"},
    {"name":"Extra Small","acronym":"XS"},
    {"name":"Small","acronym":"S"},
    {"name":"Medium","acronym":"M"},
    {"name":"Large","acronym":"L"},
    {"name":"Extra Large","acronym":"XL"},
    {"name":"Double Extra Large","acronym":"2XL"},
    {"name":"Triple Extra Large","acronym":"3XL"},
]

MAJORS = [
    {"name":"Aerospace Engineering","acronym":"AERO","standing_type":["Undergraduate","Graduate","Alumni"]},
    {"name":"Biomedical Engineering","acronym":"BME","standing_type":["Undergraduate","Graduate","Alumni"]},
    {"name":"Chemical Engineering","acronym":"ChE","standing_type":["Undergraduate","Graduate","Alumni"]},
    {"name":"Civil Engineering","acronym":"CEE","standing_type":["Undergraduate","Graduate","Alumni"]},
    {"name":"Computer Engineering","acronym":"CE","standing_type":["Undergraduate","Alumni"]},
    {"name":"Computer Science Engineering","acronym":"CSE","standing_type":["Undergraduate","Graduate","Alumni"]},
    {"name":"Electrical Engineering","acronym":"EE","standing_type":["Undergraduate","Graduate","Alumni"]},
    {"name":"Electrical Engineering: Systems","acronym":"EE:S","standing_type":["Graduate","Alumni"]},
    {"name":"Atmospheric, Oceanic, and Space Systems ","acronym":"AOSS","standing_type":["Undergraduate","Graduate","Alumni"]},
    {"name":"Engineering Undeclared","acronym":"ENGR","standing_type":["Undergraduate"]},
    {"name":"Engineering Physics","acronym":"EP","standing_type":["Undergraduate","Graduate","Alumni"]},
    {"name":"Industrial and Operations Engineering","acronym":"IOE","standing_type":["Undergraduate","Graduate","Alumni"]},
    {"name":"Materials Science and Engineering","acronym":"MSE","standing_type":["Undergraduate","Graduate","Alumni"]},
    {"name":"Mechanical Engineering","acronym":"ME","standing_type":["Undergraduate","Graduate","Alumni"]},
    {"name":"Naval Architecture and Marine Engineering","acronym":"NAME","standing_type":["Undergraduate","Graduate","Alumni"]},
    {"name":"Nuclear Engineering and Radiological Sciences","acronym":"NERS","standing_type":["Undergraduate","Graduate","Alumni"]},
    {"name":"Automotive Engineering","acronym":"AUTO","standing_type":["Graduate","Alumni"]},
    {"name":"Construction Engineering and Management","acronym":"CEE:C","standing_type":["Graduate","Alumni"]},
    {"name":"Energy Systems Engineering","acronym":"ESE","standing_type":["Graduate","Alumni"]},
    {"name":"Environmental Engineering","acronym":"ENV","standing_type":["Graduate","Alumni"]},
    {"name":"Financial Engineering","acronym":"FE","standing_type":["Graduate","Alumni"]},
    {"name":"Manufacturing Engineering","acronym":"MFE","standing_type":["Graduate","Alumni"]},
    {"name":"Pharmaceutical Engineering","acronym":"PHARM","standing_type":["Graduate","Alumni"]},
    {"name":"Space Engineering","acronym":"SPACE","standing_type":["Graduate","Alumni"]},
    {"name":"Plastics Engineering","acronym":"PLASTICS","standing_type":["Graduate","Alumni"]},
    {"name":"Structural Engineering","acronym":"STRUCT","standing_type":["Graduate","Alumni"]},
    ]
OFFICER_TEAMS = [
    {"name":"Executive Committee","lead":"President","members":["President","Vice President", "Secretary", "Treasurer"]},
    {"name":"Service Team","lead":"Service Coordinator","members":["Service Coordinator","K-12 Outreach Officer", "Campus Outreach Officer", "Operations Officer"]},
    {"name":"Professional Development Team","lead":"Corporate Relations Officer","members":["Corporate Relations Officer","External Vice President"]},
    {"name":"Social Team","lead":"Activities Officer","members":["Activities Officer","Intersociety Officer"]},
    {"name":"Chapter Team","lead":"New Initiatives Officer","members":["New Initiatives Officer","Historian","Publicity Officer","Website Officer"]},
    {"name":"Electee and Membership Team","lead":"Vice President","members":["Vice President", "Graduate Student Coordinator", "Membership Officer"]},
]

DISTINCTIONS = [
    {"name":"Electee (undergrad)", "status_type":"Electee", "standing_type":["Undergraduate"]},
    {"name":"Electee (grad)", "status_type":"Electee", "standing_type":["Graduate"]},
    {"name":"Active", "status_type":"Active", "standing_type":["Undergraduate","Graduate","Alumni"]},
    {"name":"Distinguished Active", "status_type":"Active", "standing_type":["Undergraduate","Graduate","Alumni"]},
    {"name":"Prestigious Active", "status_type":"Active", "standing_type":["Undergraduate","Graduate","Alumni"]},
]

EVENT_CATEGORY = [
    {"parent_category":None,"name":"Hours"},   
    {"parent_category":"Hours","name":"Service Hours"},   
    {"parent_category":"Hours","name":"Social Credits"},   
    {"parent_category":"Service Hours","name":"K-12 Outreach Hours"},   
    {"parent_category":"Service Hours","name":"Career Fair Hours"},   
    {"parent_category":"Service Hours","name":"Tutoring Hours"},   
    {"parent_category":"Service Hours","name":"foo bar Hours"},   
    {"parent_category":"Social Credits","name":"Grad Student Social Credits"},   
    {"parent_category":None,"name":"Leadership"},   
    {"parent_category":None,"name":"Meeting Attendance"},   
    {"parent_category":"Meeting Attendance","name":"Voting Meeting Attendance"},   
    {"parent_category":"Service Hours","name":"Conducted Interviews"},   
    {"parent_category":None,"name":"Attended Interviews"},   
    {"parent_category":None,"name":"Paperwork"},   
    {"parent_category":"Paperwork","name":"Essays"},   
    {"parent_category":"Paperwork","name":"Dues"},   
    {"parent_category":"Paperwork","name":"Electee Exam"},   
    {"parent_category":"Paperwork","name":"Peer Interviews"},   
    {"parent_category":"Paperwork","name":"Advisor Form"},   
    {"parent_category":"Paperwork","name":"Educational Background Form"},   
    {"parent_category":None,"name":"Group Meetings"},   
    {"parent_category":"Social Credits","name":"Extra Group Meetings"},   
]
#Need to finish these
REQUIREMENTS = [
    {"name":"Electee (undergrad)","reqs":[{"name":"Total Hours","term":["Fall","Winter"],"amount_required":20,"event_category":"Hours"},
                            {"name":"Service Hours","term":["Fall","Winter"],"amount_required":18,"event_category":"Service Hours"},
                            {"name":"Social Credits","term":["Fall","Winter"],"amount_required":2,"event_category":"Social Credits"},
                            {"name":"Meetings","term":["Fall","Winter"],"amount_required":6,"event_category":"Meeting Attendance"},
                            {"name":"Elections","term":["Fall","Winter"],"amount_required":1,"event_category":"Voting Meeting Attendance"},
                            {"name":"MindSET","term":["Fall","Winter"],"amount_required":3,"event_category":"K-12 Outreach Hours"},
                            {"name":"Tutoring","term":["Fall","Winter"],"amount_required":1,"event_category":"Tutoring Hours"},
                            {"name":"Career Fair","term":["Fall"],"amount_required":2,"event_category":"Career Fair Hours"},
                            {"name":"Interview","term":["Fall","Winter"],"amount_required":2,"event_category":"Attended Interviews"},
                            {"name":"Paperwork","term":["Fall","Winter"],"amount_required":10,"event_category":"Paperwork"},
                            {"name":"Character Essays","term":["Fall","Winter"],"amount_required":2,"event_category":"Essays"},
                            {"name":"Dues ($90)","term":["Fall","Winter"],"amount_required":1,"event_category":"Dues"},
                            {"name":"Electee Exam","term":["Fall","Winter"],"amount_required":1,"event_category":"Electee Exam"},
                            {"name":"Peer Interviews","term":["Fall","Winter"],"amount_required":6,"event_category":"Peer Interviews"},
                            {"name":"Group Meetings","term":["Fall","Winter"],"amount_required":2,"event_category":"Group Meetings"},
                            ]},
    {"name":"Electee (grad)","reqs":[{"name":"Total Hours","term":["Fall","Winter"],"amount_required":12,"event_category":"Hours"},
                            {"name":"Meetings","term":["Fall","Winter"],"amount_required":6,"event_category":"Meeting Attendance"},
                            {"name":"Elections","term":["Fall","Winter"],"amount_required":1,"event_category":"Voting Meeting Attendance"},
                            {"name":"Service","term":["Fall","Winter"],"amount_required":10,"event_category":"Service Hours"},
                            {"name":"Interview","term":["Fall","Winter"],"amount_required":1,"event_category":"Attended Interviews"},
                            {"name":"Paperwork","term":["Fall","Winter"],"amount_required":2,"event_category":"Paperwork"},
                            {"name":"Advisor Form","term":["Fall","Winter"],"amount_required":1,"event_category":"Advisor Form"},
                            {"name":"Advisor Form","term":["Fall","Winter"],"amount_required":1,"event_category":"Educational Background Form"},
                            {"name":"Dues ($90)","term":["Fall","Winter"],"amount_required":1,"event_category":"Dues"},
                            {"name":"Social Credits","term":["Fall","Winter"],"amount_required":2,"event_category":"Social Credits"},
                            {"name":"Grad Social Credits","term":["Fall","Winter"],"amount_required":1,"event_category":"Grad Student Social Credits"},
                            ]},
    {"name":"Active","reqs":[{"name":"Total Hours","term":["Fall","Winter"],"amount_required":3,"event_category":"Hours"},
                            {"name":"Meetings","term":["Fall","Winter"],"amount_required":2,"event_category":"Meeting Attendance"},
                            {"name":"Voting Meetings","term":["Fall","Winter"],"amount_required":1,"event_category":"Voting Meeting Attendance"},
                            {"name":"Service","term":["Fall","Winter"],"amount_required":2,"event_category":"Service Hours"},
                            {"name":"Social Credits","term":["Fall","Winter"],"amount_required":1,"event_category":"Social Credits"},
                            ]},
    {"name":"Distinguished Active","reqs":[{"name":"Total Hours","term":["Fall","Winter"],"amount_required":11,"event_category":"Hours"},
                            {"name":"Total Hours (summer)","term":["Summer"],"amount_required":17,"event_category":"Hours"},
                            {"name":"Meetings","term":["Fall","Winter"],"amount_required":5,"event_category":"Meeting Attendance"},
                            {"name":"Voting Meetings","term":["Fall","Winter"],"amount_required":3,"event_category":"Voting Meeting Attendance"},
                            {"name":"Service","term":["Fall","Winter"],"amount_required":8,"event_category":"Service Hours"},
                            {"name":"Service (summer)","term":["Summer"],"amount_required":10,"event_category":"Service Hours"},
                            {"name":"Leadership","term":["Fall","Winter","Summer"],"amount_required":1,"event_category":"Leadership"},
                            {"name":"Social Credits","term":["Fall","Winter","Summer"],"amount_required":2,"event_category":"Social Credits"},
                            {"name":"Interviews","term":["Fall","Winter"],"amount_required":1,"event_category":"Conducted Interviews"},
                            ]},
    {"name":"Prestigious Active","reqs":[{"name":"Total Hours","term":["Fall","Winter"],"amount_required":32,"event_category":"Hours"},
                            {"name":"Total Hours (summer)","term":["Summer"],"amount_required":38,"event_category":"Hours"},
                            {"name":"Meetings","term":["Fall","Winter"],"amount_required":5,"event_category":"Meeting Attendance"},
                            {"name":"Voting Meetings","term":["Fall","Winter"],"amount_required":3,"event_category":"Voting Meeting Attendance"},
                            {"name":"Service","term":["Fall","Winter","Summer"],"amount_required":24,"event_category":"Service Hours"},
                            {"name":"Leadership","term":["Fall","Winter","Summer"],"amount_required":1,"event_category":"Leadership"},
                            {"name":"Social Credits","term":["Fall","Winter","Summer"],"amount_required":2,"event_category":"Social Credits"},
                            {"name":"Interviews","term":["Fall","Winter"],"amount_required":1,"event_category":"Conducted Interviews"},
                            ]},
]
GOVERNING_DOC_TYPE=[
        {'name':'Constitution'},
        {'name':'Bylaws'},
        ]
def initializedb():

    #Governing Document types
    for doc in GOVERNING_DOC_TYPE:
        if len(GoverningDocumentType.objects.filter(name=doc["name"]))==0:
            d = GoverningDocumentType(name=doc['name'])
            d.save()
        else:
            print "Document Type: "+doc["name"]+" already exists."


    # Google Calendars.
    for calendar in GOOGLE_CALENDARS:
        if len(GoogleCalendar.objects.filter(name=calendar["name"]))==0:
            g = GoogleCalendar()
            g.name = calendar["name"]
            g.calendar_id = calendar["calendar_id"]
            g.save()
        else:
            print "Calendar: "+calendar["name"]+" already exists."
    # Semester Type
    for semester in SEMESTER_TYPES:
        if len(SemesterType.objects.filter(name=semester["name"]))==0:
            s = SemesterType(name = semester["name"])
            s.save()
        else:
            print "Semester: "+semester["name"]+" already exists."
    # Academic Terms
    for term_year in range(1998,date.today().year+2):
        for semester in SemesterType.objects.all():
        
            if len(AcademicTerm.objects.filter(year=term_year).filter(semester_type=semester))==0:
                a = AcademicTerm()
                a.year=term_year
                a.semester_type = semester
                a.save()
            else:
                print "AcademicTerm: "+semester.name+" "+str(term_year)+" already exists."

    if not CurrentTerm.objects.all().exists():
        c = CurrentTerm(current_term=AcademicTerm.objects.get(year=2014,semester_type__name='Winter'))
        c.save()
    #TBP Chapters
    for state in TBP_CHAPTERS:
        for chapter in state["chapters"]:
            if len(TBPChapter.objects.filter(state__exact=state["state"]).filter(letter__exact=chapter["letter"]))==0:
                c = TBPChapter()
                c.state = state["state"]
                c.letter = chapter["letter"]
                c.school = chapter["school"]
                c.save()
            else:
                print "Chapter "+state["state"]+'-'+chapter["letter"]+" already exists."
    
    # Officer Positions
    for position in OFFICER_POSITIONS:
        if len(OfficerPosition.objects.filter(name=position["name"]))==0:
            p = OfficerPosition()
            p.name=position["name"]
            p.description=position["description"]
            p.email=position["email"]
            p.save()
        else:
            print position["name"]+" already exisits."
            
    # Standing
    for standing in STANDINGS:
        if len(Standing.objects.filter(name=standing))==0:
            s=Standing(name=standing)
            s.save()
        else:
            print "Standing "+standing+" already exists."
            
    #Status
    for status in STATUSES:
        if len(Status.objects.filter(name=status))==0:
            s=Status(name=status)
            s.save()
        else:
            print "Status "+status+" already exists."
    #Shirt Size
    for size in SHIRT_SIZES:
        if len(ShirtSize.objects.filter(name=size["name"]))==0:
            s=ShirtSize(name=size["name"],acronym=size["acronym"])
            s.save()
        else:
            print "Size "+size["name"]+" already exists."
            
    #Majors
    for major in MAJORS:
        if len(Major.objects.filter(acronym=major["acronym"]))==0:
            m = Major(name=major["name"],acronym=major["acronym"])
            m.save()
            for standing in major["standing_type"]:
                m.standing_type.add(Standing.objects.get(name=standing))
            m.save()
        else:
            print "Major: "+major["acronym"]+" already exists."
    
    #Officer Teams
    for team in OFFICER_TEAMS:
        if len(OfficerTeam.objects.filter(name=team["name"]))==0:
            t = OfficerTeam(name=team["name"])
            t.lead = OfficerPosition.objects.get(name=team["lead"])
            t.save()
            for officer in team["members"]:
                t.members.add(OfficerPosition.objects.get(name=officer))
            t.save()
        else:
            print "Team already exists: "+team["name"]
            
    # Still need to add requirement stuff: Distinction types, event categories, and requirements
    for distinction in DISTINCTIONS:
        if len(DistinctionType.objects.filter(name=distinction["name"]))==0:
            d = DistinctionType()
            d.name = distinction["name"]
            d.status_type = Status.objects.get(name=distinction["status_type"])
            d.save()
            for standing in distinction["standing_type"]:
                d.standing_type.add(Standing.objects.get(name=standing))
            d.save()
        else:
            print "Distinction: "+distinction["name"]+" already exists."

    for event_category in EVENT_CATEGORY:
        if len(EventCategory.objects.filter(name=event_category["name"]))==0:
            e=EventCategory(name=event_category["name"])
            if event_category["parent_category"]:
                e.parent_category=EventCategory.objects.get(name=event_category["parent_category"])
            e.save()
        else:
            print "Event Category: "+ event_category["name"]+" already exists."

    for distinction in REQUIREMENTS:
        for requirement in distinction["reqs"] :
            if len(Requirement.objects.filter(name=requirement["name"]).filter(distinction_type__name=distinction["name"]))==0:
                r=Requirement()
                r.name=requirement["name"]
                r.amount_required=requirement["amount_required"]
                r.event_category=EventCategory.objects.get(name=requirement["event_category"])
                r.distinction_type = DistinctionType.objects.get(name=distinction["name"])
                r.save()
                for term in requirement["term"]:
                    r.term.add(SemesterType.objects.get(name=term))
                r.save()
            else:
                print "Requirement: "+ requirement["name"]+" already exists for "+distinction["name"]
