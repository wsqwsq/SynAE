import json
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List

# Flights Ontology
FLIGHT_AIRLINES = [
    ["AA", "AA"],
    ["AB", "AB"],
    ["AC", "AC"],
    ["AD", "AD"],
    ["AE", "AE"],
    ["AF", "AF"],
    ["AG", "AG"],
    ["AH", "AH"],
    ["AI", "AI"],
    ["AJ", "AJ"],
    ["AK", "AK"],
    ["AL", "AL"],
    ["AM", "AM"],
    ["AN", "AN"],
]  # https://en.wikipedia.org/wiki/List_of_airlines_of_the_United_States
FLIGHT_CLASSES = {
    "economy": {"economy_class_option_present": [True, False], "price": (50, 300)},
    "business": {"business_class_option_present": [True, False], "price": (300, 2000)},
    "first": {"first_class_option_present": [True, False], "price": (2000, 10000)},
}
FLIGHT_LAYOVERS_AMOUNT = [0, 1, 2]
FLIGHT_LAYOVER_DURATION_MINUTES = [
    60,
    61,
    62,
    63,
    64,
    65,
    66,
    67,
    68,
    69,
    70,
    71,
    72,
    73,
    74,
    75,
    76,
    77,
    78,
    79,
    80,
    81,
    82,
    83,
    84,
    85,
    86,
    87,
    88,
    89,
    90,
    91,
    92,
    93,
    94,
    95,
    96,
    97,
    98,
    99,
    100,
    101,
    102,
    103,
    104,
    105,
    106,
    107,
    108,
    109,
    110,
    111,
    112,
    113,
    114,
    115,
    116,
    117,
    118,
    119,
    120,
    121,
    122,
    123,
    124,
    125,
    126,
    127,
    128,
    129,
    130,
    131,
    132,
    133,
    134,
    135,
    136,
    137,
    138,
    139,
    140,
    141,
    142,
    143,
    144,
    145,
    146,
    147,
    148,
    149,
    150,
    151,
    152,
    153,
    154,
    155,
    156,
    157,
    158,
    159,
    160,
    161,
    162,
    163,
    164,
    165,
    166,
    167,
    168,
    169,
    170,
    171,
    172,
    173,
    174,
    175,
    176,
    177,
    178,
    179,
    180,
    181,
    182,
    183,
    184,
    185,
    186,
    187,
    188,
    189,
    190,
    191,
    192,
    193,
    194,
    195,
    196,
    197,
    198,
    199,
    200,
    201,
    202,
    203,
    204,
    205,
    206,
    207,
    208,
    209,
    210,
    211,
    212,
    213,
    214,
    215,
    216,
    217,
    218,
    219,
    220,
    221,
    222,
    223,
    224,
    225,
    226,
    227,
    228,
    229,
    230,
    231,
    232,
    233,
    234,
    235,
    236,
    237,
    238,
    239,
    240,
    241,
    242,
    243,
    244,
    245,
    246,
    247,
    248,
    249,
    250,
    251,
    252,
    253,
    254,
    255,
    256,
    257,
    258,
    259,
    260,
    261,
    262,
    263,
    264,
    265,
    266,
    267,
    268,
    269,
    270,
    271,
    272,
    273,
    274,
    275,
    276,
    277,
    278,
    279,
    280,
    281,
    282,
    283,
    284,
    285,
    286,
    287,
    288,
    289,
    290,
    291,
    292,
    293,
    294,
    295,
    296,
    297,
    298,
    299,
    300,
    301,
    302,
    303,
    304,
    305,
    306,
    307,
    308,
    309,
    310,
    311,
    312,
    313,
    314,
    315,
    316,
    317,
    318,
    319,
    320,
    321,
    322,
    323,
    324,
    325,
    326,
    327,
    328,
    329,
    330,
    331,
    332,
    333,
    334,
    335,
    336,
    337,
    338,
    339,
    340,
    341,
    342,
    343,
    344,
    345,
    346,
    347,
    348,
    349,
    350,
    351,
    352,
    353,
    354,
    355,
    356,
    357,
    358,
    359,
    360,
]
# https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population
FLIGHT_AIRPORTS = [
    [
        "Birmingham",
        "BHM",
        "Birmingham–Shuttlesworth International Airport",
        "Alabama",
        "Small",
    ],
    ["Huntsville", "HSV", "Huntsville International Airport", "Alabama", "Small"],
    [
        "Anchorage",
        "ANC",
        "Ted Stevens Anchorage International Airport",
        "Alaska",
        "Medium",
    ],
    ["Fairbanks", "FAI", "Fairbanks International Airport", "Alaska", "Small"],
    ["Mesa", "AZA", "Mesa Gateway Airport", "Arizona", "Small"],
    ["Phoenix", "PHX", "Phoenix Sky Harbor International Airport", "Arizona", "Large"],
    ["Tucson", "TUS", "Tucson International Airport", "Arizona", "Small"],
    ["Fayetteville", "XNA", "Northwest Arkansas National Airport", "Arkansas", "Small"],
    [
        "Little Rock",
        "LIT",
        "Bill and Hillary Clinton National Airport",
        "Arkansas",
        "Small",
    ],
    ["Burbank", "BUR", "Hollywood Burbank Airport", "California", "Medium"],
    ["Fresno", "FAT", "Fresno Yosemite International Airport", "California", "Small"],
    ["Long Beach", "LGB", "Long Beach Airport", "California", "Small"],
    ["Los Angeles", "LAX", "Los Angeles International Airport", "California", "Large"],
    ["Oakland", "OAK", "Oakland International Airport", "California", "Medium"],
    ["Ontario", "ONT", "Ontario International Airport", "California", "Medium"],
    [
        "Palm Springs",
        "PSP",
        "Palm Springs International Airport",
        "California",
        "Small",
    ],
    ["Sacramento", "SMF", "Sacramento International Airport", "California", "Medium"],
    ["San Diego", "SAN", "San Diego International Airport", "California", "Large"],
    [
        "San Francisco",
        "SFO",
        "San Francisco International Airport",
        "California",
        "Large",
    ],
    ["San Jose", "SJC", "San Jose International Airport", "California", "Medium"],
    ["Santa Ana", "SNA", "John Wayne Airport", "California", "Medium"],
    ["Santa Barbara", "SBA", "Santa Barbara Municipal Airport", "California", "Small"],
    [
        "Colorado Springs",
        "COS",
        "City of Colorado Springs Municipal Airport",
        "Colorado",
        "Small",
    ],
    ["Denver", "DEN", "Denver International Airport", "Colorado", "Large"],
    ["Hartford", "BDL", "Bradley International Airport", "Connecticut", "Medium"],
    [
        "Fort Lauderdale",
        "FLL",
        "Fort Lauderdale–Hollywood International Airport",
        "Florida",
        "Large",
    ],
    [
        "Fort Myers",
        "RSW",
        "Southwest Florida International Airport",
        "Florida",
        "Medium",
    ],
    [
        "Fort Walton Beach",
        "VPS",
        "Destin–Fort Walton Beach Airport",
        "Florida",
        "Small",
    ],
    ["Jacksonville", "JAX", "Jacksonville International Airport", "Florida", "Medium"],
    ["Key West", "EYW", "Key West International Airport", "Florida", "Small"],
    ["Miami", "MIA", "Miami International Airport", "Florida", "Large"],
    ["Orlando", "MCO", "Orlando International Airport", "Florida", "Large"],
    [
        "Panama City",
        "ECP",
        "Northwest Florida Beaches International Airport",
        "Florida",
        "Small",
    ],
    ["Pensacola", "PNS", "Pensacola International Airport", "Florida", "Small"],
    ["Punta Gorda", "PGD", "Punta Gorda Airport", "Florida", "Small"],
    ["Sanford", "SFB", "Orlando Sanford International Airport", "Florida", "Small"],
    ["Sarasota", "SRQ", "Sarasota–Bradenton International Airport", "Florida", "Small"],
    [
        "St. Petersburg",
        "PIE",
        "St. Pete–Clearwater International Airport",
        "Florida",
        "Small",
    ],
    ["Tampa", "TPA", "Tampa International Airport", "Florida", "Large"],
    ["West Palm Beach", "PBI", "Palm Beach International Airport", "Florida", "Medium"],
    [
        "Atlanta",
        "ATL",
        "Hartsfield–Jackson Atlanta International Airport",
        "Georgia",
        "Large",
    ],
    [
        "Savannah",
        "SAV",
        "Savannah/Hilton Head International Airport",
        "Georgia",
        "Small",
    ],
    ["Hilo, Hawaii", "ITO", "Hilo International Airport", "Hawaii", "Small"],
    [
        "Honolulu, Oahu",
        "HNL",
        "Daniel K. Inouye International Airport",
        "Hawaii",
        "Medium",
    ],
    ["Kahului, Maui", "OGG", "Kahului Airport", "Hawaii", "Medium"],
    [
        "Kailua-Kona, Hawaii",
        "KOA",
        "Ellison Onizuka Kona International Airport at Keahole",
        "Hawaii",
        "Small",
    ],
    ["Lihue, Kauai", "LIH", "Lihue Airport", "Hawaii", "Small"],
    ["Boise", "BOI", "Boise Airport", "Idaho", "Medium"],
    ["Chicago", "MDW", "Chicago Midway International Airport", "Illinois", "Large"],
    ["Chicago", "ORD", "Chicago O'Hare International Airport", "Illinois", "Large"],
    ["Fort Wayne", "FWA", "Fort Wayne International Airport", "Indiana", "Small"],
    ["Indianapolis", "IND", "Indianapolis International Airport", "Indiana", "Medium"],
    ["South Bend", "SBN", "South Bend International Airport", "Indiana", "Small"],
    ["Cedar Rapids", "CID", "Eastern Iowa Airport", "Iowa", "Small"],
    ["Des Moines", "DSM", "Des Moines International Airport", "Iowa", "Small"],
    [
        "Wichita",
        "ICT",
        "Wichita Dwight D. Eisenhower National Airport",
        "Kansas",
        "Small",
    ],
    [
        "Hebron",
        "CVG",
        "Cincinnati/Northern Kentucky International Airport",
        "Kentucky",
        "Medium",
    ],
    ["Lexington", "LEX", "Blue Grass Airport", "Kentucky", "Small"],
    [
        "Louisville",
        "SDF",
        "Louisville Muhammad Ali International Airport",
        "Kentucky",
        "Small",
    ],
    [
        "New Orleans",
        "MSY",
        "Louis Armstrong New Orleans International Airport",
        "Louisiana",
        "Medium",
    ],
    ["Portland", "PWM", "Portland International Jetport", "Maine", "Small"],
    [
        "Baltimore",
        "BWI",
        "Baltimore/Washington International Airport",
        "Maryland",
        "Large",
    ],
    [
        "Boston",
        "BOS",
        "Gen. Edward Lawrence Logan International Airport",
        "Massachusetts",
        "Large",
    ],
    ["Detroit", "DTW", "Detroit Metro Wayne County Airport", "Michigan", "Large"],
    [
        "Grand Rapids",
        "GRR",
        "Gerald R. Ford International Airport",
        "Michigan",
        "Small",
    ],
    [
        "St. Paul",
        "MSP",
        "Minneapolis–Saint Paul International Airport",
        "Minnesota",
        "Large",
    ],
    [
        "Jackson",
        "JAN",
        "Jackson–Medgar Wiley Evers International Airport",
        "Mississippi",
        "Small",
    ],
    ["Kansas City", "MCI", "Kansas City International Airport", "Missouri", "Medium"],
    [
        "St. Louis",
        "STL",
        "St. Louis Lambert International Airport",
        "Missouri",
        "Medium",
    ],
    [
        "Springfield",
        "SGF",
        "Springfield–Branson National Airport",
        "Missouri",
        "Small",
    ],
    ["Billings", "BIL", "Billings Logan International Airport", "Montana", "Small"],
    ["Bozeman", "BZN", "Bozeman Yellowstone International Airport", "Montana", "Small"],
    ["Kalispell", "FCA", "Glacier Park International Airport", "Montana", "Small"],
    ["Missoula", "MSO", "Missoula Montana Airport", "Montana", "Small"],
    ["Omaha", "OMA", "Eppley Airfield", "Nebraska", "Medium"],
    ["Las Vegas", "LAS", "Harry Reid International Airport", "Nevada", "Large"],
    ["Reno", "RNO", "Reno/Tahoe International Airport", "Nevada", "Medium"],
    [
        "Manchester",
        "MHT",
        "Manchester–Boston Regional Airport",
        "New Hampshire",
        "Small",
    ],
    [
        "Atlantic City",
        "ACY",
        "Atlantic City International Airport",
        "New Jersey",
        "Small",
    ],
    ["Newark", "EWR", "Newark Liberty International Airport", "New Jersey", "Large"],
    ["Albuquerque", "ABQ", "Albuquerque International Sunport", "New Mexico", "Medium"],
    ["Albany", "ALB", "Albany International Airport", "New York", "Small"],
    ["Buffalo", "BUF", "Buffalo Niagara International Airport", "New York", "Small"],
    ["New York", "JFK", "John F. Kennedy International Airport", "New York", "Large"],
    ["New York", "LGA", "LaGuardia Airport", "New York", "Large"],
    ["Ronkonkoma", "ISP", "Long Island MacArthur Airport", "New York", "Small"],
    [
        "Rochester",
        "ROC",
        "Frederick Douglass/Greater Rochester International Airport",
        "New York",
        "Small",
    ],
    ["Syracuse", "SYR", "Syracuse Hancock International Airport", "New York", "Small"],
    ["White Plains", "HPN", "Westchester County Airport", "New York", "Small"],
    ["Asheville", "AVL", "Asheville Regional Airport", "North Carolina", "Small"],
    [
        "Charlotte",
        "CLT",
        "Charlotte Douglas International Airport",
        "North Carolina",
        "Large",
    ],
    [
        "Greensboro",
        "GSO",
        "Piedmont Triad International Airport",
        "North Carolina",
        "Small",
    ],
    [
        "Raleigh",
        "RDU",
        "Raleigh–Durham International Airport",
        "North Carolina",
        "Medium",
    ],
    [
        "Wilmington",
        "ILM",
        "Wilmington International Airport",
        "North Carolina",
        "Small",
    ],
    ["Fargo", "FAR", "Hector International Airport", "North Dakota", "Small"],
    ["Cleveland", "CLE", "Cleveland Hopkins International Airport", "Ohio", "Medium"],
    ["Columbus", "CMH", "John Glenn Columbus International Airport", "Ohio", "Medium"],
    ["Dayton", "DAY", "James M. Cox Dayton International Airport", "Ohio", "Small"],
    [
        "Oklahoma City",
        "OKC",
        "OKC Will Rogers International Airport",
        "Oklahoma",
        "Small",
    ],
    ["Tulsa", "TUL", "Tulsa International Airport", "Oklahoma", "Small"],
    ["Eugene", "EUG", "Mahlon Sweet Field", "Oregon", "Small"],
    ["Medford", "MFR", "Rogue Valley International–Medford Airport", "Oregon", "Small"],
    ["Portland", "PDX", "Portland International Airport", "Oregon", "Medium"],
    ["Redmond", "RDM", "Roberts Field", "Oregon", "Small"],
    [
        "Allentown",
        "ABE",
        "Lehigh Valley International Airport",
        "Pennsylvania",
        "Small",
    ],
    ["Harrisburg", "MDT", "Harrisburg International Airport", "Pennsylvania", "Small"],
    [
        "Philadelphia",
        "PHL",
        "Philadelphia International Airport",
        "Pennsylvania",
        "Large",
    ],
    ["Pittsburgh", "PIT", "Pittsburgh International Airport", "Pennsylvania", "Medium"],
    [
        "Providence",
        "PVD",
        "Rhode Island T. F. Green International Airport",
        "Rhode Island",
        "Small",
    ],
    [
        "Charleston",
        "CHS",
        "Charleston International Airport",
        "South Carolina",
        "Medium",
    ],
    ["Columbia", "CAE", "Columbia Metropolitan Airport", "South Carolina", "Small"],
    [
        "Greenville",
        "GSP",
        "Greenville–Spartanburg International Airport",
        "South Carolina",
        "Small",
    ],
    [
        "Myrtle Beach",
        "MYR",
        "Myrtle Beach International Airport",
        "South Carolina",
        "Small",
    ],
    ["Rapid City", "RAP", "Rapid City Regional Airport", "South Dakota", "Small"],
    ["Sioux Falls", "FSD", "Sioux Falls Regional Airport", "South Dakota", "Small"],
    ["Chattanooga", "CHA", "Chattanooga Metropolitan Airport", "Tennessee", "Small"],
    ["Knoxville", "TYS", "McGhee Tyson Airport", "Tennessee", "Small"],
    ["Memphis", "MEM", "Memphis International Airport", "Tennessee", "Medium"],
    ["Nashville", "BNA", "Nashville International Airport", "Tennessee", "Large"],
    ["Austin", "AUS", "Austin–Bergstrom International Airport", "Texas", "Large"],
    ["Dallas", "DAL", "Dallas Love Field", "Texas", "Medium"],
    [
        "Dallas",
        "DFW",
        "Dallas Fort Worth International Airport",
        "Texas",
        "Large",
    ],
    ["El Paso", "ELP", "El Paso International Airport", "Texas", "Small"],
    ["Harlingen", "HRL", "Valley International Airport", "Texas", "Small"],
    [
        "Houston",
        "IAH",
        "George Bush Intercontinental/Houston Airport",
        "Texas",
        "Large",
    ],
    ["Houston", "HOU", "William P. Hobby Airport", "Texas", "Medium"],
    ["Lubbock", "LBB", "Lubbock Preston Smith International Airport", "Texas", "Small"],
    ["McAllen", "MFE", "McAllen Miller International Airport", "Texas", "Small"],
    [
        "Midland",
        "MAF",
        "Midland International Air and Space Port",
        "Texas",
        "Small",
    ],
    ["San Antonio", "SAT", "San Antonio International Airport", "Texas", "Medium"],
    ["Salt Lake City", "SLC", "Salt Lake City International Airport", "Utah", "Large"],
    [
        "Burlington",
        "BTV",
        "Patrick Leahy Burlington International Airport",
        "Vermont",
        "Small",
    ],
    ["Norfolk", "ORF", "Norfolk International Airport", "Virginia", "Small"],
    ["Richmond", "RIC", "Richmond International Airport", "Virginia", "Small"],
    [
        "Arlington",
        "DCA",
        "Ronald Reagan Washington National Airport",
        "Virginia",
        "Large",
    ],
    [
        "Dulles",
        "IAD",
        "Washington Dulles International Airport",
        "Virginia",
        "Large",
    ],
    ["Pasco", "PSC", "Tri-Cities Airport", "Washington", "Small"],
    [
        "SeaTac",
        "SEA",
        "Seattle–Tacoma International Airport",
        "Washington",
        "Large",
    ],
    ["Spokane", "GEG", "Spokane International Airport", "Washington", "Small"],
    [
        "Greenville",
        "ATW",
        "Appleton International Airport",
        "Wisconsin",
        "Small",
    ],
    ["Madison", "MSN", "Dane County Regional Airport", "Wisconsin", "Small"],
    [
        "Milwaukee",
        "MKE",
        "Milwaukee Mitchell International Airport",
        "Wisconsin",
        "Medium",
    ],
    ["Jackson", "JAC", "Jackson Hole Airport", "Wyoming", "Small"],
    [
        "Carolina",
        "SJU",
        "Luis Muñoz Marín International Airport",
        "Puerto Rico",
        "Medium",
    ],
    [
        "St. Thomas",
        "STT",
        "Cyril E. King Airport",
        "U.S. Virgin Islands",
        "Small",
    ],
]

# Cities Ontology
CITIES = [
    ["New York", "NY"],
    ["Los Angeles", "CA"],
    ["Chicago", "IL"],
    ["Houston", "TX"],
    ["Phoenix", "AZ"],
    ["Philadelphia", "PA"],
    ["San Antonio", "TX"],
    ["San Diego", "CA"],
    ["Dallas", "TX"],
    ["Jacksonville", "FL"],
    ["Austin", "TX"],
    ["Fort Worth", "TX"],
    ["San Jose", "CA"],
    ["Columbus", "OH"],
    ["Charlotte", "NC"],
    ["Indianapolis", "IN"],
    ["San Francisco", "CA"],
    ["Seattle", "WA"],
    ["Denver", "CO"],
    ["Oklahoma City", "OK"],
    ["Nashville", "TN"],
    ["Washington", "DC"],
    ["El Paso", "TX"],
    ["Las Vegas", "NV"],
    ["Boston", "MA"],
    ["Detroit", "MI"],
    ["Portland", "OR"],
    ["Louisville", "KY"],
    ["Memphis", "TN"],
    ["Baltimore", "MD"],
    ["Milwaukee", "WI"],
    ["Albuquerque", "NM"],
    ["Tucson", "AZ"],
    ["Fresno", "CA"],
    ["Sacramento", "CA"],
    ["Mesa", "AZ"],
    ["Atlanta", "GA"],
    ["Kansas City", "MO"],
    ["Colorado Springs", "CO"],
    ["Omaha", "NE"],
    ["Raleigh", "NC"],
    ["Miami", "FL"],
    ["Virginia Beach", "VA"],
    ["Long Beach", "CA"],
    ["Oakland", "CA"],
    ["Minneapolis", "MN"],
    ["Bakersfield", "CA"],
    ["Tulsa", "OK"],
    ["Tampa", "FL"],
    ["Arlington", "TX"],
    ["Wichita", "KS"],
    ["Aurora", "CO"],
    ["New Orleans", "LA"],
    ["Cleveland", "OH"],
    ["Honolulu", "HI"],
    ["Anaheim", "CA"],
    ["Henderson", "NV"],
    ["Orlando", "FL"],
    ["Lexington", "KY"],
    ["Stockton", "CA"],
    ["Riverside", "CA"],
    ["Corpus Christi", "TX"],
    ["Irvine", "CA"],
    ["Cincinnati", "OH"],
    ["Santa Ana", "CA"],
    ["Newark", "NJ"],
    ["Saint Paul", "MN"],
    ["Pittsburgh", "PA"],
    ["Greensboro", "NC"],
    ["Durham", "NC"],
    ["Lincoln", "NE"],
    ["Jersey City", "NJ"],
    ["Plano", "TX"],
    ["Anchorage", "AK"],
    ["North Las Vegas", "NV"],
    ["St. Louis", "MO"],
    ["Madison", "WI"],
    ["Chandler", "AZ"],
    ["Gilbert", "AZ"],
    ["Reno", "NV"],
    ["Buffalo", "NY"],
    ["Chula Vista", "CA"],
    ["Fort Wayne", "IN"],
    ["Lubbock", "TX"],
    ["Toledo", "OH"],
    ["St. Petersburg", "FL"],
    ["Laredo", "TX"],
    ["Irving", "TX"],
    ["Chesapeake", "VA"],
    ["Glendale", "AZ"],
    ["Winston-Salem", "NC"],
    ["Port St. Lucie", "FL"],
    ["Scottsdale", "AZ"],
    ["Garland", "TX"],
    ["Boise", "ID"],
    ["Norfolk", "VA"],
    ["Spokane", "WA"],
    ["Richmond", "VA"],
    ["Fremont", "CA"],
    ["Huntsville", "AL"],
    ["Frisco", "TX"],
    ["Cape Coral", "FL"],
    ["Santa Clarita", "CA"],
    ["San Bernardino", "CA"],
    ["Tacoma", "WA"],
    ["Hialeah", "FL"],
    ["Baton Rouge", "LA"],
    ["Modesto", "CA"],
    ["Fontana", "CA"],
    ["McKinney", "TX"],
    ["Moreno Valley", "CA"],
    ["Des Moines", "IA"],
    ["Fayetteville", "NC"],
    ["Salt Lake City", "UT"],
    ["Yonkers", "NY"],
    ["Worcester", "MA"],
    ["Rochester", "NY"],
    ["Sioux Falls", "SD"],
    ["Little Rock", "AR"],
    ["Amarillo", "TX"],
    ["Tallahassee", "FL"],
    ["Grand Prairie", "TX"],
    ["Columbus", "GA"],
    ["Augusta", "GA"],
    ["Peoria", "AZ"],
    ["Oxnard", "CA"],
    ["Knoxville", "TN"],
    ["Overland Park", "KS"],
    ["Birmingham", "AL"],
    ["Grand Rapids", "MI"],
    ["Vancouver", "WA"],
    ["Montgomery", "AL"],
    ["Huntington Beach", "CA"],
    ["Providence", "RI"],
    ["Brownsville", "TX"],
    ["Tempe", "AZ"],
    ["Akron", "OH"],
    ["Glendale", "CA"],
    ["Chattanooga", "TN"],
    ["Fort Lauderdale", "FL"],
    ["Newport News", "VA"],
    ["Mobile", "AL"],
    ["Ontario", "CA"],
    ["Clarksville", "TN"],
    ["Cary", "NC"],
    ["Elk Grove", "CA"],
    ["Shreveport", "LA"],
    ["Eugene", "OR"],
    ["Aurora", "IL"],
    ["Salem", "OR"],
    ["Santa Rosa", "CA"],
    ["Rancho Cucamonga", "CA"],
    ["Pembroke Pines", "FL"],
    ["Fort Collins", "CO"],
    ["Springfield", "MO"],
    ["Oceanside", "CA"],
    ["Garden Grove", "CA"],
    ["Lancaster", "CA"],
    ["Murfreesboro", "TN"],
    ["Palmdale", "CA"],
    ["Corona", "CA"],
    ["Killeen", "TX"],
    ["Salinas", "CA"],
    ["Roseville", "CA"],
    ["Denton", "TX"],
    ["Surprise", "AZ"],
    ["Macon", "GA"],
    ["Paterson", "NJ"],
    ["Lakewood", "CO"],
    ["Hayward", "CA"],
    ["Charleston", "SC"],
    ["Alexandria", "VA"],
    ["Hollywood", "FL"],
    ["Springfield", "MA"],
    ["Kansas City", "KS"],
    ["Sunnyvale", "CA"],
    ["Bellevue", "WA"],
    ["Joliet", "IL"],
    ["Naperville", "IL"],
    ["Escondido", "CA"],
    ["Bridgeport", "CT"],
    ["Savannah", "GA"],
    ["Olathe", "KS"],
    ["Mesquite", "TX"],
    ["Pasadena", "TX"],
    ["McAllen", "TX"],
    ["Rockford", "IL"],
    ["Gainesville", "FL"],
    ["Syracuse", "NY"],
    ["Pomona", "CA"],
    ["Visalia", "CA"],
    ["Thornton", "CO"],
    ["Waco", "TX"],
    ["Jackson", "MS"],
    ["Columbia", "SC"],
    ["Lakewood", "NJ"],
    ["Fullerton", "CA"],
    ["Torrance", "CA"],
    ["Victorville", "CA"],
    ["Midland", "TX"],
    ["Orange", "CA"],
    ["Miramar", "FL"],
    ["Hampton", "VA"],
    ["Warren", "MI"],
    ["Stamford", "CT"],
    ["Cedar Rapids", "IA"],
    ["Elizabeth", "NJ"],
    ["Palm Bay", "FL"],
    ["Dayton", "OH"],
    ["New Haven", "CT"],
    ["Coral Springs", "FL"],
    ["Meridian", "ID"],
    ["West Valley City", "UT"],
    ["Pasadena", "CA"],
    ["Lewisville", "TX"],
    ["Kent", "WA"],
    ["Sterling Heights", "MI"],
    ["Fargo", "ND"],
    ["Carrollton", "TX"],
    ["Santa Clara", "CA"],
    ["Round Rock", "TX"],
    ["Norman", "OK"],
    ["Columbia", "MO"],
    ["Abilene", "TX"],
    ["Athens", "GA"],
    ["Pearland", "TX"],
    ["Clovis", "CA"],
    ["Topeka", "KS"],
    ["College Station", "TX"],
    ["Simi Valley", "CA"],
    ["Allentown", "PA"],
    ["West Palm Beach", "FL"],
    ["Thousand Oaks", "CA"],
    ["Vallejo", "CA"],
    ["Wilmington", "NC"],
    ["Rochester", "MN"],
    ["Concord", "CA"],
    ["Lakeland", "FL"],
    ["North Charleston", "SC"],
    ["Lafayette", "LA"],
    ["Arvada", "CO"],
    ["Independence", "MO"],
    ["Billings", "MT"],
    ["Fairfield", "CA"],
    ["Hartford", "CT"],
    ["Ann Arbor", "MI"],
    ["Broken Arrow", "OK"],
    ["Berkeley", "CA"],
    ["Cambridge", "MA"],
    ["Richardson", "TX"],
    ["Antioch", "CA"],
    ["High Point", "NC"],
    ["Clearwater", "FL"],
    ["League City", "TX"],
    ["Odessa", "TX"],
    ["Manchester", "NH"],
    ["Evansville", "IN"],
    ["Waterbury", "CT"],
    ["West Jordan", "UT"],
    ["Las Cruces", "NM"],
    ["Westminster", "CO"],
    ["Lowell", "MA"],
    ["Nampa", "ID"],
    ["Richmond", "CA"],
    ["Pompano Beach", "FL"],
    ["Carlsbad", "CA"],
    ["Menifee", "CA"],
    ["Provo", "UT"],
    ["Elgin", "IL"],
    ["Greeley", "CO"],
    ["Springfield", "IL"],
    ["Beaumont", "TX"],
    ["Lansing", "MI"],
    ["Murrieta", "CA"],
    ["Goodyear", "AZ"],
    ["Allen", "TX"],
    ["Tuscaloosa", "AL"],
    ["Everett", "WA"],
    ["Pueblo", "CO"],
    ["New Braunfels", "TX"],
    ["South Fulton", "GA"],
    ["Miami Gardens", "FL"],
    ["Gresham", "OR"],
    ["Temecula", "CA"],
    ["Rio Rancho", "NM"],
    ["Peoria", "IL"],
    ["Tyler", "TX"],
    ["Sparks", "NV"],
    ["Concord", "NC"],
    ["Santa Maria", "CA"],
    ["Ventura", "CA"],
    ["Buckeye", "AZ"],
    ["Downey", "CA"],
    ["Sugar Land", "TX"],
    ["Costa Mesa", "CA"],
    ["Conroe", "TX"],
    ["Spokane Valley", "WA"],
    ["Davie", "FL"],
    ["Hillsboro", "OR"],
    ["Jurupa Valley", "CA"],
    ["Centennial", "CO"],
    ["Edison", "NJ"],
    ["Boulder", "CO"],
    ["Dearborn", "MI"],
    ["Edinburg", "TX"],
    ["Sandy Springs", "GA"],
    ["Green Bay", "WI"],
    ["West Covina", "CA"],
    ["Brockton", "MA"],
    ["St. George", "UT"],
    ["Bend", "OR"],
    ["Renton", "WA"],
    ["Lee's Summit", "MO"],
    ["Fishers", "IN"],
    ["El Monte", "CA"],
    ["South Bend", "IN"],
    ["Rialto", "CA"],
    ["Woodbridge", "NJ"],
    ["El Cajon", "CA"],
    ["Inglewood", "CA"],
    ["Burbank", "CA"],
    ["Wichita Falls", "TX"],
    ["Vacaville", "CA"],
    ["Carmel", "IN"],
    ["Palm Coast", "FL"],
    ["Fayetteville", "AR"],
    ["Quincy", "MA"],
    ["San Mateo", "CA"],
    ["Chico", "CA"],
    ["Lynn", "MA"],
    ["Albany", "NY"],
    ["Yuma", "AZ"],
    ["New Bedford", "MA"],
    ["Suffolk", "VA"],
    ["Hesperia", "CA"],
]
city_neighborhoods_dict = {
    "New York,NY": [
        {"neighborhood": "Manhattan", "latitude": 40.7127, "longitude": -74.0059},
        {"neighborhood": "Brooklyn", "latitude": 40.65, "longitude": -73.95},
        {"neighborhood": "Queens", "latitude": 40.75, "longitude": -73.86666667},
        {
            "neighborhood": "The Bronx",
            "latitude": 40.83722222,
            "longitude": -73.88611111,
        },
        {"neighborhood": "Staten Island", "latitude": 40.58333333, "longitude": -74.15},
    ],
    "Los Angeles,CA": [
        {
            "neighborhood": "Hollywood",
            "latitude": 34.10166667,
            "longitude": -118.32666667,
        },
        {
            "neighborhood": "Beverly Hills",
            "latitude": 34.07305556,
            "longitude": -118.39944444,
        },
        {
            "neighborhood": "Santa Monica",
            "latitude": 34.01583333,
            "longitude": -118.45138889,
        },
        {"neighborhood": "Venice", "latitude": 33.99083333, "longitude": -118.45916667},
        {"neighborhood": "Downtown LA", "latitude": 34.05, "longitude": -118.25},
    ],
    "Chicago,IL": [
        {
            "neighborhood": "The Loop",
            "latitude": 41.88111111,
            "longitude": -87.62972222,
        },
        {"neighborhood": "Lincoln Park", "latitude": 41.92, "longitude": -87.65},
        {"neighborhood": "Wicker Park", "latitude": 41.9075, "longitude": -87.67694444},
        {"neighborhood": "Bucktown", "latitude": 41.9, "longitude": -87.68},
        {
            "neighborhood": "Logan Square",
            "latitude": 41.88908333,
            "longitude": -87.64433333,
        },
    ],
    "Houston,TX": [
        {
            "neighborhood": "Downtown Houston",
            "latitude": 29.756334,
            "longitude": -95.364037,
        },
        {"neighborhood": "Montrose", "latitude": 29.74, "longitude": -95.391},
        {
            "neighborhood": "The Heights",
            "latitude": 29.76277778,
            "longitude": -95.38305556,
        },
        {"neighborhood": "River Oaks", "latitude": 29.751, "longitude": -95.433},
        {"neighborhood": "Galleria", "latitude": 29.7407, "longitude": -95.4636},
    ],
    "Phoenix,AZ": [
        {
            "neighborhood": "Roosevelt Row",
            "latitude": 33.44833333,
            "longitude": -112.07388889,
        },
        {
            "neighborhood": "Arcadia",
            "latitude": 33.44833333,
            "longitude": -112.07388889,
        },
        {
            "neighborhood": "Camelback East",
            "latitude": 33.44833333,
            "longitude": -112.07388889,
        },
        {
            "neighborhood": "Glendale",
            "latitude": 33.53861111,
            "longitude": -112.18638889,
        },
    ],
    "Philadelphia,PA": [
        {"neighborhood": "Center City", "latitude": 39.952, "longitude": -75.164},
        {"neighborhood": "Fishtown", "latitude": 39.965, "longitude": -75.135},
        {
            "neighborhood": "Northern Liberties",
            "latitude": 39.96305556,
            "longitude": -75.145,
        },
        {"neighborhood": "Society Hill", "latitude": 39.945, "longitude": -75.149},
        {
            "neighborhood": "University City",
            "latitude": 39.95277778,
            "longitude": -75.16361111,
        },
    ],
    "San Antonio,TX": [
        {
            "neighborhood": "Downtown San Antonio",
            "latitude": 29.425,
            "longitude": -98.49388889,
        },
        {
            "neighborhood": "Alamo Heights",
            "latitude": 29.42583333,
            "longitude": -98.48611111,
        },
        {"neighborhood": "King William", "latitude": 29.425, "longitude": -98.49388889},
        {
            "neighborhood": "Pearl District",
            "latitude": 29.425,
            "longitude": -98.49388889,
        },
        {"neighborhood": "Monte Vista", "latitude": 29.425, "longitude": -98.49388889},
    ],
    "San Diego,CA": [
        {
            "neighborhood": "Gaslamp Quarter",
            "latitude": 32.71166667,
            "longitude": -117.15916667,
        },
        {"neighborhood": "La Jolla", "latitude": 32.84, "longitude": -117.27694444},
        {
            "neighborhood": "North Park",
            "latitude": 32.74083056,
            "longitude": -117.12971944,
        },
        {
            "neighborhood": "Little Italy",
            "latitude": 32.72055556,
            "longitude": -117.15444444,
        },
    ],
    "Dallas,TX": [
        {"neighborhood": "Uptown", "latitude": 32.80061111, "longitude": -96.79980556},
        {
            "neighborhood": "Deep Ellum",
            "latitude": 32.78444444,
            "longitude": -96.78055556,
        },
        {
            "neighborhood": "Bishop Arts District",
            "latitude": 32.74895278,
            "longitude": -96.82833889,
        },
    ],
    "Jacksonville,FL": [
        {
            "neighborhood": "Downtown Jacksonville",
            "latitude": 30.33694444,
            "longitude": -81.66138889,
        }
    ],
    "Austin,TX": [
        {"neighborhood": "Downtown Austin", "latitude": 30.271, "longitude": -97.743},
        {
            "neighborhood": "South Congress",
            "latitude": 30.26722222,
            "longitude": -97.74305556,
        },
        {
            "neighborhood": "East Austin",
            "latitude": 30.26722222,
            "longitude": -97.74305556,
        },
        {"neighborhood": "Hyde Park", "latitude": 30.30583333, "longitude": -97.73},
        {
            "neighborhood": "Clarksville",
            "latitude": 30.26722222,
            "longitude": -97.74305556,
        },
    ],
    "Fort Worth,TX": [
        {
            "neighborhood": "Downtown Fort Worth",
            "latitude": 32.89694444,
            "longitude": -97.03805556,
        },
        {
            "neighborhood": "Stockyards National Historic District",
            "latitude": 32.755,
            "longitude": -97.33,
        },
        {
            "neighborhood": "Cultural District",
            "latitude": 32.75638889,
            "longitude": -97.3325,
        },
        {
            "neighborhood": "Near Southside",
            "latitude": 32.75638889,
            "longitude": -97.3325,
        },
        {"neighborhood": "Tanglewood", "latitude": 32.75638889, "longitude": -97.3325},
    ],
    "San Jose,CA": [
        {
            "neighborhood": "Downtown San Jose",
            "latitude": 37.3353,
            "longitude": -121.8813,
        },
        {"neighborhood": "Willow Glen", "latitude": 37.30357, "longitude": -121.897345},
        {"neighborhood": "Almaden Valley", "latitude": 37.2214, "longitude": -121.8622},
        {
            "neighborhood": "Santana Row",
            "latitude": 37.32027778,
            "longitude": -121.94777778,
        },
    ],
    "Columbus,OH": [
        {
            "neighborhood": "Downtown Columbus",
            "latitude": 39.96669444,
            "longitude": -83.0,
        },
        {
            "neighborhood": "German Village",
            "latitude": 39.96222222,
            "longitude": -83.00055556,
        },
        {
            "neighborhood": "Clintonville",
            "latitude": 39.96222222,
            "longitude": -83.00055556,
        },
        {
            "neighborhood": "Victorian Village",
            "latitude": 39.96222222,
            "longitude": -83.00055556,
        },
    ],
    "Charlotte,NC": [
        {"neighborhood": "NoDa", "latitude": 35.22722222, "longitude": -80.84305556},
        {
            "neighborhood": "Plaza Midwood",
            "latitude": 35.22722222,
            "longitude": -80.84305556,
        },
        {
            "neighborhood": "Elizabeth",
            "latitude": 35.22722222,
            "longitude": -80.84305556,
        },
        {"neighborhood": "Myers Park", "latitude": 35.1925, "longitude": -80.83305556},
    ],
    "Indianapolis,IN": [
        {
            "neighborhood": "Downtown Indianapolis",
            "latitude": 39.76694444,
            "longitude": -86.17694444,
        },
        {"neighborhood": "Mass Ave", "latitude": 39.775, "longitude": -86.14861111},
        {
            "neighborhood": "Fountain Square",
            "latitude": 39.75222222,
            "longitude": -86.14,
        },
        {
            "neighborhood": "Carmel Arts District",
            "latitude": 39.96805556,
            "longitude": -86.1125,
        },
    ],
    "San Francisco,CA": [
        {
            "neighborhood": "Fisherman's Wharf",
            "latitude": 37.80833333,
            "longitude": -122.41555556,
        },
        {"neighborhood": "Haight-Ashbury", "latitude": 37.77, "longitude": -122.4469},
        {
            "neighborhood": "The Mission District",
            "latitude": 37.76,
            "longitude": -122.42,
        },
        {
            "neighborhood": "Chinatown",
            "latitude": 37.79416667,
            "longitude": -122.40694444,
        },
        {
            "neighborhood": "Pacific Heights",
            "latitude": 37.7917,
            "longitude": -122.4356,
        },
    ],
    "Seattle,WA": [
        {
            "neighborhood": "Pioneer Square",
            "latitude": 47.60166667,
            "longitude": -122.33194444,
        },
        {
            "neighborhood": "Capitol Hill",
            "latitude": 47.61666667,
            "longitude": -122.31666667,
        },
        {"neighborhood": "Ballard", "latitude": 47.677, "longitude": -122.385},
        {"neighborhood": "Fremont", "latitude": 47.6505, "longitude": -122.3499},
        {"neighborhood": "Queen Anne", "latitude": 47.625, "longitude": -122.35916667},
    ],
    "Denver,CO": [
        {"neighborhood": "LoDo", "latitude": 39.7392, "longitude": -104.9849},
        {"neighborhood": "Larimer Square", "latitude": 40.65, "longitude": -105.46},
        {
            "neighborhood": "Highland",
            "latitude": 39.76263889,
            "longitude": -105.01191111,
        },
        {
            "neighborhood": "Capitol Hill",
            "latitude": 39.73333333,
            "longitude": -104.98333333,
        },
        {
            "neighborhood": "Cherry Creek",
            "latitude": 39.75455556,
            "longitude": -105.00822222,
        },
    ],
    "Oklahoma City,OK": [
        {
            "neighborhood": "Downtown Oklahoma City",
            "latitude": 35.40138889,
            "longitude": -97.90472222,
        },
        {"neighborhood": "Bricktown", "latitude": 35.466419, "longitude": -97.5091},
        {
            "neighborhood": "Plaza District",
            "latitude": 36.13138889,
            "longitude": -95.93722222,
        },
        {
            "neighborhood": "Automobile Alley",
            "latitude": 35.46861111,
            "longitude": -97.52138889,
        },
        {"neighborhood": "Midtown", "latitude": 35.46861111, "longitude": -97.52138889},
    ],
    "Nashville,TN": [
        {
            "neighborhood": "Downtown Nashville",
            "latitude": 36.16222222,
            "longitude": -86.77444444,
        },
        {
            "neighborhood": "The Gulch",
            "latitude": 36.16222222,
            "longitude": -86.77444444,
        },
        {
            "neighborhood": "12 South",
            "latitude": 36.16222222,
            "longitude": -86.77444444,
        },
        {
            "neighborhood": "East Nashville",
            "latitude": 36.14972222,
            "longitude": -86.81333333,
        },
        {
            "neighborhood": "Germantown",
            "latitude": 36.16222222,
            "longitude": -86.77444444,
        },
    ],
    "Washington,DC": [
        {"neighborhood": "Georgetown", "latitude": 38.90944444, "longitude": -77.065},
        {
            "neighborhood": "Dupont Circle",
            "latitude": 38.90944444,
            "longitude": -77.04333333,
        },
        {"neighborhood": "Adams Morgan", "latitude": 38.92261, "longitude": -77.042661},
        {"neighborhood": "Columbia Heights", "latitude": 38.925, "longitude": -77.03},
        {
            "neighborhood": "Capitol Hill",
            "latitude": 38.88972222,
            "longitude": -77.01111111,
        },
    ],
    "El Paso,TX": [
        {
            "neighborhood": "Downtown El Paso",
            "latitude": 31.73944444,
            "longitude": -106.48694444,
        },
        {
            "neighborhood": "El Paso Mission Trail",
            "latitude": 31.77305556,
            "longitude": -106.49111111,
        },
        {
            "neighborhood": "Kern Place",
            "latitude": 31.75916667,
            "longitude": -106.48861111,
        },
        {
            "neighborhood": "Mesilla Valley",
            "latitude": 31.75916667,
            "longitude": -106.48861111,
        },
        {
            "neighborhood": "Westside",
            "latitude": 31.75916667,
            "longitude": -106.48861111,
        },
    ],
    "Las Vegas,NV": [
        {
            "neighborhood": "Summerlin",
            "latitude": 36.18333333,
            "longitude": -115.33333333,
        }
    ],
    "Boston,MA": [
        {"neighborhood": "Beacon Hill", "latitude": 42.3583, "longitude": -71.0661},
        {"neighborhood": "North End", "latitude": 42.365, "longitude": -71.05444444},
        {
            "neighborhood": "Fenway-Kenmore",
            "latitude": 42.34205278,
            "longitude": -71.10025278,
        },
        {
            "neighborhood": "Charlestown",
            "latitude": 42.37527778,
            "longitude": -71.06444444,
        },
    ],
    "Detroit,MI": [
        {
            "neighborhood": "Downtown Detroit",
            "latitude": 42.33333333,
            "longitude": -83.05,
        },
        {
            "neighborhood": "Midtown Detroit",
            "latitude": 42.35055556,
            "longitude": -83.05944444,
        },
        {
            "neighborhood": "Eastern Market",
            "latitude": 42.33333333,
            "longitude": -83.05,
        },
        {"neighborhood": "Corktown", "latitude": 42.33333333, "longitude": -83.05},
        {"neighborhood": "Rivertown", "latitude": 42.33333333, "longitude": -83.05},
    ],
    "Portland,OR": [
        {
            "neighborhood": "Downtown Portland",
            "latitude": 45.51935,
            "longitude": -122.67962,
        },
        {
            "neighborhood": "Pearl District",
            "latitude": 45.53012,
            "longitude": -122.68136,
        },
        {
            "neighborhood": "Alberta Arts District",
            "latitude": 45.55905,
            "longitude": -122.64286,
        },
        {
            "neighborhood": "Hawthorne District",
            "latitude": 45.51245,
            "longitude": -122.62081,
        },
    ],
    "Louisville,KY": [
        {
            "neighborhood": "Downtown Louisville",
            "latitude": 38.25611111,
            "longitude": -85.75138889,
        },
        {
            "neighborhood": "Old Louisville",
            "latitude": 38.22995,
            "longitude": -85.76297,
        },
        {
            "neighborhood": "Highlands",
            "latitude": 38.25611111,
            "longitude": -85.75138889,
        },
    ],
    "Memphis,TN": [
        {
            "neighborhood": "Downtown Memphis",
            "latitude": 35.1389,
            "longitude": -90.0575,
        },
        {
            "neighborhood": "Cooper-Young",
            "latitude": 35.1175,
            "longitude": -89.97111111,
        },
        {
            "neighborhood": "Overton Square",
            "latitude": 35.1175,
            "longitude": -89.97111111,
        },
        {"neighborhood": "Midtown Memphis", "latitude": 35.145, "longitude": -89.99},
    ],
    "Baltimore,MD": [
        {
            "neighborhood": "Inner Harbor",
            "latitude": 39.283494,
            "longitude": -76.609897,
        },
        {
            "neighborhood": "Fell's Point",
            "latitude": 39.28305556,
            "longitude": -76.59277778,
        },
        {
            "neighborhood": "Mount Vernon",
            "latitude": 39.29833333,
            "longitude": -76.61666667,
        },
        {"neighborhood": "Federal Hill", "latitude": 39.27888889, "longitude": -76.61},
        {"neighborhood": "Canton", "latitude": 39.28944444, "longitude": -76.61527778},
    ],
    "Milwaukee,WI": [
        {"neighborhood": "Riverwest", "latitude": 43.05, "longitude": -87.95},
        {"neighborhood": "Downtown Milwaukee", "latitude": 43.05, "longitude": -87.95},
        {
            "neighborhood": "Bay View",
            "latitude": 42.99166667,
            "longitude": -87.89583333,
        },
        {"neighborhood": "Shorewood", "latitude": 43.05, "longitude": -87.95},
        {"neighborhood": "Wauwatosa", "latitude": 43.05, "longitude": -87.95},
    ],
    "Albuquerque,NM": [
        {
            "neighborhood": "Downtown Albuquerque",
            "latitude": 35.08444444,
            "longitude": -106.65027778,
        },
        {
            "neighborhood": "Old Town",
            "latitude": 35.09611111,
            "longitude": -106.66986111,
        },
        {
            "neighborhood": "Nob Hill",
            "latitude": 35.07972222,
            "longitude": -106.60444444,
        },
        {
            "neighborhood": "University Heights",
            "latitude": 35.08444444,
            "longitude": -106.65027778,
        },
        {"neighborhood": "Uptown", "latitude": 35.08444444, "longitude": -106.65027778},
    ],
    "Tucson,AZ": [
        {
            "neighborhood": "Downtown Tucson",
            "latitude": 32.22166667,
            "longitude": -110.92638889,
        },
        {
            "neighborhood": "4th Avenue",
            "latitude": 32.22166667,
            "longitude": -110.92638889,
        },
        {
            "neighborhood": "El Presidio San Agustín del Tucson",
            "latitude": 32.22166667,
            "longitude": -110.92638889,
        },
        {
            "neighborhood": "Sam Hughes",
            "latitude": 32.22166667,
            "longitude": -110.92638889,
        },
    ],
    "Fresno,CA": [
        {
            "neighborhood": "Downtown Fresno",
            "latitude": 36.75,
            "longitude": -119.76666667,
        },
        {"neighborhood": "Tower District", "latitude": 36.75, "longitude": -119.65},
        {"neighborhood": "Figarden", "latitude": 36.82277778, "longitude": -119.8625},
        {
            "neighborhood": "Woodward Park",
            "latitude": 36.75,
            "longitude": -119.76666667,
        },
    ],
    "Sacramento,CA": [
        {
            "neighborhood": "Downtown Sacramento",
            "latitude": 38.58055556,
            "longitude": -121.53027778,
        },
        {"neighborhood": "Midtown Sacramento", "latitude": 38.57, "longitude": -121.45},
        {"neighborhood": "Old Sacramento", "latitude": 38.45, "longitude": -121.35},
        {"neighborhood": "East Sacramento", "latitude": 38.57, "longitude": -121.45},
    ],
    "Mesa,AZ": [
        {
            "neighborhood": "Downtown Mesa",
            "latitude": 33.42222222,
            "longitude": -111.82277778,
        },
        {
            "neighborhood": "Mesa Grande",
            "latitude": 33.42222222,
            "longitude": -111.82277778,
        },
        {
            "neighborhood": "Dobson Ranch",
            "latitude": 33.42222222,
            "longitude": -111.82277778,
        },
        {
            "neighborhood": "Red Mountain Ranch",
            "latitude": 33.42222222,
            "longitude": -111.82277778,
        },
    ],
    "Atlanta,GA": [
        {
            "neighborhood": "Midtown Atlanta",
            "latitude": 33.7868014,
            "longitude": -84.3795169,
        },
        {"neighborhood": "Buckhead", "latitude": 33.83942, "longitude": -84.37992},
        {
            "neighborhood": "Virginia-Highland",
            "latitude": 33.74888889,
            "longitude": -84.39,
        },
        {"neighborhood": "Inman Park", "latitude": 33.74888889, "longitude": -84.39},
    ],
    "Kansas City,MO": [
        {
            "neighborhood": "Downtown Kansas City",
            "latitude": 39.10666667,
            "longitude": -94.67638889,
        },
        {
            "neighborhood": "Crossroads Arts District",
            "latitude": 39.09166667,
            "longitude": -94.58194444,
        },
        {
            "neighborhood": "Westport",
            "latitude": 39.05333333,
            "longitude": -94.59194444,
        },
        {
            "neighborhood": "Brookside",
            "latitude": 39.09972222,
            "longitude": -94.57833333,
        },
    ],
    "Colorado Springs,CO": [
        {
            "neighborhood": "Downtown Colorado Springs",
            "latitude": 37.265,
            "longitude": -107.00833333,
        },
        {
            "neighborhood": "Old Colorado City",
            "latitude": 38.83388889,
            "longitude": -104.82527778,
        },
        {
            "neighborhood": "Manitou Springs",
            "latitude": 38.8575,
            "longitude": -104.91277778,
        },
        {
            "neighborhood": "Briargate",
            "latitude": 38.83388889,
            "longitude": -104.82527778,
        },
        {
            "neighborhood": "Peregrine",
            "latitude": 38.83388889,
            "longitude": -104.82527778,
        },
    ],
    "Omaha,NE": [
        {
            "neighborhood": "Downtown Omaha",
            "latitude": 41.2583039,
            "longitude": -95.9418751,
        },
        {
            "neighborhood": "Old Market",
            "latitude": 41.25555556,
            "longitude": -95.93055556,
        },
        {
            "neighborhood": "Midtown Crossing",
            "latitude": 41.25888889,
            "longitude": -95.95916667,
        },
        {"neighborhood": "Aksarben", "latitude": 41.25861111, "longitude": -95.9375},
        {
            "neighborhood": "Dundee-Happy Hollow",
            "latitude": 41.265034,
            "longitude": -95.99038,
        },
    ],
    "Raleigh,NC": [
        {
            "neighborhood": "Downtown Raleigh",
            "latitude": 35.85416667,
            "longitude": -78.76194444,
        },
        {
            "neighborhood": "Glenwood-Brooklyn",
            "latitude": 35.85416667,
            "longitude": -78.76194444,
        },
        {
            "neighborhood": "Boylan Heights",
            "latitude": 35.85416667,
            "longitude": -78.76194444,
        },
        {
            "neighborhood": "Mordecai",
            "latitude": 35.85416667,
            "longitude": -78.76194444,
        },
        {"neighborhood": "Cameron Village", "latitude": 35.88, "longitude": -78.79},
    ],
    "Miami,FL": [
        {"neighborhood": "Coconut Grove", "latitude": 25.71666667, "longitude": -80.25},
        {"neighborhood": "Wynwood", "latitude": 25.804, "longitude": -80.199},
        {
            "neighborhood": "Design District",
            "latitude": 25.81666667,
            "longitude": -80.2,
        },
        {
            "neighborhood": "Little Havana",
            "latitude": 25.77257778,
            "longitude": -80.21458889,
        },
    ],
    "Virginia Beach,VA": [
        {"neighborhood": "Oceanfront", "latitude": 36.85, "longitude": -75.97777778},
        {"neighborhood": "Shore Drive", "latitude": 36.85, "longitude": -75.97777778},
        {"neighborhood": "Lynnhaven", "latitude": 36.85, "longitude": -75.97777778},
        {"neighborhood": "Pembroke", "latitude": 36.85, "longitude": -75.97777778},
    ],
    "Long Beach,CA": [
        {
            "neighborhood": "Downtown Long Beach",
            "latitude": 33.81777778,
            "longitude": -118.15166667,
        },
        {
            "neighborhood": "Belmont Shore",
            "latitude": 33.75722222,
            "longitude": -118.13694444,
        },
        {"neighborhood": "Naples", "latitude": 33.76833333, "longitude": -118.19555556},
        {
            "neighborhood": "Peninsula",
            "latitude": 33.76833333,
            "longitude": -118.19555556,
        },
        {"neighborhood": "Bixby Knolls", "latitude": 33.8356, "longitude": -118.1767},
    ],
    "Oakland,CA": [
        {
            "neighborhood": "Downtown Oakland",
            "latitude": 37.81194444,
            "longitude": -122.295,
        },
        {
            "neighborhood": "Jack London Square",
            "latitude": 37.79361111,
            "longitude": -122.27138889,
        },
        {
            "neighborhood": "Rockridge",
            "latitude": 37.80444444,
            "longitude": -122.27083333,
        },
        {"neighborhood": "Temescal", "latitude": 37.837222, "longitude": -122.262222},
        {
            "neighborhood": "Adams Point",
            "latitude": 37.8125,
            "longitude": -122.25527778,
        },
    ],
    "Minneapolis,MN": [
        {"neighborhood": "Downtown Minneapolis", "latitude": 44.95, "longitude": -93.2},
        {"neighborhood": "Uptown", "latitude": 44.94888889, "longitude": -93.29861111},
        {
            "neighborhood": "Dinkytown",
            "latitude": 44.98083333,
            "longitude": -93.23611111,
        },
        {
            "neighborhood": "Nordeast",
            "latitude": 44.98722222,
            "longitude": -93.25444444,
        },
        {
            "neighborhood": "Lyn-Lake",
            "latitude": 44.98194444,
            "longitude": -93.26916667,
        },
    ],
    "Bakersfield,CA": [
        {
            "neighborhood": "Downtown Bakersfield",
            "latitude": 35.37333333,
            "longitude": -119.01888889,
        },
        {
            "neighborhood": "Stockdale",
            "latitude": 35.37333333,
            "longitude": -119.01888889,
        },
        {
            "neighborhood": "Seven Oaks",
            "latitude": 35.37333333,
            "longitude": -119.01888889,
        },
        {
            "neighborhood": "Oleander",
            "latitude": 38.58166667,
            "longitude": -121.49444444,
        },
    ],
    "Tulsa,OK": [
        {
            "neighborhood": "Downtown Tulsa",
            "latitude": 36.13138889,
            "longitude": -95.93722222,
        },
        {
            "neighborhood": "Brookside",
            "latitude": 36.13138889,
            "longitude": -95.93722222,
        },
        {
            "neighborhood": "Utica Square",
            "latitude": 36.13138889,
            "longitude": -95.93722222,
        },
        {
            "neighborhood": "Pearl District",
            "latitude": 36.13138889,
            "longitude": -95.93722222,
        },
    ],
    "Tampa,FL": [
        {
            "neighborhood": "Downtown Tampa",
            "latitude": 27.94972222,
            "longitude": -82.45638889,
        },
        {"neighborhood": "Ybor City", "latitude": 27.96138889, "longitude": -82.445},
        {
            "neighborhood": "Hyde Park",
            "latitude": 27.93694444,
            "longitude": -82.47555556,
        },
        {
            "neighborhood": "South Tampa",
            "latitude": 27.94972222,
            "longitude": -82.45638889,
        },
        {"neighborhood": "Westshore", "latitude": 27.9475, "longitude": -82.45861111},
    ],
    "Arlington,TX": [
        {
            "neighborhood": "Downtown Arlington",
            "latitude": 32.705,
            "longitude": -97.12277778,
        },
        {"neighborhood": "Uptown", "latitude": 32.77916667, "longitude": -96.80888889},
        {
            "neighborhood": "Dalworthington Gardens",
            "latitude": 32.69361111,
            "longitude": -97.15666667,
        },
    ],
    "Wichita,KS": [
        {"neighborhood": "Delano", "latitude": 37.68277778, "longitude": -97.35972222},
        {
            "neighborhood": "Old Town",
            "latitude": 37.68888889,
            "longitude": -97.33611111,
        },
        {
            "neighborhood": "Riverside",
            "latitude": 37.69861111,
            "longitude": -97.35972222,
        },
        {
            "neighborhood": "College Hill",
            "latitude": 37.68694444,
            "longitude": -97.28944444,
        },
        {
            "neighborhood": "Downtown Wichita",
            "latitude": 37.68888889,
            "longitude": -97.33611111,
        },
    ],
    "Aurora,CO": [
        {"neighborhood": "Aurora Hills", "latitude": 39.7294, "longitude": -104.8319},
        {
            "neighborhood": "Cherry Creek",
            "latitude": 39.75455556,
            "longitude": -105.00822222,
        },
        {
            "neighborhood": "Downtown Aurora",
            "latitude": 39.7294,
            "longitude": -104.8319,
        },
        {
            "neighborhood": "Hoffman Heights",
            "latitude": 39.7294,
            "longitude": -104.8319,
        },
        {
            "neighborhood": "Stanley Marketplace",
            "latitude": 39.7294,
            "longitude": -104.8319,
        },
    ],
    "New Orleans,LA": [
        {
            "neighborhood": "French Quarter",
            "latitude": 29.95861111,
            "longitude": -90.065,
        },
        {
            "neighborhood": "Garden District",
            "latitude": 29.92777778,
            "longitude": -90.08472222,
        },
        {"neighborhood": "Marigny", "latitude": 29.96472222, "longitude": -90.05527778},
        {"neighborhood": "Bywater", "latitude": 29.97611111, "longitude": -90.07833333},
    ],
    "Cleveland,OH": [
        {
            "neighborhood": "Downtown Cleveland",
            "latitude": 41.49888889,
            "longitude": -81.68972222,
        },
        {"neighborhood": "Tremont", "latitude": 41.49916667, "longitude": -81.69472222},
        {
            "neighborhood": "Ohio City",
            "latitude": 41.49916667,
            "longitude": -81.69472222,
        },
        {
            "neighborhood": "Gordon Square",
            "latitude": 41.49916667,
            "longitude": -81.69472222,
        },
        {
            "neighborhood": "Shaker Square",
            "latitude": 41.48388889,
            "longitude": -81.59055556,
        },
    ],
    "Honolulu,HI": [
        {"neighborhood": "Waikiki", "latitude": 21.2752, "longitude": -157.8312},
        {
            "neighborhood": "Downtown Honolulu",
            "latitude": 21.46666667,
            "longitude": -157.96666667,
        },
        {
            "neighborhood": "Chinatown",
            "latitude": 21.30694444,
            "longitude": -157.85833333,
        },
        {
            "neighborhood": "Kaka'ako",
            "latitude": 21.30694444,
            "longitude": -157.85833333,
        },
        {"neighborhood": "Ala Moana", "latitude": 21.28873, "longitude": -157.84826},
    ],
    "Anaheim,CA": [
        {
            "neighborhood": "Downtown Anaheim",
            "latitude": 33.83611111,
            "longitude": -117.88972222,
        },
        {
            "neighborhood": "The Colony",
            "latitude": 33.83611111,
            "longitude": -117.88972222,
        },
        {
            "neighborhood": "Anaheim Hills",
            "latitude": 33.84444444,
            "longitude": -117.77722222,
        },
        {
            "neighborhood": "The Anaheim Resort",
            "latitude": 33.83611111,
            "longitude": -117.88972222,
        },
    ],
    "Henderson,NV": [
        {
            "neighborhood": "Water Street District",
            "latitude": 36.03333333,
            "longitude": -114.98333333,
        },
        {"neighborhood": "Lake Las Vegas", "latitude": 36.102, "longitude": -114.9295},
        {
            "neighborhood": "MacDonald Highlands",
            "latitude": 36.03333333,
            "longitude": -114.98333333,
        },
    ],
    "Orlando,FL": [
        {
            "neighborhood": "Downtown Orlando",
            "latitude": 28.53361111,
            "longitude": -81.37583333,
        },
        {"neighborhood": "Winter Park", "latitude": 28.54, "longitude": -81.38},
        {
            "neighborhood": "Lake Eola Heights",
            "latitude": 28.53361111,
            "longitude": -81.37583333,
        },
        {
            "neighborhood": "Thornton Park",
            "latitude": 28.53361111,
            "longitude": -81.37583333,
        },
        {
            "neighborhood": "College Park",
            "latitude": 28.5686012,
            "longitude": -81.3894297,
        },
    ],
    "Lexington,KY": [
        {
            "neighborhood": "Downtown Lexington",
            "latitude": 38.04638889,
            "longitude": -84.49694444,
        },
        {
            "neighborhood": "Ashland Park",
            "latitude": 38.02916667,
            "longitude": -84.48222222,
        },
        {
            "neighborhood": "Gratz Park",
            "latitude": 38.04638889,
            "longitude": -84.49694444,
        },
        {
            "neighborhood": "Historic South Hill",
            "latitude": 38.04638889,
            "longitude": -84.49694444,
        },
    ],
    "Stockton,CA": [
        {
            "neighborhood": "Downtown Stockton",
            "latitude": 37.97555556,
            "longitude": -121.30083333,
        },
        {
            "neighborhood": "Miracle Mile",
            "latitude": 37.97555556,
            "longitude": -121.30083333,
        },
        {
            "neighborhood": "Pacific",
            "latitude": 37.97555556,
            "longitude": -121.30083333,
        },
        {
            "neighborhood": "Weberstown",
            "latitude": 37.97555556,
            "longitude": -121.30083333,
        },
        {
            "neighborhood": "Civic Center",
            "latitude": 37.97555556,
            "longitude": -121.30083333,
        },
    ],
    "Riverside,CA": [
        {
            "neighborhood": "Arlington",
            "latitude": 33.94805556,
            "longitude": -117.39611111,
        },
        {
            "neighborhood": "Casa Blanca",
            "latitude": 33.94805556,
            "longitude": -117.39611111,
        },
        {
            "neighborhood": "Downtown Riverside",
            "latitude": 33.94805556,
            "longitude": -117.39611111,
        },
        {
            "neighborhood": "Eastside",
            "latitude": 33.94805556,
            "longitude": -117.39611111,
        },
        {"neighborhood": "Hawthorne", "latitude": 34.0, "longitude": -118.2},
    ],
    "Corpus Christi,TX": [
        {
            "neighborhood": "Bay Area",
            "latitude": 27.77222222,
            "longitude": -97.25277778,
        },
        {
            "neighborhood": "Calallen",
            "latitude": 27.85730556,
            "longitude": -97.63577778,
        },
        {
            "neighborhood": "Downtown Corpus Christi",
            "latitude": 27.7121,
            "longitude": -97.3254,
        },
        {
            "neighborhood": "Flour Bluff",
            "latitude": 27.74277778,
            "longitude": -97.40194444,
        },
        {
            "neighborhood": "North Beach",
            "latitude": 27.74277778,
            "longitude": -97.40194444,
        },
    ],
    "Irvine,CA": [
        {
            "neighborhood": "Business District",
            "latitude": 33.66944444,
            "longitude": -117.82305556,
        },
        {
            "neighborhood": "El Camino Real",
            "latitude": 33.66944444,
            "longitude": -117.82305556,
        },
        {
            "neighborhood": "Irvine Spectrum",
            "latitude": 33.66944444,
            "longitude": -117.82305556,
        },
        {
            "neighborhood": "Northwood",
            "latitude": 33.66944444,
            "longitude": -117.82305556,
        },
        {
            "neighborhood": "Quail Hill",
            "latitude": 33.84444444,
            "longitude": -117.77722222,
        },
    ],
    "Cincinnati,OH": [
        {"neighborhood": "Clifton", "latitude": 39.2, "longitude": -84.54},
        {"neighborhood": "Downtown Cincinnati", "latitude": 39.0, "longitude": -84.5},
        {"neighborhood": "Hyde Park", "latitude": 39.13972222, "longitude": -84.4425},
        {
            "neighborhood": "Mount Adams",
            "latitude": 39.10658333,
            "longitude": -84.49961111,
        },
        {
            "neighborhood": "Over-the-Rhine",
            "latitude": 39.11305556,
            "longitude": -84.51611111,
        },
    ],
    "Santa Ana,CA": [
        {
            "neighborhood": "Downtown Santa Ana",
            "latitude": 33.62805556,
            "longitude": -117.95861111,
        },
        {"neighborhood": "French Park", "latitude": 34.42, "longitude": -118.52},
    ],
    "Newark,NJ": [
        {"neighborhood": "Broadway", "latitude": 40.775, "longitude": -74.15833333},
        {
            "neighborhood": "Downtown Newark",
            "latitude": 40.6925,
            "longitude": -74.16861111,
        },
        {"neighborhood": "Ironbound", "latitude": 40.725, "longitude": -74.16111111},
        {
            "neighborhood": "North Broadway",
            "latitude": 40.775,
            "longitude": -74.15833333,
        },
        {
            "neighborhood": "University Heights",
            "latitude": 40.74111111,
            "longitude": -74.18305556,
        },
    ],
    "Saint Paul,MN": [
        {
            "neighborhood": "Downtown Saint Paul",
            "latitude": 44.94777778,
            "longitude": -93.10388889,
        },
        {
            "neighborhood": "Frogtown",
            "latitude": 44.96277778,
            "longitude": -93.12611111,
        },
        {"neighborhood": "Hamline-Midway", "latitude": 44.9658, "longitude": -93.1654},
        {"neighborhood": "Summit Hill", "latitude": 44.95, "longitude": -93.2},
    ],
    "Pittsburgh,PA": [
        {
            "neighborhood": "Downtown Pittsburgh",
            "latitude": 40.44111111,
            "longitude": -80.0,
        },
        {"neighborhood": "Oakland", "latitude": 40.441, "longitude": -79.957},
        {
            "neighborhood": "Shadyside",
            "latitude": 40.43972222,
            "longitude": -79.97638889,
        },
        {
            "neighborhood": "Strip District",
            "latitude": 40.43972222,
            "longitude": -79.97638889,
        },
    ],
    "Greensboro,NC": [
        {"neighborhood": "College Hill", "latitude": 35.9557, "longitude": -80.0053},
        {
            "neighborhood": "Downtown Greensboro",
            "latitude": 36.095,
            "longitude": -79.82583333,
        },
        {
            "neighborhood": "Fisher Park",
            "latitude": 36.07555556,
            "longitude": -79.79277778,
        },
        {
            "neighborhood": "Irving Park",
            "latitude": 36.09638889,
            "longitude": -79.79833333,
        },
    ],
    "Durham,NC": [
        {
            "neighborhood": "Downtown Durham",
            "latitude": 35.97861111,
            "longitude": -78.9,
        },
        {
            "neighborhood": "Hope Valley",
            "latitude": 35.94888889,
            "longitude": -78.94777778,
        },
        {"neighborhood": "Old North Durham", "latitude": 35.88, "longitude": -78.79},
        {"neighborhood": "Trinity Park", "latitude": 35.97861111, "longitude": -78.9},
    ],
    "Lincoln,NE": [
        {
            "neighborhood": "Haymarket",
            "latitude": 40.80916667,
            "longitude": -96.67805556,
        },
        {
            "neighborhood": "Downtown Lincoln",
            "latitude": 40.80916667,
            "longitude": -96.67805556,
        },
        {
            "neighborhood": "University Place",
            "latitude": 40.80916667,
            "longitude": -96.67805556,
        },
        {
            "neighborhood": "Havelock",
            "latitude": 40.80916667,
            "longitude": -96.67805556,
        },
        {"neighborhood": "Bethany", "latitude": 40.80916667, "longitude": -96.67805556},
    ],
    "Jersey City,NJ": [
        {
            "neighborhood": "Downtown Jersey City",
            "latitude": 40.71,
            "longitude": -74.06,
        },
        {
            "neighborhood": "Journal Square",
            "latitude": 40.732153,
            "longitude": -74.062078,
        },
        {"neighborhood": "Newport", "latitude": 40.729698, "longitude": -74.03635},
        {
            "neighborhood": "Greenville",
            "latitude": 40.70027778,
            "longitude": -74.09444444,
        },
        {
            "neighborhood": "Liberty State Park",
            "latitude": 40.70416667,
            "longitude": -74.04916667,
        },
    ],
    "Plano,TX": [
        {"neighborhood": "Collin County", "latitude": 33.18, "longitude": -96.58},
        {
            "neighborhood": "Preston Hollow",
            "latitude": 32.77916667,
            "longitude": -96.80888889,
        },
        {
            "neighborhood": "Russell Creek",
            "latitude": 33.05027778,
            "longitude": -96.69888889,
        },
    ],
    "Anchorage,AK": [
        {
            "neighborhood": "Downtown Anchorage",
            "latitude": 61.21666667,
            "longitude": -149.89361111,
        },
        {
            "neighborhood": "Spenard",
            "latitude": 61.21666667,
            "longitude": -149.89361111,
        },
        {"neighborhood": "Fairview", "latitude": 61.162, "longitude": -149.2792},
        {
            "neighborhood": "Government Hill",
            "latitude": 61.21666667,
            "longitude": -149.89361111,
        },
        {
            "neighborhood": "Bootleggers Cove",
            "latitude": 61.21666667,
            "longitude": -149.89361111,
        },
    ],
    "North Las Vegas,NV": [
        {
            "neighborhood": "Aliante",
            "latitude": 36.22861111,
            "longitude": -115.14666667,
        },
        {
            "neighborhood": "El Dorado",
            "latitude": 40.51828889,
            "longitude": -118.22220556,
        },
        {
            "neighborhood": "Valley Vista",
            "latitude": 36.1125,
            "longitude": -115.25027778,
        },
    ],
    "St. Louis,MO": [
        {
            "neighborhood": "Downtown St. Louis",
            "latitude": 38.626,
            "longitude": -90.1922,
        },
        {"neighborhood": "Soulard", "latitude": 38.6053, "longitude": -90.2086},
        {
            "neighborhood": "Lafayette Square",
            "latitude": 38.6162,
            "longitude": -90.2157,
        },
        {
            "neighborhood": "Cherokee Street",
            "latitude": 38.62722222,
            "longitude": -90.19777778,
        },
        {"neighborhood": "The Hill", "latitude": 38.617, "longitude": -90.278},
    ],
    "Madison,WI": [
        {
            "neighborhood": "Downtown Madison",
            "latitude": 43.07472222,
            "longitude": -89.38416667,
        },
        {
            "neighborhood": "State Street",
            "latitude": 43.07472222,
            "longitude": -89.38416667,
        },
        {"neighborhood": "Atwood", "latitude": 43.07472222, "longitude": -89.38416667},
        {
            "neighborhood": "Maple Bluff",
            "latitude": 43.11083333,
            "longitude": -89.36833333,
        },
        {
            "neighborhood": "University Heights",
            "latitude": 43.07527778,
            "longitude": -89.40416667,
        },
    ],
    "Chandler,AZ": [
        {
            "neighborhood": "Downtown Chandler",
            "latitude": 33.3,
            "longitude": -111.83333333,
        },
        {"neighborhood": "Ocotillo", "latitude": 33.3, "longitude": -111.83333333},
        {"neighborhood": "Sun Lakes", "latitude": 33.21472222, "longitude": -111.87},
        {
            "neighborhood": "Dobson Ranch",
            "latitude": 33.42222222,
            "longitude": -111.82277778,
        },
    ],
    "Gilbert,AZ": [
        {
            "neighborhood": "Downtown Gilbert",
            "latitude": 33.35277778,
            "longitude": -111.78888889,
        },
        {
            "neighborhood": "Heritage District",
            "latitude": 33.35277778,
            "longitude": -111.78888889,
        },
    ],
    "Reno,NV": [
        {
            "neighborhood": "Downtown Reno",
            "latitude": 39.52722222,
            "longitude": -119.82194444,
        },
        {
            "neighborhood": "Riverside",
            "latitude": 39.52722222,
            "longitude": -119.82194444,
        },
        {
            "neighborhood": "Old Southwest",
            "latitude": 39.52722222,
            "longitude": -119.82194444,
        },
    ],
    "Buffalo,NY": [
        {
            "neighborhood": "Allentown",
            "latitude": 42.88638889,
            "longitude": -78.87805556,
        },
        {
            "neighborhood": "Canalside",
            "latitude": 42.88638889,
            "longitude": -78.87805556,
        },
        {
            "neighborhood": "Downtown Buffalo",
            "latitude": 42.88638889,
            "longitude": -78.87805556,
        },
        {
            "neighborhood": "Elmwood Village",
            "latitude": 42.900391,
            "longitude": -78.877415,
        },
        {"neighborhood": "North Buffalo", "latitude": 42.9, "longitude": -78.85},
    ],
    "Chula Vista,CA": [
        {"neighborhood": "Bonita", "latitude": 32.62777778, "longitude": -117.04805556},
        {
            "neighborhood": "Eastlake",
            "latitude": 32.62777778,
            "longitude": -117.04805556,
        },
        {
            "neighborhood": "Otay Ranch",
            "latitude": 32.62777778,
            "longitude": -117.04805556,
        },
        {
            "neighborhood": "Rancho del Rey",
            "latitude": 32.62777778,
            "longitude": -117.04805556,
        },
    ],
    "Fort Wayne,IN": [
        {
            "neighborhood": "Downtown Fort Wayne",
            "latitude": 41.08888889,
            "longitude": -85.16138889,
        },
        {
            "neighborhood": "Fort Wayne Historic District",
            "latitude": 41.08888889,
            "longitude": -85.16138889,
        },
        {
            "neighborhood": "Southwest Fort Wayne",
            "latitude": 41.08888889,
            "longitude": -85.16138889,
        },
        {
            "neighborhood": "West Central",
            "latitude": 41.08888889,
            "longitude": -85.16138889,
        },
    ],
    "Lubbock,TX": [
        {"neighborhood": "Downtown Lubbock", "latitude": 33.585, "longitude": -101.845},
        {"neighborhood": "Maxey Park", "latitude": 31.0, "longitude": -99.0},
        {"neighborhood": "Overton", "latitude": 33.585, "longitude": -101.845},
    ],
    "Toledo,OH": [
        {
            "neighborhood": "Downtown Toledo",
            "latitude": 41.65277778,
            "longitude": -83.53777778,
        },
        {
            "neighborhood": "Old West End",
            "latitude": 41.65277778,
            "longitude": -83.53777778,
        },
        {
            "neighborhood": "Ottawa Hills",
            "latitude": 41.65277778,
            "longitude": -83.53777778,
        },
        {
            "neighborhood": "Reynolds Corners",
            "latitude": 41.65277778,
            "longitude": -83.53777778,
        },
        {
            "neighborhood": "Sylvania",
            "latitude": 41.65277778,
            "longitude": -83.53777778,
        },
    ],
    "St. Petersburg,FL": [
        {
            "neighborhood": "Downtown St. Petersburg",
            "latitude": 27.77333333,
            "longitude": -82.62194444,
        },
        {"neighborhood": "Old Northeast", "latitude": 27.77305556, "longitude": -82.64},
        {"neighborhood": "Snell Isle", "latitude": 27.79621, "longitude": -82.62024},
        {
            "neighborhood": "Tierra Verde",
            "latitude": 27.68138889,
            "longitude": -82.72444444,
        },
    ],
    "Laredo,TX": [
        {
            "neighborhood": "Downtown Laredo",
            "latitude": 27.52361111,
            "longitude": -99.49027778,
        },
        {"neighborhood": "Del Mar", "latitude": 27.52361111, "longitude": -99.49027778},
        {"neighborhood": "Hillside", "latitude": 27.77, "longitude": -99.33},
        {"neighborhood": "Winfield", "latitude": 27.0, "longitude": -99.18},
    ],
    "Irving,TX": [
        {
            "neighborhood": "Downtown Irving",
            "latitude": 32.81666667,
            "longitude": -96.95,
        },
        {
            "neighborhood": "Heritage District",
            "latitude": 32.81666667,
            "longitude": -96.95,
        },
        {
            "neighborhood": "Las Colinas",
            "latitude": 32.89172222,
            "longitude": -96.94830556,
        },
        {"neighborhood": "North Irving", "latitude": 32.81666667, "longitude": -96.95},
        {
            "neighborhood": "Valley Ranch",
            "latitude": 32.928324,
            "longitude": -96.951721,
        },
    ],
    "Chesapeake,VA": [
        {"neighborhood": "Deep Creek", "latitude": 36.75409, "longitude": -76.35234},
        {"neighborhood": "Greenbrier", "latitude": 37.7854, "longitude": -80.3083},
        {
            "neighborhood": "Great Bridge",
            "latitude": 38.99166667,
            "longitude": -76.37222222,
        },
        {"neighborhood": "Indian River", "latitude": 37.8, "longitude": -76.1},
        {
            "neighborhood": "South Norfolk",
            "latitude": 36.767398,
            "longitude": -76.287405,
        },
    ],
    "Glendale,AZ": [
        {
            "neighborhood": "Downtown Glendale",
            "latitude": 33.53861111,
            "longitude": -112.18638889,
        },
        {
            "neighborhood": "Glendale Avenue",
            "latitude": 33.53861111,
            "longitude": -112.18638889,
        },
        {
            "neighborhood": "Maricopa Manor",
            "latitude": 33.42777778,
            "longitude": -112.11888889,
        },
        {
            "neighborhood": "Sahuaro Ranch",
            "latitude": 33.53861111,
            "longitude": -112.18638889,
        },
        {
            "neighborhood": "Thunderbird",
            "latitude": 33.53861111,
            "longitude": -112.18638889,
        },
    ],
    "Winston-Salem,NC": [
        {
            "neighborhood": "Buena Vista",
            "latitude": 36.10277778,
            "longitude": -80.26083333,
        },
        {
            "neighborhood": "Kernersville",
            "latitude": 36.10611111,
            "longitude": -80.08416667,
        },
        {"neighborhood": "Old Salem", "latitude": 36.0872, "longitude": -80.2422},
    ],
    "Port St. Lucie,FL": [
        {
            "neighborhood": "Bayshore Heights",
            "latitude": 27.27583333,
            "longitude": -80.355,
        },
        {
            "neighborhood": "Downtown Port St. Lucie",
            "latitude": 27.27583333,
            "longitude": -80.355,
        },
        {"neighborhood": "Tradition", "latitude": 27.27583333, "longitude": -80.355},
    ],
    "Scottsdale,AZ": [
        {
            "neighborhood": "Downtown Scottsdale",
            "latitude": 33.49305556,
            "longitude": -111.92611111,
        },
        {
            "neighborhood": "McDowell Mountain Ranch",
            "latitude": 33.49305556,
            "longitude": -111.92611111,
        },
        {
            "neighborhood": "Old Town Scottsdale",
            "latitude": 33.49305556,
            "longitude": -111.92611111,
        },
    ],
    "Garland,TX": [
        {
            "neighborhood": "Downtown Garland",
            "latitude": 32.90722222,
            "longitude": -96.63527778,
        },
        {
            "neighborhood": "Firewheel",
            "latitude": 32.90722222,
            "longitude": -96.63527778,
        },
        {
            "neighborhood": "Lakeview",
            "latitude": 32.90722222,
            "longitude": -96.63527778,
        },
        {
            "neighborhood": "Oakridge",
            "latitude": 32.90722222,
            "longitude": -96.63527778,
        },
    ],
    "Boise,ID": [
        {
            "neighborhood": "Boise Heights",
            "latitude": 43.61583333,
            "longitude": -116.20166667,
        },
        {
            "neighborhood": "Downtown Boise",
            "latitude": 43.61583333,
            "longitude": -116.20166667,
        },
        {
            "neighborhood": "East End",
            "latitude": 43.61583333,
            "longitude": -116.20166667,
        },
        {
            "neighborhood": "North End",
            "latitude": 43.61583333,
            "longitude": -116.20166667,
        },
    ],
    "Norfolk,VA": [
        {
            "neighborhood": "Downtown Norfolk",
            "latitude": 36.84694444,
            "longitude": -76.28527778,
        },
        {"neighborhood": "Ghent", "latitude": 36.86266667, "longitude": -76.30080556},
        {
            "neighborhood": "Larchmont",
            "latitude": 36.84694444,
            "longitude": -76.28527778,
        },
        {"neighborhood": "Ocean View", "latitude": 36.95, "longitude": -76.24638889},
        {
            "neighborhood": "Waterside",
            "latitude": 36.84444444,
            "longitude": -76.29138889,
        },
    ],
    "Spokane,WA": [
        {
            "neighborhood": "Browne's Addition",
            "latitude": 47.65888889,
            "longitude": -117.425,
        },
        {"neighborhood": "Downtown Spokane", "latitude": 47.657, "longitude": -117.42},
        {"neighborhood": "Garfield", "latitude": 47.65888889, "longitude": -117.425},
        {"neighborhood": "Riverside", "latitude": 47.65888889, "longitude": -117.425},
        {"neighborhood": "South Perry", "latitude": 47.65888889, "longitude": -117.425},
    ],
    "Richmond,VA": [
        {
            "neighborhood": "Church Hill",
            "latitude": 37.54083333,
            "longitude": -77.43666667,
        },
        {
            "neighborhood": "Downtown Richmond",
            "latitude": 37.54083333,
            "longitude": -77.43666667,
        },
        {"neighborhood": "The Fan", "latitude": 37.5525, "longitude": -77.46555556},
    ],
    "Fremont,CA": [
        {
            "neighborhood": "Ardenwood",
            "latitude": 37.55805556,
            "longitude": -122.04944444,
        }
    ],
    "Huntsville,AL": [
        {
            "neighborhood": "Downtown Huntsville",
            "latitude": 34.69333333,
            "longitude": -86.56083333,
        },
        {
            "neighborhood": "Medical District",
            "latitude": 34.69333333,
            "longitude": -86.56083333,
        },
        {
            "neighborhood": "Twickenham",
            "latitude": 34.69333333,
            "longitude": -86.56083333,
        },
    ],
    "Frisco,TX": [
        {"neighborhood": "Legacy West", "latitude": 33.1239, "longitude": -96.7956},
        {
            "neighborhood": "The Colony",
            "latitude": 33.09083333,
            "longitude": -96.88472222,
        },
        {
            "neighborhood": "Little Elm",
            "latitude": 33.16388889,
            "longitude": -96.93027778,
        },
        {"neighborhood": "Prosper", "latitude": 33.14166667, "longitude": -96.82166667},
    ],
    "Cape Coral,FL": [
        {
            "neighborhood": "Downtown Cape Coral",
            "latitude": 26.63972222,
            "longitude": -81.9825,
        },
        {"neighborhood": "Cape Harbour", "latitude": 25.1, "longitude": -76.13333333},
        {
            "neighborhood": "Pine Island Road",
            "latitude": 26.63972222,
            "longitude": -81.9825,
        },
        {
            "neighborhood": "Del Prado Boulevard",
            "latitude": 26.63972222,
            "longitude": -81.9825,
        },
    ],
    "Santa Clarita,CA": [
        {"neighborhood": "Downtown Newhall", "latitude": 34.38, "longitude": -118.53},
        {"neighborhood": "Valencia", "latitude": 34.42, "longitude": -118.56},
        {"neighborhood": "Canyon Country", "latitude": 34.42, "longitude": -118.45},
        {"neighborhood": "Saugus", "latitude": 34.44, "longitude": -118.52},
        {"neighborhood": "Stevenson Ranch", "latitude": 34.42, "longitude": -118.52},
    ],
    "San Bernardino,CA": [
        {
            "neighborhood": "Downtown San Bernardino",
            "latitude": 34.21638889,
            "longitude": -117.40138889,
        },
        {"neighborhood": "University District", "latitude": 34.1, "longitude": -117.3},
        {
            "neighborhood": "Del Rosa",
            "latitude": 34.14666667,
            "longitude": -117.24361111,
        },
    ],
    "Tacoma,WA": [
        {
            "neighborhood": "Downtown Tacoma",
            "latitude": 47.24583333,
            "longitude": -122.45944444,
        },
        {
            "neighborhood": "Stadium District",
            "latitude": 47.24583333,
            "longitude": -122.45944444,
        },
        {
            "neighborhood": "North End",
            "latitude": 47.24583333,
            "longitude": -122.45944444,
        },
        {"neighborhood": "Hilltop", "latitude": 47.245, "longitude": -122.45305556},
        {
            "neighborhood": "Tacoma Dome",
            "latitude": 47.23666667,
            "longitude": -122.42666667,
        },
    ],
    "Hialeah,FL": [
        {
            "neighborhood": "Downtown Hialeah",
            "latitude": 25.86055556,
            "longitude": -80.29388889,
        },
        {
            "neighborhood": "Hialeah Gardens",
            "latitude": 25.86055556,
            "longitude": -80.29388889,
        },
        {
            "neighborhood": "Miami Lakes",
            "latitude": 25.86055556,
            "longitude": -80.29388889,
        },
        {
            "neighborhood": "Opa-locka",
            "latitude": 25.90166667,
            "longitude": -80.25083333,
        },
        {
            "neighborhood": "Westland Mall",
            "latitude": 25.86805556,
            "longitude": -80.31805556,
        },
    ],
    "Baton Rouge,LA": [
        {
            "neighborhood": "Garden District",
            "latitude": 30.4475,
            "longitude": -91.17861111,
        },
        {"neighborhood": "Mid City", "latitude": 30.4475, "longitude": -91.17861111},
        {
            "neighborhood": "Old South Baton Rouge",
            "latitude": 30.54,
            "longitude": -91.09,
        },
        {
            "neighborhood": "University Hills",
            "latitude": 30.4475,
            "longitude": -91.17861111,
        },
    ],
    "Modesto,CA": [
        {
            "neighborhood": "Downtown Modesto",
            "latitude": 37.66138889,
            "longitude": -120.99444444,
        },
        {
            "neighborhood": "Vintage Faire Mall",
            "latitude": 38.581152,
            "longitude": -121.501644,
        },
    ],
    "Fontana,CA": [
        {
            "neighborhood": "Downtown Fontana",
            "latitude": 34.1,
            "longitude": -117.46666667,
        },
        {"neighborhood": "Sierra Lakes", "latitude": 34.1, "longitude": -117.46666667},
        {"neighborhood": "North Fontana", "latitude": 34.1, "longitude": -117.46666667},
        {"neighborhood": "South Fontana", "latitude": 34.1, "longitude": -117.46666667},
        {
            "neighborhood": "Fontana Gateway",
            "latitude": 34.1421,
            "longitude": -117.4743,
        },
    ],
    "McKinney,TX": [
        {
            "neighborhood": "Downtown McKinney",
            "latitude": 33.19722222,
            "longitude": -96.63972222,
        },
        {
            "neighborhood": "Adriatica",
            "latitude": 33.19722222,
            "longitude": -96.63972222,
        },
        {
            "neighborhood": "Craig Ranch",
            "latitude": 33.19722222,
            "longitude": -96.63972222,
        },
    ],
    "Moreno Valley,CA": [
        {
            "neighborhood": "Edgemont",
            "latitude": 33.94305556,
            "longitude": -117.22833333,
        },
        {
            "neighborhood": "Meadowbrook",
            "latitude": 33.78222222,
            "longitude": -117.2275,
        },
        {"neighborhood": "Moreno", "latitude": 33.94305556, "longitude": -117.22833333},
        {
            "neighborhood": "Sunnymead",
            "latitude": 33.94305556,
            "longitude": -117.22833333,
        },
    ],
    "Des Moines,IA": [
        {
            "neighborhood": "Downtown Des Moines",
            "latitude": 41.58,
            "longitude": -93.6125,
        },
        {
            "neighborhood": "Sherman Hill",
            "latitude": 41.58861111,
            "longitude": -93.63833333,
        },
        {
            "neighborhood": "West Glen",
            "latitude": 41.50944444,
            "longitude": -93.78055556,
        },
    ],
    "Fayetteville,NC": [
        {
            "neighborhood": "Downtown Fayetteville",
            "latitude": 35.085,
            "longitude": -78.97722222,
        },
        {"neighborhood": "Terry Sanford", "latitude": 35.0647, "longitude": -78.9155},
        {"neighborhood": "Westover", "latitude": 35.085, "longitude": -78.97722222},
    ],
    "Salt Lake City,UT": [
        {"neighborhood": "The Avenues", "latitude": 40.775, "longitude": -111.875},
        {
            "neighborhood": "Central City",
            "latitude": 40.76083333,
            "longitude": -111.89111111,
        },
        {
            "neighborhood": "Downtown Salt Lake City",
            "latitude": 40.7608,
            "longitude": -111.891,
        },
        {
            "neighborhood": "Marmalade District",
            "latitude": 40.77777778,
            "longitude": -111.88888889,
        },
        {
            "neighborhood": "Sugar House",
            "latitude": 40.725384,
            "longitude": -111.859618,
        },
    ],
    "Yonkers,NY": [
        {
            "neighborhood": "Downtown Yonkers",
            "latitude": 40.94138889,
            "longitude": -73.86444444,
        },
        {"neighborhood": "Getty Square", "latitude": 40.93377, "longitude": -73.89795},
        {
            "neighborhood": "Ludlow Park",
            "latitude": 40.94138889,
            "longitude": -73.86444444,
        },
        {
            "neighborhood": "Park Hill",
            "latitude": 40.94138889,
            "longitude": -73.86444444,
        },
        {
            "neighborhood": "Ridge Hill",
            "latitude": 40.94138889,
            "longitude": -73.86444444,
        },
    ],
    "Worcester,MA": [
        {
            "neighborhood": "Downtown Worcester",
            "latitude": 42.27138889,
            "longitude": -71.79888889,
        },
        {
            "neighborhood": "Quinsigamond Village",
            "latitude": 42.27138889,
            "longitude": -71.79888889,
        },
        {
            "neighborhood": "Shrewsbury Street",
            "latitude": 42.27138889,
            "longitude": -71.79888889,
        },
        {
            "neighborhood": "Union Hill",
            "latitude": 42.27138889,
            "longitude": -71.79888889,
        },
    ],
    "Rochester,NY": [
        {
            "neighborhood": "Downtown Rochester",
            "latitude": 43.16555556,
            "longitude": -77.61611111,
        },
        {
            "neighborhood": "High Falls District",
            "latitude": 43.16555556,
            "longitude": -77.61611111,
        },
        {
            "neighborhood": "South Wedge",
            "latitude": 43.16555556,
            "longitude": -77.61611111,
        },
        {
            "neighborhood": "Upper Monroe",
            "latitude": 43.16555556,
            "longitude": -77.61611111,
        },
    ],
    "Sioux Falls,SD": [
        {
            "neighborhood": "Downtown Sioux Falls",
            "latitude": 43.53638889,
            "longitude": -96.73166667,
        },
        {
            "neighborhood": "Falls Park",
            "latitude": 43.53638889,
            "longitude": -96.73166667,
        },
        {
            "neighborhood": "Pettigrew Heights",
            "latitude": 44.07138889,
            "longitude": -103.22083333,
        },
        {
            "neighborhood": "Roosevelt Park",
            "latitude": 43.53638889,
            "longitude": -96.73166667,
        },
    ],
    "Little Rock,AR": [
        {
            "neighborhood": "Downtown Little Rock",
            "latitude": 34.74444444,
            "longitude": -92.28805556,
        },
        {
            "neighborhood": "Hillcrest",
            "latitude": 34.75805556,
            "longitude": -92.32444444,
        },
        {
            "neighborhood": "MacArthur Park",
            "latitude": 34.73833333,
            "longitude": -92.26522222,
        },
        {
            "neighborhood": "Quapaw Quarter",
            "latitude": 34.73437,
            "longitude": -92.27302,
        },
        {
            "neighborhood": "River Market District",
            "latitude": 34.78083333,
            "longitude": -92.25694444,
        },
    ],
    "Amarillo,TX": [
        {
            "neighborhood": "Downtown Amarillo",
            "latitude": 35.19916667,
            "longitude": -101.84527778,
        },
        {
            "neighborhood": "Hillside Terrace",
            "latitude": 32.842892,
            "longitude": -97.09639,
        },
        {
            "neighborhood": "North Heights",
            "latitude": 35.19916667,
            "longitude": -101.84527778,
        },
        {"neighborhood": "Pleasant Valley", "latitude": 35.4, "longitude": -101.89},
        {
            "neighborhood": "San Jacinto",
            "latitude": 35.19916667,
            "longitude": -101.84527778,
        },
    ],
    "Tallahassee,FL": [
        {"neighborhood": "Frenchtown", "latitude": 30.45, "longitude": -84.292},
        {
            "neighborhood": "Los Robles",
            "latitude": 30.43833333,
            "longitude": -84.28055556,
        },
        {
            "neighborhood": "College Town",
            "latitude": 30.43833333,
            "longitude": -84.28055556,
        },
        {
            "neighborhood": "Downtown Tallahassee",
            "latitude": 30.43833333,
            "longitude": -84.28055556,
        },
    ],
    "Grand Prairie,TX": [
        {
            "neighborhood": "Prairie Ridge",
            "latitude": 32.71527778,
            "longitude": -96.96611111,
        }
    ],
    "Columbus,GA": [
        {
            "neighborhood": "Downtown Columbus",
            "latitude": 32.49222222,
            "longitude": -84.94027778,
        },
        {
            "neighborhood": "Midtown Columbus",
            "latitude": 32.49222222,
            "longitude": -84.94027778,
        },
        {
            "neighborhood": "North Columbus",
            "latitude": 32.49222222,
            "longitude": -84.94027778,
        },
        {
            "neighborhood": "Baker Village",
            "latitude": 32.49222222,
            "longitude": -84.94027778,
        },
    ],
    "Augusta,GA": [
        {"neighborhood": "Downtown Augusta", "latitude": 33.47, "longitude": -81.975},
        {"neighborhood": "Summerville", "latitude": 33.47, "longitude": -81.975},
        {"neighborhood": "Harrisburg", "latitude": 33.47, "longitude": -81.975},
        {
            "neighborhood": "Olde Town",
            "latitude": 32.08111111,
            "longitude": -81.09111111,
        },
    ],
    "Peoria,AZ": [
        {
            "neighborhood": "Downtown Peoria",
            "latitude": 33.5825,
            "longitude": -112.23861111,
        },
        {"neighborhood": "Vistancia", "latitude": 33.5825, "longitude": -112.23861111},
        {
            "neighborhood": "Pioneer Park",
            "latitude": 33.63055556,
            "longitude": -112.36666667,
        },
    ],
    "Oxnard,CA": [
        {"neighborhood": "Colonia", "latitude": 34.19138889, "longitude": -119.1825},
        {"neighborhood": "Strickland", "latitude": 34.19138889, "longitude": -119.1825},
        {
            "neighborhood": "Wagon Wheel",
            "latitude": 34.23916667,
            "longitude": -119.18277778,
        },
    ],
    "Knoxville,TN": [
        {
            "neighborhood": "Downtown Knoxville",
            "latitude": 35.9617,
            "longitude": -83.9232,
        },
        {"neighborhood": "Old City", "latitude": 35.9617, "longitude": -83.9232},
        {"neighborhood": "Fourth and Gill", "latitude": 35.9617, "longitude": -83.9232},
        {"neighborhood": "Fort Sanders", "latitude": 35.9617, "longitude": -83.9232},
        {"neighborhood": "Bearden", "latitude": 35.9617, "longitude": -83.9232},
    ],
    "Overland Park,KS": [
        {
            "neighborhood": "Downtown Overland Park",
            "latitude": 38.88694444,
            "longitude": -94.68694444,
        },
        {
            "neighborhood": "St. Andrews",
            "latitude": 38.88694444,
            "longitude": -94.68694444,
        },
        {
            "neighborhood": "South Overland Park",
            "latitude": 38.88694444,
            "longitude": -94.68694444,
        },
    ],
    "Birmingham,AL": [
        {
            "neighborhood": "Downtown Birmingham",
            "latitude": 33.524755,
            "longitude": -86.81274,
        },
        {
            "neighborhood": "Avondale",
            "latitude": 33.52400833,
            "longitude": -86.77804444,
        },
        {"neighborhood": "Lakeview", "latitude": 33.5175, "longitude": -86.80944444},
    ],
    "Grand Rapids,MI": [
        {
            "neighborhood": "Downtown Grand Rapids",
            "latitude": 47.23722222,
            "longitude": -93.53027778,
        },
        {
            "neighborhood": "Heritage Hill",
            "latitude": 42.96333333,
            "longitude": -85.66777778,
        },
        {
            "neighborhood": "East Grand Rapids",
            "latitude": 47.23722222,
            "longitude": -93.53027778,
        },
    ],
    "Vancouver,WA": [
        {
            "neighborhood": "Downtown Vancouver",
            "latitude": 45.63111111,
            "longitude": -122.67166667,
        },
        {
            "neighborhood": "Hudson's Bay",
            "latitude": 45.63111111,
            "longitude": -122.67166667,
        },
        {
            "neighborhood": "Esther Short",
            "latitude": 45.63111111,
            "longitude": -122.67166667,
        },
        {
            "neighborhood": "Fisher's Landing",
            "latitude": 45.63111111,
            "longitude": -122.67166667,
        },
    ],
    "Montgomery,AL": [
        {
            "neighborhood": "Downtown Montgomery",
            "latitude": 32.3675,
            "longitude": -86.3,
        },
        {"neighborhood": "Old Cloverdale", "latitude": 32.3675, "longitude": -86.3},
        {"neighborhood": "Cloverdale", "latitude": 32.3675, "longitude": -86.3},
        {"neighborhood": "Garden District", "latitude": 32.3675, "longitude": -86.3},
        {"neighborhood": "Capitol Heights", "latitude": 32.3675, "longitude": -86.3},
    ],
    "Huntington Beach,CA": [
        {
            "neighborhood": "Downtown Huntington Beach",
            "latitude": 33.67636,
            "longitude": -118.0025,
        },
        {
            "neighborhood": "Huntington Harbour",
            "latitude": 33.69277778,
            "longitude": -118.00027778,
        },
        {
            "neighborhood": "SeaCliff",
            "latitude": 33.69277778,
            "longitude": -118.00027778,
        },
    ],
    "Providence,RI": [
        {
            "neighborhood": "Downtown Providence",
            "latitude": 41.82361111,
            "longitude": -71.42222222,
        },
        {
            "neighborhood": "Federal Hill",
            "latitude": 41.82361111,
            "longitude": -71.42222222,
        },
        {
            "neighborhood": "College Hill",
            "latitude": 41.82361111,
            "longitude": -71.42222222,
        },
        {
            "neighborhood": "Smith Hill",
            "latitude": 41.82361111,
            "longitude": -71.42222222,
        },
        {"neighborhood": "Fox Point", "latitude": 41.8191, "longitude": -71.398},
    ],
    "Brownsville,TX": [
        {
            "neighborhood": "Downtown Brownsville",
            "latitude": 25.93027778,
            "longitude": -97.48444444,
        },
        {
            "neighborhood": "Mitte Cultural District",
            "latitude": 25.93027778,
            "longitude": -97.48444444,
        },
        {"neighborhood": "Sunrise Mall", "latitude": 25.9021, "longitude": -97.5104},
        {
            "neighborhood": "Jacinto Lopez",
            "latitude": 29.425,
            "longitude": -98.49388889,
        },
    ],
    "Tempe,AZ": [
        {
            "neighborhood": "Roosevelt",
            "latitude": 33.41277778,
            "longitude": -111.94305556,
        },
        {
            "neighborhood": "Downtown Lakes",
            "latitude": 33.41277778,
            "longitude": -111.94305556,
        },
    ],
    "Akron,OH": [
        {
            "neighborhood": "Downtown Akron",
            "latitude": 41.08055556,
            "longitude": -81.52222222,
        },
        {
            "neighborhood": "North Hill",
            "latitude": 41.08055556,
            "longitude": -81.52222222,
        },
        {
            "neighborhood": "West Hill",
            "latitude": 41.08055556,
            "longitude": -81.52222222,
        },
        {
            "neighborhood": "Goodyear Heights",
            "latitude": 41.08055556,
            "longitude": -81.52222222,
        },
    ],
    "Glendale,CA": [
        {
            "neighborhood": "Downtown Glendale",
            "latitude": 34.14611111,
            "longitude": -118.255,
        },
        {
            "neighborhood": "Glendale Galleria",
            "latitude": 34.14611111,
            "longitude": -118.255,
        },
        {
            "neighborhood": "Verdugo Woodlands",
            "latitude": 34.21666667,
            "longitude": -118.28333333,
        },
    ],
    "Chattanooga,TN": [
        {
            "neighborhood": "Downtown Chattanooga",
            "latitude": 35.04555556,
            "longitude": -85.26722222,
        },
        {
            "neighborhood": "North Shore",
            "latitude": 35.04555556,
            "longitude": -85.26722222,
        },
        {
            "neighborhood": "Southside",
            "latitude": 35.04555556,
            "longitude": -85.26722222,
        },
        {
            "neighborhood": "St. Elmo",
            "latitude": 35.04555556,
            "longitude": -85.26722222,
        },
        {
            "neighborhood": "Lookout Mountain",
            "latitude": 35.04555556,
            "longitude": -85.26722222,
        },
    ],
    "Fort Lauderdale,FL": [
        {
            "neighborhood": "Downtown Fort Lauderdale",
            "latitude": 26.0725,
            "longitude": -80.15277778,
        },
        {"neighborhood": "Las Olas", "latitude": 26.13333333, "longitude": -80.15},
        {
            "neighborhood": "Riverwalk Fort Lauderdale",
            "latitude": 26.13333333,
            "longitude": -80.15,
        },
        {
            "neighborhood": "Victoria Park",
            "latitude": 26.0725,
            "longitude": -80.15277778,
        },
    ],
    "Newport News,VA": [
        {
            "neighborhood": "Downtown Newport News",
            "latitude": 37.07083333,
            "longitude": -76.48444444,
        },
        {
            "neighborhood": "Hilton Village",
            "latitude": 37.07083333,
            "longitude": -76.48444444,
        },
        {
            "neighborhood": "Lee Hall",
            "latitude": 37.07083333,
            "longitude": -76.48444444,
        },
        {
            "neighborhood": "Menchville",
            "latitude": 37.07083333,
            "longitude": -76.48444444,
        },
        {
            "neighborhood": "Oyster Point",
            "latitude": 37.07083333,
            "longitude": -76.48444444,
        },
    ],
    "Mobile,AL": [
        {
            "neighborhood": "Downtown Mobile",
            "latitude": 30.6675,
            "longitude": -88.10111111,
        },
        {
            "neighborhood": "Midtown Mobile",
            "latitude": 30.6675,
            "longitude": -88.10111111,
        },
        {
            "neighborhood": "Spring Hill",
            "latitude": 30.69416667,
            "longitude": -88.13722222,
        },
        {
            "neighborhood": "Toulminville",
            "latitude": 30.6675,
            "longitude": -88.10111111,
        },
    ],
    "Ontario,CA": [
        {
            "neighborhood": "Downtown Ontario",
            "latitude": 43.74166667,
            "longitude": -79.37333333,
        },
        {"neighborhood": "New Model Colony", "latitude": 46.5, "longitude": -66.0},
        {"neighborhood": "North Ontario", "latitude": 49.25, "longitude": -84.5},
        {"neighborhood": "Shepherd Park", "latitude": 45.22629, "longitude": -76.19452},
    ],
    "Clarksville,TN": [
        {
            "neighborhood": "Downtown Clarksville",
            "latitude": 36.52972222,
            "longitude": -87.35944444,
        },
        {
            "neighborhood": "New Providence",
            "latitude": 36.52972222,
            "longitude": -87.35944444,
        },
        {
            "neighborhood": "North Clarksville",
            "latitude": 36.52972222,
            "longitude": -87.35944444,
        },
    ],
    "Cary,NC": [
        {"neighborhood": "Green Level", "latitude": 35.78194444, "longitude": -78.82},
        {"neighborhood": "Park West", "latitude": 35.78194444, "longitude": -78.82},
        {
            "neighborhood": "Research Triangle Park",
            "latitude": 35.88,
            "longitude": -78.79,
        },
    ],
    "Elk Grove,CA": [
        {
            "neighborhood": "Downtown Elk Grove",
            "latitude": 38.43833333,
            "longitude": -121.38194444,
        },
        {"neighborhood": "Laguna", "latitude": 38.41805556, "longitude": -121.46916667},
        {
            "neighborhood": "Laguna West",
            "latitude": 38.41805556,
            "longitude": -121.46916667,
        },
        {
            "neighborhood": "Old Town Elk Grove",
            "latitude": 38.40103,
            "longitude": -121.37279,
        },
        {"neighborhood": "Sheldon", "latitude": 38.40103, "longitude": -121.37279},
    ],
    "Shreveport,LA": [
        {
            "neighborhood": "Allendale",
            "latitude": 32.46388889,
            "longitude": -93.79444444,
        },
        {
            "neighborhood": "Downtown Shreveport",
            "latitude": 32.46388889,
            "longitude": -93.79444444,
        },
        {
            "neighborhood": "Highland",
            "latitude": 32.46388889,
            "longitude": -93.79444444,
        },
        {
            "neighborhood": "South Highlands",
            "latitude": 32.46388889,
            "longitude": -93.79444444,
        },
    ],
    "Eugene,OR": [
        {
            "neighborhood": "Downtown Eugene",
            "latitude": 44.05638889,
            "longitude": -123.1175,
        },
        {"neighborhood": "Fairmount", "latitude": 44.05638889, "longitude": -123.1175},
        {
            "neighborhood": "Jefferson Westside",
            "latitude": 44.04611111,
            "longitude": -123.10861111,
        },
        {
            "neighborhood": "South University",
            "latitude": 44.05638889,
            "longitude": -123.1175,
        },
        {"neighborhood": "Whiteaker", "latitude": 44.058356, "longitude": -123.105326},
    ],
    "Aurora,IL": [
        {
            "neighborhood": "Downtown Aurora",
            "latitude": 41.76388889,
            "longitude": -88.29,
        },
        {"neighborhood": "East Aurora", "latitude": 41.76388889, "longitude": -88.29},
        {"neighborhood": "Fox Valley", "latitude": 41.76388889, "longitude": -88.29},
        {
            "neighborhood": "Near West Side",
            "latitude": 41.88,
            "longitude": -87.66666667,
        },
    ],
    "Salem,OR": [
        {
            "neighborhood": "Downtown Salem",
            "latitude": 36.10277778,
            "longitude": -80.26083333,
        },
        {"neighborhood": "East Lancaster", "latitude": 44.9418, "longitude": -122.9865},
        {"neighborhood": "Faye Wright", "latitude": 44.89181, "longitude": -123.0474},
        {
            "neighborhood": "North Salem",
            "latitude": 42.52222222,
            "longitude": -70.89611111,
        },
        {
            "neighborhood": "South Salem",
            "latitude": 42.52222222,
            "longitude": -70.89611111,
        },
    ],
    "Santa Rosa,CA": [
        {
            "neighborhood": "Downtown Santa Rosa",
            "latitude": 38.44861111,
            "longitude": -122.70472222,
        },
        {
            "neighborhood": "West End",
            "latitude": 38.44861111,
            "longitude": -122.70472222,
        },
        {
            "neighborhood": "Junior College Neighborhood",
            "latitude": 38.44861111,
            "longitude": -122.70472222,
        },
        {
            "neighborhood": "Cherry Street District",
            "latitude": 38.44861111,
            "longitude": -122.70472222,
        },
    ],
    "Rancho Cucamonga,CA": [
        {
            "neighborhood": "North Rancho Cucamonga",
            "latitude": 34.106683,
            "longitude": -117.6107,
        },
        {
            "neighborhood": "South Rancho Cucamonga",
            "latitude": 34.12333333,
            "longitude": -117.57944444,
        },
        {
            "neighborhood": "Rancho Etiwanda",
            "latitude": 34.106683,
            "longitude": -117.6107,
        },
        {
            "neighborhood": "Terra Vista",
            "latitude": 34.12333333,
            "longitude": -117.57944444,
        },
        {
            "neighborhood": "Victoria Gardens",
            "latitude": 34.10138889,
            "longitude": -117.53833333,
        },
    ],
    "Pembroke Pines,FL": [
        {
            "neighborhood": "Downtown Pembroke Pines",
            "latitude": 26.13333333,
            "longitude": -80.15,
        },
        {
            "neighborhood": "Silver Lakes",
            "latitude": 26.0125,
            "longitude": -80.31361111,
        },
        {
            "neighborhood": "Pembroke Falls",
            "latitude": 26.0125,
            "longitude": -80.31361111,
        },
    ],
    "Fort Collins,CO": [
        {
            "neighborhood": "Downtown Fort Collins",
            "latitude": 40.55916667,
            "longitude": -105.07805556,
        },
        {
            "neighborhood": "Harmony Corridor",
            "latitude": 40.55916667,
            "longitude": -105.07805556,
        },
        {
            "neighborhood": "Campus West",
            "latitude": 40.55916667,
            "longitude": -105.07805556,
        },
        {
            "neighborhood": "Fossil Lake",
            "latitude": 40.55916667,
            "longitude": -105.07805556,
        },
    ],
    "Springfield,MO": [
        {
            "neighborhood": "Downtown Springfield",
            "latitude": 37.21527778,
            "longitude": -93.29833333,
        },
        {
            "neighborhood": "Midtown Springfield",
            "latitude": 37.21527778,
            "longitude": -93.29833333,
        },
        {
            "neighborhood": "Park Central Square",
            "latitude": 37.21527778,
            "longitude": -93.29833333,
        },
        {
            "neighborhood": "Rountree",
            "latitude": 37.21527778,
            "longitude": -93.29833333,
        },
        {
            "neighborhood": "Phelps Grove",
            "latitude": 37.21527778,
            "longitude": -93.29833333,
        },
    ],
    "Oceanside,CA": [
        {
            "neighborhood": "Downtown Oceanside",
            "latitude": 33.19706667,
            "longitude": -117.37414167,
        },
        {
            "neighborhood": "South Oceanside",
            "latitude": 33.19706667,
            "longitude": -117.37414167,
        },
        {
            "neighborhood": "Mira Costa",
            "latitude": 33.21166667,
            "longitude": -117.32583333,
        },
        {
            "neighborhood": "San Luis Rey",
            "latitude": 33.21166667,
            "longitude": -117.32583333,
        },
    ],
    "Garden Grove,CA": [
        {
            "neighborhood": "Downtown Garden Grove",
            "latitude": 36.61777778,
            "longitude": -121.91666667,
        },
        {
            "neighborhood": "West Garden Grove",
            "latitude": 33.77888889,
            "longitude": -117.96027778,
        },
        {
            "neighborhood": "East Garden Grove",
            "latitude": 33.77888889,
            "longitude": -117.96027778,
        },
        {
            "neighborhood": "Fountain Valley",
            "latitude": 33.70861111,
            "longitude": -117.95638889,
        },
    ],
    "Lancaster,CA": [
        {
            "neighborhood": "Downtown Lancaster",
            "latitude": 34.68333333,
            "longitude": -118.15,
        },
        {
            "neighborhood": "West Lancaster",
            "latitude": 34.68333333,
            "longitude": -118.15,
        },
    ],
    "Murfreesboro,TN": [
        {
            "neighborhood": "Downtown Murfreesboro",
            "latitude": 35.84611111,
            "longitude": -86.39194444,
        },
        {
            "neighborhood": "Historic District",
            "latitude": 35.84611111,
            "longitude": -86.39194444,
        },
        {
            "neighborhood": "Northwest Murfreesboro",
            "latitude": 35.84611111,
            "longitude": -86.39194444,
        },
        {
            "neighborhood": "Blackman",
            "latitude": 35.84611111,
            "longitude": -86.39194444,
        },
    ],
    "Palmdale,CA": [
        {
            "neighborhood": "Downtown Palmdale",
            "latitude": 34.58111111,
            "longitude": -118.10055556,
        },
        {
            "neighborhood": "Avenue S",
            "latitude": 34.58111111,
            "longitude": -118.10055556,
        },
        {
            "neighborhood": "Anaverde",
            "latitude": 34.58111111,
            "longitude": -118.10055556,
        },
    ],
    "Corona,CA": [
        {
            "neighborhood": "Downtown Corona",
            "latitude": 33.86666667,
            "longitude": -117.56666667,
        },
        {
            "neighborhood": "Corona Hills",
            "latitude": 33.86666667,
            "longitude": -117.56666667,
        },
        {
            "neighborhood": "South Corona",
            "latitude": 33.86666667,
            "longitude": -117.56666667,
        },
        {
            "neighborhood": "Dos Lagos",
            "latitude": 33.86666667,
            "longitude": -117.56666667,
        },
        {
            "neighborhood": "Eagle Glen",
            "latitude": 33.86666667,
            "longitude": -117.56666667,
        },
    ],
    "Killeen,TX": [
        {
            "neighborhood": "Downtown Killeen",
            "latitude": 31.10555556,
            "longitude": -97.72666667,
        },
        {
            "neighborhood": "North Killeen",
            "latitude": 31.10555556,
            "longitude": -97.72666667,
        },
        {
            "neighborhood": "South Killeen",
            "latitude": 31.10555556,
            "longitude": -97.72666667,
        },
        {
            "neighborhood": "West Killeen",
            "latitude": 31.10555556,
            "longitude": -97.72666667,
        },
    ],
    "Salinas,CA": [
        {
            "neighborhood": "Downtown Salinas",
            "latitude": 36.67777778,
            "longitude": -121.65555556,
        },
        {"neighborhood": "Alisal", "latitude": 36.67777778, "longitude": -121.65555556},
        {
            "neighborhood": "East Salinas",
            "latitude": 36.67777778,
            "longitude": -121.65555556,
        },
    ],
    "Roseville,CA": [
        {
            "neighborhood": "Downtown Roseville",
            "latitude": 38.7525,
            "longitude": -121.28944444,
        },
        {
            "neighborhood": "Folsom Road",
            "latitude": 38.67222222,
            "longitude": -121.15777778,
        },
        {
            "neighborhood": "Lead Hill",
            "latitude": 38.58166667,
            "longitude": -121.49444444,
        },
    ],
    "Denton,TX": [
        {
            "neighborhood": "Downtown Denton",
            "latitude": 33.21638889,
            "longitude": -97.12916667,
        },
        {
            "neighborhood": "Oak Street",
            "latitude": 32.77916667,
            "longitude": -96.80888889,
        },
        {
            "neighborhood": "University Drive",
            "latitude": 32.77916667,
            "longitude": -96.80888889,
        },
        {"neighborhood": "Cooper Street", "latitude": 32.763, "longitude": -97.0326},
    ],
    "Surprise,AZ": [
        {"neighborhood": "Downtown Surprise", "latitude": 33.17, "longitude": -112.04},
        {"neighborhood": "Asante", "latitude": 33.63055556, "longitude": -112.36666667},
        {
            "neighborhood": "Marley Park",
            "latitude": 33.63055556,
            "longitude": -112.36666667,
        },
        {"neighborhood": "Sierra Montana", "latitude": 44.4, "longitude": -110.6},
    ],
    "Macon,GA": [
        {"neighborhood": "Cherry Street", "latitude": 32.8328, "longitude": -83.6148},
        {"neighborhood": "Rivoli", "latitude": 32.8745862, "longitude": -83.7124689},
        {
            "neighborhood": "Ingleside",
            "latitude": 32.83472222,
            "longitude": -83.65166667,
        },
    ],
    "Paterson,NJ": [
        {
            "neighborhood": "Downtown Paterson",
            "latitude": 40.914746,
            "longitude": -74.162826,
        },
        {
            "neighborhood": "Wrigley Park",
            "latitude": 40.914746,
            "longitude": -74.162826,
        },
        {
            "neighborhood": "Riverside Village",
            "latitude": 40.914746,
            "longitude": -74.162826,
        },
        {
            "neighborhood": "People's Park",
            "latitude": 40.914746,
            "longitude": -74.162826,
        },
        {"neighborhood": "Lakeview", "latitude": 40.914746, "longitude": -74.162826},
    ],
    "Lakewood,CO": [
        {
            "neighborhood": "Downtown Lakewood",
            "latitude": 39.70472222,
            "longitude": -105.11722222,
        },
        {"neighborhood": "Belmar", "latitude": 39.707332, "longitude": -105.077661},
        {
            "neighborhood": "Wheat Ridge",
            "latitude": 39.76611111,
            "longitude": -105.07722222,
        },
        {
            "neighborhood": "Green Mountain",
            "latitude": 39.70472222,
            "longitude": -105.11722222,
        },
    ],
    "Hayward,CA": [
        {
            "neighborhood": "Downtown Hayward",
            "latitude": 37.66882,
            "longitude": -122.080796,
        },
        {
            "neighborhood": "Jackson Triangle",
            "latitude": 37.66882,
            "longitude": -122.080796,
        },
        {
            "neighborhood": "Harder-Tennyson",
            "latitude": 37.66882,
            "longitude": -122.080796,
        },
        {"neighborhood": "Glen Eden", "latitude": 37.65, "longitude": -121.91},
    ],
    "Charleston,SC": [
        {
            "neighborhood": "Downtown Charleston",
            "latitude": 32.78333333,
            "longitude": -79.93194444,
        },
        {
            "neighborhood": "Harleston Village",
            "latitude": 32.7804961,
            "longitude": -79.9446713,
        },
        {
            "neighborhood": "Ansonborough",
            "latitude": 32.78555556,
            "longitude": -79.93694444,
        },
    ],
    "Alexandria,VA": [
        {
            "neighborhood": "Potomac Yard",
            "latitude": 38.8296006,
            "longitude": -77.049618,
        },
        {
            "neighborhood": "Rosemont",
            "latitude": 38.82027778,
            "longitude": -77.05027778,
        },
    ],
    "Hollywood,FL": [
        {
            "neighborhood": "Downtown Hollywood",
            "latitude": 26.02138889,
            "longitude": -80.175,
        },
        {
            "neighborhood": "Hollywood Beach",
            "latitude": 26.02138889,
            "longitude": -80.175,
        },
        {"neighborhood": "Liberia", "latitude": 25.79333333, "longitude": -80.29055556},
        {
            "neighborhood": "Washington Park",
            "latitude": 26.02138889,
            "longitude": -80.175,
        },
        {
            "neighborhood": "Emerald Hills",
            "latitude": 26.17638889,
            "longitude": -80.14444444,
        },
    ],
    "Springfield,MA": [
        {
            "neighborhood": "Downtown Springfield",
            "latitude": 42.10138889,
            "longitude": -72.59027778,
        },
        {
            "neighborhood": "South End",
            "latitude": 42.10138889,
            "longitude": -72.59027778,
        },
        {
            "neighborhood": "Liberty Heights",
            "latitude": 42.10138889,
            "longitude": -72.59027778,
        },
        {
            "neighborhood": "East Springfield",
            "latitude": 42.10138889,
            "longitude": -72.59027778,
        },
        {"neighborhood": "Forest Park", "latitude": 42.07502778, "longitude": -72.5685},
    ],
    "Kansas City,KS": [
        {
            "neighborhood": "Downtown Kansas City",
            "latitude": 37.97694444,
            "longitude": -100.85277778,
        },
        {"neighborhood": "Midtown", "latitude": 39.09972222, "longitude": -94.57833333},
        {
            "neighborhood": "Overland Park",
            "latitude": 38.88694444,
            "longitude": -94.68694444,
        },
        {"neighborhood": "Olathe", "latitude": 38.88277778, "longitude": -94.82027778},
        {"neighborhood": "Shawnee", "latitude": 39.01583333, "longitude": -94.8075},
    ],
    "Sunnyvale,CA": [
        {
            "neighborhood": "Downtown Sunnyvale",
            "latitude": 37.37111111,
            "longitude": -122.0375,
        },
        {
            "neighborhood": "Heritage District",
            "latitude": 37.37111111,
            "longitude": -122.0375,
        },
        {
            "neighborhood": "Washington Park",
            "latitude": 37.37111111,
            "longitude": -122.0375,
        },
        {"neighborhood": "Ponderosa", "latitude": 37.37111111, "longitude": -122.0375},
    ],
    "Bellevue,WA": [
        {
            "neighborhood": "Downtown Bellevue",
            "latitude": 47.61444444,
            "longitude": -122.15361111,
        },
        {
            "neighborhood": "Bellevue Downtown",
            "latitude": 47.61444444,
            "longitude": -122.15361111,
        },
        {
            "neighborhood": "Wilburton",
            "latitude": 47.61444444,
            "longitude": -122.15361111,
        },
        {
            "neighborhood": "Crossroads",
            "latitude": 47.61444444,
            "longitude": -122.15361111,
        },
    ],
    "Joliet,IL": [
        {
            "neighborhood": "Downtown Joliet",
            "latitude": 41.52972222,
            "longitude": -88.07277778,
        },
        {
            "neighborhood": "Near West Side",
            "latitude": 41.52972222,
            "longitude": -88.07277778,
        },
        {
            "neighborhood": "West Side",
            "latitude": 41.52972222,
            "longitude": -88.07277778,
        },
        {
            "neighborhood": "South Side",
            "latitude": 41.52972222,
            "longitude": -88.07277778,
        },
        {
            "neighborhood": "East Side",
            "latitude": 41.52972222,
            "longitude": -88.07277778,
        },
    ],
    "Naperville,IL": [
        {
            "neighborhood": "Downtown Naperville",
            "latitude": 41.74826,
            "longitude": -88.16585,
        },
        {"neighborhood": "River Run", "latitude": 41.74826, "longitude": -88.16585},
        {"neighborhood": "Willow Creek", "latitude": 41.85195, "longitude": -88.08567},
    ],
    "Escondido,CA": [
        {
            "neighborhood": "Downtown Escondido",
            "latitude": 33.12472222,
            "longitude": -117.08083333,
        },
        {
            "neighborhood": "Old Escondido",
            "latitude": 33.12472222,
            "longitude": -117.08083333,
        },
        {
            "neighborhood": "North Broadway",
            "latitude": 33.12472222,
            "longitude": -117.08083333,
        },
        {
            "neighborhood": "East Valley Parkway",
            "latitude": 33.12472222,
            "longitude": -117.08083333,
        },
        {
            "neighborhood": "Kit Carson Park",
            "latitude": 33.12472222,
            "longitude": -117.08083333,
        },
    ],
    "Bridgeport,CT": [
        {
            "neighborhood": "Downtown Bridgeport",
            "latitude": 41.18638889,
            "longitude": -73.19555556,
        },
        {
            "neighborhood": "Black Rock",
            "latitude": 41.15861111,
            "longitude": -73.22527778,
        },
        {
            "neighborhood": "North Bridgeport",
            "latitude": 41.18638889,
            "longitude": -73.19555556,
        },
    ],
    "Savannah,GA": [
        {
            "neighborhood": "Historic District",
            "latitude": 32.07444444,
            "longitude": -81.09166667,
        },
        {
            "neighborhood": "Victorian District",
            "latitude": 32.07444444,
            "longitude": -81.09166667,
        },
        {
            "neighborhood": "Ardsley Park",
            "latitude": 32.08111111,
            "longitude": -81.09111111,
        },
        {
            "neighborhood": "Wilmington Island",
            "latitude": 32.00333333,
            "longitude": -80.97527778,
        },
    ],
    "Olathe,KS": [
        {
            "neighborhood": "Downtown Olathe",
            "latitude": 38.86666667,
            "longitude": -94.86666667,
        },
        {
            "neighborhood": "Olathe Station",
            "latitude": 38.88277778,
            "longitude": -94.82027778,
        },
        {
            "neighborhood": "Prairie Village",
            "latitude": 38.88694444,
            "longitude": -94.68694444,
        },
        {
            "neighborhood": "Mahaffie",
            "latitude": 38.88277778,
            "longitude": -94.82027778,
        },
    ],
    "Mesquite,TX": [
        {
            "neighborhood": "Pleasant Grove",
            "latitude": 32.77916667,
            "longitude": -96.80888889,
        }
    ],
    "Pasadena,TX": [
        {
            "neighborhood": "Downtown Pasadena",
            "latitude": 29.67611111,
            "longitude": -95.17388889,
        },
        {
            "neighborhood": "East End",
            "latitude": 29.67611111,
            "longitude": -95.17388889,
        },
        {
            "neighborhood": "Golden Acres",
            "latitude": 29.67611111,
            "longitude": -95.17388889,
        },
        {
            "neighborhood": "Red Bluff",
            "latitude": 29.67611111,
            "longitude": -95.17388889,
        },
    ],
    "McAllen,TX": [
        {
            "neighborhood": "Downtown McAllen",
            "latitude": 26.21638889,
            "longitude": -98.23638889,
        },
        {
            "neighborhood": "Arts District",
            "latitude": 26.21638889,
            "longitude": -98.23638889,
        },
        {
            "neighborhood": "North McAllen",
            "latitude": 26.21638889,
            "longitude": -98.23638889,
        },
        {
            "neighborhood": "South McAllen",
            "latitude": 26.21638889,
            "longitude": -98.23638889,
        },
        {
            "neighborhood": "West McAllen",
            "latitude": 26.21638889,
            "longitude": -98.23638889,
        },
    ],
    "Rockford,IL": [
        {
            "neighborhood": "Downtown Rockford",
            "latitude": 42.27113,
            "longitude": -89.094,
        },
        {"neighborhood": "Haight Village", "latitude": 42.27113, "longitude": -89.094},
        {"neighborhood": "Midtown", "latitude": 41.88194444, "longitude": -87.62777778},
        {
            "neighborhood": "Cherry Valley",
            "latitude": 42.23472222,
            "longitude": -88.94888889,
        },
    ],
    "Gainesville,FL": [
        {
            "neighborhood": "Downtown Gainesville",
            "latitude": 29.65199722,
            "longitude": -82.32499167,
        },
        {
            "neighborhood": "University Heights",
            "latitude": 29.78722222,
            "longitude": -82.03305556,
        },
        {
            "neighborhood": "Archer Road",
            "latitude": 29.65199722,
            "longitude": -82.32499167,
        },
        {
            "neighborhood": "Haile Plantation",
            "latitude": 29.65199722,
            "longitude": -82.32499167,
        },
    ],
    "Syracuse,NY": [
        {
            "neighborhood": "Downtown Syracuse",
            "latitude": 43.04694444,
            "longitude": -76.14444444,
        },
        {
            "neighborhood": "Armory Square",
            "latitude": 43.04694444,
            "longitude": -76.14444444,
        },
        {
            "neighborhood": "University Hill",
            "latitude": 43.04694444,
            "longitude": -76.14444444,
        },
        {"neighborhood": "Westcott", "latitude": 43.041, "longitude": -76.1212},
        {
            "neighborhood": "Tipperary Hill",
            "latitude": 43.04694444,
            "longitude": -76.14444444,
        },
    ],
    "Pomona,CA": [
        {
            "neighborhood": "Downtown Pomona",
            "latitude": 34.06083333,
            "longitude": -117.75583333,
        },
        {
            "neighborhood": "Pomona Valley",
            "latitude": 34.06083333,
            "longitude": -117.75583333,
        },
        {"neighborhood": "Phillips Ranch", "latitude": 34.0361, "longitude": -117.7842},
        {
            "neighborhood": "Barber City",
            "latitude": 34.09805556,
            "longitude": -117.71388889,
        },
    ],
    "Visalia,CA": [
        {
            "neighborhood": "Downtown Visalia",
            "latitude": 36.33027778,
            "longitude": -119.2925,
        },
        {
            "neighborhood": "Southwest Visalia",
            "latitude": 36.33027778,
            "longitude": -119.2925,
        },
        {
            "neighborhood": "East Visalia",
            "latitude": 36.33027778,
            "longitude": -119.2925,
        },
        {"neighborhood": "Mooney", "latitude": 36.33027778, "longitude": -119.2925},
    ],
    "Thornton,CO": [
        {
            "neighborhood": "Thornton Heights",
            "latitude": 39.90305556,
            "longitude": -104.95444444,
        },
        {
            "neighborhood": "North Thornton",
            "latitude": 39.90305556,
            "longitude": -104.95444444,
        },
        {
            "neighborhood": "East Thornton",
            "latitude": 39.90305556,
            "longitude": -104.95444444,
        },
    ],
    "Waco,TX": [
        {
            "neighborhood": "Downtown Waco",
            "latitude": 31.55138889,
            "longitude": -97.15583333,
        },
        {
            "neighborhood": "Austin Avenue",
            "latitude": 31.55138889,
            "longitude": -97.15583333,
        },
        {
            "neighborhood": "Baylor University Area",
            "latitude": 31.55138889,
            "longitude": -97.15583333,
        },
        {
            "neighborhood": "Brook Oaks",
            "latitude": 32.77916667,
            "longitude": -96.80888889,
        },
    ],
    "Jackson,MS": [
        {
            "neighborhood": "Belhaven",
            "latitude": 32.29888889,
            "longitude": -90.18472222,
        },
        {
            "neighborhood": "LeFleur's Bluff",
            "latitude": 32.29888889,
            "longitude": -90.18472222,
        },
        {
            "neighborhood": "North Jackson",
            "latitude": 32.29888889,
            "longitude": -90.18472222,
        },
    ],
    "Columbia,SC": [
        {
            "neighborhood": "Downtown Columbia",
            "latitude": 34.00055556,
            "longitude": -81.03472222,
        },
        {
            "neighborhood": "The Vista",
            "latitude": 34.00055556,
            "longitude": -81.03472222,
        },
        {
            "neighborhood": "Five Points",
            "latitude": 34.00055556,
            "longitude": -81.03472222,
        },
    ],
    "Lakewood,NJ": [
        {
            "neighborhood": "Downtown Lakewood",
            "latitude": 40.09145,
            "longitude": -74.21207,
        },
        {
            "neighborhood": "Lake Carasaljo",
            "latitude": 40.077069,
            "longitude": -74.19851,
        },
        {
            "neighborhood": "East Lakewood",
            "latitude": 40.077069,
            "longitude": -74.19851,
        },
        {
            "neighborhood": "West Lakewood",
            "latitude": 40.077069,
            "longitude": -74.19851,
        },
        {"neighborhood": "Hebrew Park", "latitude": 40.077069, "longitude": -74.19851},
    ],
    "Fullerton,CA": [
        {
            "neighborhood": "Downtown Fullerton",
            "latitude": 33.88,
            "longitude": -117.92861111,
        },
        {"neighborhood": "Sunny Hills", "latitude": 33.88, "longitude": -117.92861111},
        {
            "neighborhood": "West Fullerton",
            "latitude": 33.88,
            "longitude": -117.92861111,
        },
        {
            "neighborhood": "East Fullerton",
            "latitude": 33.88,
            "longitude": -117.92861111,
        },
        {
            "neighborhood": "Raymond Hills",
            "latitude": 33.88,
            "longitude": -117.92861111,
        },
    ],
    "Torrance,CA": [
        {
            "neighborhood": "Downtown Torrance",
            "latitude": 33.83472222,
            "longitude": -118.34138889,
        },
        {
            "neighborhood": "Old Town Torrance",
            "latitude": 33.83472222,
            "longitude": -118.34138889,
        },
        {"neighborhood": "Walteria", "latitude": 33.805, "longitude": -118.35111111},
    ],
    "Victorville,CA": [
        {
            "neighborhood": "Downtown Victorville",
            "latitude": 34.5375,
            "longitude": -117.29333333,
        },
        {
            "neighborhood": "Spring Valley Lake",
            "latitude": 34.53611111,
            "longitude": -117.29111111,
        },
        {
            "neighborhood": "Victor Valley",
            "latitude": 34.53611111,
            "longitude": -117.29111111,
        },
        {"neighborhood": "Bear Valley", "latitude": 34.53416667, "longitude": -117.205},
    ],
    "Midland,TX": [
        {"neighborhood": "Downtown Midland", "latitude": 32.0, "longitude": -102.1},
        {"neighborhood": "North Midland", "latitude": 32.0, "longitude": -102.1},
        {
            "neighborhood": "Grassland Estates",
            "latitude": 35.19916667,
            "longitude": -101.84527778,
        },
    ],
    "Orange,CA": [
        {"neighborhood": "Old Towne", "latitude": 33.67, "longitude": -117.78},
        {
            "neighborhood": "Downtown Orange",
            "latitude": 33.80305556,
            "longitude": -117.8325,
        },
        {
            "neighborhood": "Orange Park Acres",
            "latitude": 33.80194,
            "longitude": -117.78139,
        },
        {
            "neighborhood": "Villa Park",
            "latitude": 33.81611111,
            "longitude": -117.81111111,
        },
        {
            "neighborhood": "Canyon District",
            "latitude": 33.80305556,
            "longitude": -117.8325,
        },
    ],
    "Miramar,FL": [
        {
            "neighborhood": "Miramar Park",
            "latitude": 25.97888889,
            "longitude": -80.2825,
        },
        {
            "neighborhood": "Silver Lakes",
            "latitude": 25.97888889,
            "longitude": -80.2825,
        },
        {
            "neighborhood": "Miramar Town Center",
            "latitude": 25.97888889,
            "longitude": -80.2825,
        },
        {
            "neighborhood": "Sunset Lakes",
            "latitude": 25.97888889,
            "longitude": -80.2825,
        },
    ],
    "Hampton,VA": [
        {
            "neighborhood": "Downtown Hampton",
            "latitude": 37.02638889,
            "longitude": -76.34444444,
        },
        {"neighborhood": "Phoebus", "latitude": 37.02638889, "longitude": -76.34444444},
        {
            "neighborhood": "Fox Hill",
            "latitude": 37.02638889,
            "longitude": -76.34444444,
        },
        {
            "neighborhood": "Aberdeen Gardens",
            "latitude": 37.03333333,
            "longitude": -76.40583333,
        },
    ],
    "Warren,MI": [
        {"neighborhood": "Downtown Warren", "latitude": 42.5125, "longitude": -83.025},
        {"neighborhood": "Warren Woods", "latitude": 42.5125, "longitude": -83.025},
        {"neighborhood": "Northeast Warren", "latitude": 42.5125, "longitude": -83.025},
        {"neighborhood": "Southeast Warren", "latitude": 42.5125, "longitude": -83.025},
    ],
    "Stamford,CT": [
        {
            "neighborhood": "Downtown Stamford",
            "latitude": 41.05277778,
            "longitude": -73.53888889,
        },
        {
            "neighborhood": "Harbor Point",
            "latitude": 41.05277778,
            "longitude": -73.53888889,
        },
    ],
    "Cedar Rapids,IA": [
        {
            "neighborhood": "Downtown Cedar Rapids",
            "latitude": 41.98305556,
            "longitude": -91.66861111,
        },
        {
            "neighborhood": "Czech Village",
            "latitude": 41.98305556,
            "longitude": -91.66861111,
        },
    ],
    "Elizabeth,NJ": [
        {
            "neighborhood": "Downtown Elizabeth",
            "latitude": 40.663,
            "longitude": -74.214,
        },
        {"neighborhood": "Elizabethport", "latitude": 40.663, "longitude": -74.214},
        {"neighborhood": "Bayway", "latitude": 40.663, "longitude": -74.214},
        {"neighborhood": "Frog Hollow", "latitude": 40.663, "longitude": -74.214},
    ],
    "Palm Bay,FL": [
        {
            "neighborhood": "Downtown Palm Bay",
            "latitude": 28.08388889,
            "longitude": -82.75388889,
        },
        {
            "neighborhood": "Bayside Lakes",
            "latitude": 27.99792222,
            "longitude": -80.67000833,
        },
        {
            "neighborhood": "Palm Bay West",
            "latitude": 27.99792222,
            "longitude": -80.67000833,
        },
        {"neighborhood": "Malabar", "latitude": 27.99792222, "longitude": -80.67000833},
    ],
    "Dayton,OH": [
        {
            "neighborhood": "Downtown Dayton",
            "latitude": 39.75944444,
            "longitude": -84.19166667,
        },
        {
            "neighborhood": "Oregon District",
            "latitude": 39.75944444,
            "longitude": -84.19166667,
        },
        {
            "neighborhood": "South Park",
            "latitude": 39.75944444,
            "longitude": -84.19166667,
        },
        {
            "neighborhood": "Old North Dayton",
            "latitude": 39.75944444,
            "longitude": -84.19166667,
        },
        {
            "neighborhood": "West Carrollton",
            "latitude": 39.66805556,
            "longitude": -84.24722222,
        },
    ],
    "New Haven,CT": [
        {
            "neighborhood": "Downtown New Haven",
            "latitude": 41.26388889,
            "longitude": -72.88666667,
        },
        {"neighborhood": "Fair Haven", "latitude": 41.311, "longitude": -72.896},
    ],
    "Coral Springs,FL": [
        {
            "neighborhood": "North Springs",
            "latitude": 26.27055556,
            "longitude": -80.25916667,
        },
        {
            "neighborhood": "Coral Woods",
            "latitude": 26.27055556,
            "longitude": -80.25916667,
        },
        {
            "neighborhood": "Ramblewood",
            "latitude": 26.27055556,
            "longitude": -80.25916667,
        },
    ],
    "Meridian,ID": [
        {
            "neighborhood": "Downtown Meridian",
            "latitude": 32.37472222,
            "longitude": -88.70416667,
        },
        {
            "neighborhood": "Meridian Heights",
            "latitude": 38.921428,
            "longitude": -77.035816,
        },
    ],
    "West Valley City,UT": [
        {
            "neighborhood": "Downtown West Valley City",
            "latitude": 40.68916667,
            "longitude": -111.99388889,
        },
        {
            "neighborhood": "Valley Fair",
            "latitude": 40.68916667,
            "longitude": -111.99388889,
        },
        {
            "neighborhood": "Granger",
            "latitude": 40.68916667,
            "longitude": -111.99388889,
        },
        {"neighborhood": "Hunter", "latitude": 40.68916667, "longitude": -111.99388889},
    ],
    "Pasadena,CA": [
        {"neighborhood": "Old Town", "latitude": 34.1475, "longitude": -118.14388889},
        {
            "neighborhood": "Downtown Pasadena",
            "latitude": 34.1475,
            "longitude": -118.14388889,
        },
        {"neighborhood": "South Lake", "latitude": 34.1475, "longitude": -118.14388889},
    ],
    "Lewisville,TX": [
        {
            "neighborhood": "Old Town Lewisville",
            "latitude": 33.03833333,
            "longitude": -97.00611111,
        },
        {
            "neighborhood": "Downtown Lewisville",
            "latitude": 33.06916667,
            "longitude": -96.96444444,
        },
        {
            "neighborhood": "The Colony",
            "latitude": 33.09083333,
            "longitude": -96.88472222,
        },
        {
            "neighborhood": "Castle Hills",
            "latitude": 33.03833333,
            "longitude": -97.00611111,
        },
        {
            "neighborhood": "Vista Ridge",
            "latitude": 33.03833333,
            "longitude": -97.00611111,
        },
    ],
    "Kent,WA": [
        {
            "neighborhood": "Downtown Kent",
            "latitude": 47.38277778,
            "longitude": -122.22694444,
        },
        {
            "neighborhood": "Meridian",
            "latitude": 47.37111111,
            "longitude": -122.17916667,
        },
        {
            "neighborhood": "Kent Valley",
            "latitude": 47.38277778,
            "longitude": -122.22694444,
        },
        {
            "neighborhood": "Lake Meridian",
            "latitude": 47.37111111,
            "longitude": -122.17916667,
        },
        {
            "neighborhood": "Covington",
            "latitude": 47.37416667,
            "longitude": -122.11972222,
        },
    ],
    "Sterling Heights,MI": [
        {
            "neighborhood": "Downtown Sterling Heights",
            "latitude": 42.58027778,
            "longitude": -83.03027778,
        },
        {
            "neighborhood": "Sterling Heights Township",
            "latitude": 42.58027778,
            "longitude": -83.03027778,
        },
        {"neighborhood": "Utica", "latitude": 42.58027778, "longitude": -83.03027778},
        {
            "neighborhood": "Shelby Township",
            "latitude": 42.67083333,
            "longitude": -83.03305556,
        },
        {
            "neighborhood": "Macomb Township",
            "latitude": 42.58027778,
            "longitude": -83.03027778,
        },
    ],
    "Fargo,ND": [
        {
            "neighborhood": "Downtown Fargo",
            "latitude": 46.87333333,
            "longitude": -96.82722222,
        },
        {
            "neighborhood": "North Fargo",
            "latitude": 46.87333333,
            "longitude": -96.82722222,
        },
        {
            "neighborhood": "South Fargo",
            "latitude": 46.87333333,
            "longitude": -96.82722222,
        },
    ],
    "Carrollton,TX": [
        {
            "neighborhood": "Old Downtown",
            "latitude": 32.95361111,
            "longitude": -96.89027778,
        },
        {
            "neighborhood": "Trinity Mills",
            "latitude": 32.95361111,
            "longitude": -96.89027778,
        },
        {"neighborhood": "Hebron", "latitude": 32.95361111, "longitude": -96.89027778},
        {"neighborhood": "Creek Valley", "latitude": 33.2, "longitude": -97.12},
    ],
    "Santa Clara,CA": [
        {
            "neighborhood": "Downtown Santa Clara",
            "latitude": 37.36694444,
            "longitude": -121.98388889,
        },
        {
            "neighborhood": "Santa Clara University",
            "latitude": 37.36694444,
            "longitude": -121.98388889,
        },
        {
            "neighborhood": "Lawrence Station",
            "latitude": 37.35305556,
            "longitude": -121.93638889,
        },
    ],
    "Round Rock,TX": [
        {
            "neighborhood": "Downtown Round Rock",
            "latitude": 30.52694444,
            "longitude": -97.66388889,
        },
        {
            "neighborhood": "Old Town",
            "latitude": 30.26722222,
            "longitude": -97.74305556,
        },
        {
            "neighborhood": "Round Rock West",
            "latitude": 30.52694444,
            "longitude": -97.66388889,
        },
        {
            "neighborhood": "Teravista",
            "latitude": 30.52694444,
            "longitude": -97.66388889,
        },
    ],
    "Norman,OK": [
        {
            "neighborhood": "Downtown Norman",
            "latitude": 35.22083333,
            "longitude": -97.44361111,
        },
        {
            "neighborhood": "Campus Corner",
            "latitude": 35.22083333,
            "longitude": -97.44361111,
        },
        {
            "neighborhood": "East Norman",
            "latitude": 35.22083333,
            "longitude": -97.44361111,
        },
    ],
    "Columbia,MO": [
        {
            "neighborhood": "Downtown Columbia",
            "latitude": 38.9475,
            "longitude": -92.32666667,
        },
        {
            "neighborhood": "The District",
            "latitude": 38.9475,
            "longitude": -92.32666667,
        },
        {"neighborhood": "East Campus", "latitude": 38.9475, "longitude": -92.32666667},
        {
            "neighborhood": "Old Southwest",
            "latitude": 38.9475,
            "longitude": -92.32666667,
        },
        {
            "neighborhood": "Shepard Boulevard",
            "latitude": 38.96035,
            "longitude": -92.3662,
        },
    ],
    "Abilene,TX": [
        {"neighborhood": "Downtown Abilene", "latitude": 32.45, "longitude": -99.75},
        {"neighborhood": "North Abilene", "latitude": 32.45, "longitude": -99.75},
        {"neighborhood": "South Abilene", "latitude": 32.45, "longitude": -99.75},
        {"neighborhood": "West Abilene", "latitude": 32.45, "longitude": -99.75},
        {"neighborhood": "Lytle Creek", "latitude": 32.45, "longitude": -99.75},
    ],
    "Athens,GA": [
        {
            "neighborhood": "Downtown Athens",
            "latitude": 33.95,
            "longitude": -83.38333333,
        },
        {"neighborhood": "Five Points", "latitude": 33.95, "longitude": -83.38333333},
        {"neighborhood": "Normaltown", "latitude": 33.95, "longitude": -83.38333333},
        {"neighborhood": "Oconee Heights", "latitude": 33.99, "longitude": -83.71},
    ],
    "Pearland,TX": [
        {
            "neighborhood": "Downtown Pearland",
            "latitude": 29.55444444,
            "longitude": -95.29583333,
        },
        {
            "neighborhood": "Silverlake",
            "latitude": 29.55444444,
            "longitude": -95.29583333,
        },
        {
            "neighborhood": "Pearland Town Center",
            "latitude": 29.55444444,
            "longitude": -95.29583333,
        },
    ],
    "Clovis,CA": [
        {
            "neighborhood": "Downtown Clovis",
            "latitude": 36.82527778,
            "longitude": -119.70305556,
        },
        {
            "neighborhood": "Old Town Clovis",
            "latitude": 36.82527778,
            "longitude": -119.70305556,
        },
        {
            "neighborhood": "Clovis West",
            "latitude": 36.82527778,
            "longitude": -119.70305556,
        },
    ],
    "Topeka,KS": [
        {
            "neighborhood": "Downtown Topeka",
            "latitude": 39.03472222,
            "longitude": -95.69555556,
        },
        {"neighborhood": "Potwin", "latitude": 39.03472222, "longitude": -95.69555556},
    ],
    "College Station,TX": [
        {
            "neighborhood": "Downtown College Station",
            "latitude": 30.60138889,
            "longitude": -96.31444444,
        },
        {
            "neighborhood": "Northgate",
            "latitude": 30.60138889,
            "longitude": -96.31444444,
        },
        {
            "neighborhood": "South College Station",
            "latitude": 30.60138889,
            "longitude": -96.31444444,
        },
        {
            "neighborhood": "Pebble Creek",
            "latitude": 30.592879,
            "longitude": -96.321606,
        },
    ],
    "Simi Valley,CA": [
        {
            "neighborhood": "Downtown Simi Valley",
            "latitude": 34.27027778,
            "longitude": -118.69527778,
        },
        {
            "neighborhood": "Simi Town Center",
            "latitude": 34.27111111,
            "longitude": -118.73944444,
        },
        {
            "neighborhood": "Wood Ranch",
            "latitude": 34.27111111,
            "longitude": -118.73944444,
        },
        {
            "neighborhood": "Big Sky",
            "latitude": 34.27111111,
            "longitude": -118.73944444,
        },
        {"neighborhood": "Madera", "latitude": 34.27111111, "longitude": -118.73944444},
    ],
    "Allentown,PA": [
        {
            "neighborhood": "Center City",
            "latitude": 40.60166667,
            "longitude": -75.47722222,
        },
        {
            "neighborhood": "Old Allentown",
            "latitude": 40.60166667,
            "longitude": -75.47722222,
        },
        {
            "neighborhood": "South Side",
            "latitude": 40.60166667,
            "longitude": -75.47722222,
        },
        {
            "neighborhood": "East Side",
            "latitude": 40.60166667,
            "longitude": -75.47722222,
        },
    ],
    "West Palm Beach,FL": [
        {
            "neighborhood": "Downtown",
            "latitude": 26.70972222,
            "longitude": -80.06416667,
        },
        {"neighborhood": "El Cid", "latitude": 26.70972222, "longitude": -80.06416667},
        {
            "neighborhood": "Flamingo Park",
            "latitude": 26.70972222,
            "longitude": -80.06416667,
        },
        {
            "neighborhood": "Northwood",
            "latitude": 26.70972222,
            "longitude": -80.06416667,
        },
    ],
    "Thousand Oaks,CA": [
        {
            "neighborhood": "Downtown Thousand Oaks",
            "latitude": 34.18944444,
            "longitude": -118.875,
        },
        {"neighborhood": "Newbury Park", "latitude": 34.18417, "longitude": -118.90972},
        {"neighborhood": "North Ranch", "latitude": 34.18944444, "longitude": -118.875},
        {"neighborhood": "Oak Park", "latitude": 34.18944444, "longitude": -118.875},
        {
            "neighborhood": "Westlake Village",
            "latitude": 34.14194444,
            "longitude": -118.81944444,
        },
    ],
    "Vallejo,CA": [
        {
            "neighborhood": "Downtown Vallejo",
            "latitude": 38.11305556,
            "longitude": -122.23583333,
        },
        {
            "neighborhood": "Mare Island",
            "latitude": 38.095254,
            "longitude": -122.278004,
        },
        {
            "neighborhood": "North Vallejo",
            "latitude": 38.11305556,
            "longitude": -122.23583333,
        },
        {
            "neighborhood": "South Vallejo",
            "latitude": 38.11305556,
            "longitude": -122.23583333,
        },
        {
            "neighborhood": "Glen Cove",
            "latitude": 38.11305556,
            "longitude": -122.23583333,
        },
    ],
    "Wilmington,NC": [
        {
            "neighborhood": "Downtown Wilmington",
            "latitude": 34.21,
            "longitude": -77.88666667,
        },
        {
            "neighborhood": "Historic District",
            "latitude": 34.21,
            "longitude": -77.88666667,
        },
        {
            "neighborhood": "Wrightsville Beach",
            "latitude": 34.21138889,
            "longitude": -77.79638889,
        },
        {
            "neighborhood": "Carolina Beach",
            "latitude": 34.03972222,
            "longitude": -77.89611111,
        },
        {"neighborhood": "Masonboro", "latitude": 34.21, "longitude": -77.88666667},
    ],
    "Rochester,MN": [
        {
            "neighborhood": "Downtown Rochester",
            "latitude": 44.02333333,
            "longitude": -92.46138889,
        },
        {
            "neighborhood": "Northwest Rochester",
            "latitude": 44.02333333,
            "longitude": -92.46138889,
        },
    ],
    "Concord,CA": [
        {
            "neighborhood": "Downtown Concord",
            "latitude": 37.97805556,
            "longitude": -122.03111111,
        },
        {
            "neighborhood": "Clayton Valley",
            "latitude": 37.97805556,
            "longitude": -122.03111111,
        },
        {
            "neighborhood": "Pleasant Hill",
            "latitude": 37.93611111,
            "longitude": -122.08861111,
        },
        {
            "neighborhood": "Bay Point",
            "latitude": 37.97805556,
            "longitude": -122.03111111,
        },
    ],
    "Lakeland,FL": [
        {
            "neighborhood": "Downtown Lakeland",
            "latitude": 28.05555556,
            "longitude": -81.95444444,
        },
        {
            "neighborhood": "Lake Mirror Park",
            "latitude": 28.05555556,
            "longitude": -81.95444444,
        },
        {
            "neighborhood": "Lakeland Highlands",
            "latitude": 28.05555556,
            "longitude": -81.95444444,
        },
        {
            "neighborhood": "South Lakeland",
            "latitude": 28.05555556,
            "longitude": -81.95444444,
        },
        {
            "neighborhood": "North Lakeland",
            "latitude": 28.05555556,
            "longitude": -81.95444444,
        },
    ],
    "North Charleston,SC": [
        {
            "neighborhood": "Downtown North Charleston",
            "latitude": 32.89861111,
            "longitude": -80.04055556,
        },
        {
            "neighborhood": "Park Circle",
            "latitude": 32.88527778,
            "longitude": -80.01694444,
        },
        {
            "neighborhood": "Northwoods Mall",
            "latitude": 32.79805556,
            "longitude": -80.03194444,
        },
        {
            "neighborhood": "Charleston Heights",
            "latitude": 32.88527778,
            "longitude": -80.01694444,
        },
        {
            "neighborhood": "Ashley Phosphate",
            "latitude": 32.88527778,
            "longitude": -80.01694444,
        },
    ],
    "Lafayette,LA": [
        {
            "neighborhood": "Downtown Lafayette",
            "latitude": 30.21666667,
            "longitude": -92.03333333,
        },
        {
            "neighborhood": "Breaux Bridge",
            "latitude": 30.27363889,
            "longitude": -91.89933333,
        },
        {
            "neighborhood": "Carencro",
            "latitude": 30.31416667,
            "longitude": -92.04361111,
        },
    ],
    "Arvada,CO": [
        {"neighborhood": "Belmar", "latitude": 39.73876, "longitude": -105.16473},
        {"neighborhood": "Fairview", "latitude": 39.8028, "longitude": -105.0875},
        {
            "neighborhood": "Historic Olde Town",
            "latitude": 39.8028,
            "longitude": -105.0875,
        },
    ],
    "Independence,MO": [
        {
            "neighborhood": "39th Street",
            "latitude": 39.07833333,
            "longitude": -94.41944444,
        },
        {
            "neighborhood": "Downtown Independence",
            "latitude": 39.07833333,
            "longitude": -94.41944444,
        },
    ],
    "Billings,MT": [
        {
            "neighborhood": "Downtown Billings",
            "latitude": 45.78361111,
            "longitude": -108.50611111,
        },
        {
            "neighborhood": "Heights",
            "latitude": 45.78361111,
            "longitude": -108.50611111,
        },
        {
            "neighborhood": "Lockwood",
            "latitude": 45.78361111,
            "longitude": -108.50611111,
        },
        {
            "neighborhood": "Rimrock",
            "latitude": 45.78361111,
            "longitude": -108.50611111,
        },
        {"neighborhood": "Shiloh", "latitude": 45.78361111, "longitude": -108.50611111},
    ],
    "Fairfield,CA": [
        {
            "neighborhood": "Downtown Fairfield",
            "latitude": 38.25777778,
            "longitude": -122.05416667,
        },
        {
            "neighborhood": "Green Valley",
            "latitude": 38.25777778,
            "longitude": -122.05416667,
        },
        {
            "neighborhood": "Paradise Valley",
            "latitude": 38.25777778,
            "longitude": -122.05416667,
        },
        {
            "neighborhood": "Rancho Solano",
            "latitude": 38.25777778,
            "longitude": -122.05416667,
        },
        {
            "neighborhood": "Suisun Valley",
            "latitude": 38.26277778,
            "longitude": -121.9275,
        },
    ],
    "Hartford,CT": [
        {"neighborhood": "Asylum Hill", "latitude": 41.7625, "longitude": -72.67416667},
        {
            "neighborhood": "Barry Square",
            "latitude": 41.7625,
            "longitude": -72.67416667,
        },
        {
            "neighborhood": "Behind the Rocks",
            "latitude": 41.7625,
            "longitude": -72.67416667,
        },
        {
            "neighborhood": "Downtown Hartford",
            "latitude": 41.7625,
            "longitude": -72.67416667,
        },
        {
            "neighborhood": "Sheldon-Charter Oak",
            "latitude": 41.7625,
            "longitude": -72.67416667,
        },
    ],
    "Ann Arbor,MI": [
        {
            "neighborhood": "Downtown Ann Arbor",
            "latitude": 42.274,
            "longitude": -83.683,
        },
        {
            "neighborhood": "Kerrytown",
            "latitude": 42.28138889,
            "longitude": -83.74833333,
        },
        {
            "neighborhood": "Lower Burns Park",
            "latitude": 42.27694444,
            "longitude": -83.73805556,
        },
        {
            "neighborhood": "Old West Side",
            "latitude": 42.28138889,
            "longitude": -83.74833333,
        },
    ],
    "Broken Arrow,OK": [
        {
            "neighborhood": "Broken Arrow Downtown",
            "latitude": 36.03638889,
            "longitude": -95.78361111,
        },
        {
            "neighborhood": "Turtle Creek",
            "latitude": 31.71388889,
            "longitude": -110.0675,
        },
    ],
    "Berkeley,CA": [
        {
            "neighborhood": "Berkeley Hills",
            "latitude": 37.87166667,
            "longitude": -122.27277778,
        },
        {
            "neighborhood": "Downtown Berkeley",
            "latitude": 37.87166667,
            "longitude": -122.27277778,
        },
        {
            "neighborhood": "Elmwood",
            "latitude": 37.87166667,
            "longitude": -122.27277778,
        },
        {
            "neighborhood": "North Berkeley",
            "latitude": 37.87166667,
            "longitude": -122.27277778,
        },
        {
            "neighborhood": "South Berkeley",
            "latitude": 37.87166667,
            "longitude": -122.27277778,
        },
    ],
    "Cambridge,MA": [
        {"neighborhood": "Cambridgeport", "latitude": 42.36, "longitude": -71.1075},
        {
            "neighborhood": "East Cambridge",
            "latitude": 42.37361111,
            "longitude": -71.11055556,
        },
        {
            "neighborhood": "Harvard Square",
            "latitude": 42.37444444,
            "longitude": -71.11694444,
        },
        {
            "neighborhood": "Kendall Square",
            "latitude": 42.37361111,
            "longitude": -71.11055556,
        },
        {"neighborhood": "MIT", "latitude": 42.37361111, "longitude": -71.11055556},
    ],
    "Richardson,TX": [
        {
            "neighborhood": "Canyon Creek",
            "latitude": 32.99166667,
            "longitude": -96.70388889,
        },
        {
            "neighborhood": "Downtown Richardson",
            "latitude": 32.99166667,
            "longitude": -96.70388889,
        },
        {
            "neighborhood": "Heights Park",
            "latitude": 32.77916667,
            "longitude": -96.80888889,
        },
    ],
    "Antioch,CA": [
        {
            "neighborhood": "Downtown Antioch",
            "latitude": 38.005,
            "longitude": -121.80583333,
        },
        {"neighborhood": "Lone Tree", "latitude": 38.005, "longitude": -121.80583333},
        {"neighborhood": "Marsh Creek", "latitude": 38.005, "longitude": -121.80583333},
        {"neighborhood": "Hillcrest", "latitude": 38.005, "longitude": -121.80583333},
    ],
    "High Point,NC": [
        {
            "neighborhood": "Downtown High Point",
            "latitude": 35.99111111,
            "longitude": -79.99361111,
        },
        {
            "neighborhood": "Emerywood",
            "latitude": 35.99111111,
            "longitude": -79.99361111,
        },
        {
            "neighborhood": "Fairview",
            "latitude": 35.99111111,
            "longitude": -79.99361111,
        },
        {
            "neighborhood": "West End",
            "latitude": 35.99111111,
            "longitude": -79.99361111,
        },
    ],
    "Clearwater,FL": [
        {
            "neighborhood": "Downtown Clearwater",
            "latitude": 27.97361111,
            "longitude": -82.76416667,
        },
        {
            "neighborhood": "Clearwater Beach",
            "latitude": 27.979931,
            "longitude": -82.827232,
        },
        {
            "neighborhood": "Island Estates",
            "latitude": 27.97361111,
            "longitude": -82.76416667,
        },
        {
            "neighborhood": "Harbor Oaks",
            "latitude": 27.97361111,
            "longitude": -82.76416667,
        },
    ],
    "League City,TX": [
        {
            "neighborhood": "Downtown League City",
            "latitude": 32.77916667,
            "longitude": -96.80888889,
        },
        {
            "neighborhood": "Victory Lakes",
            "latitude": 29.49972222,
            "longitude": -95.08972222,
        },
        {
            "neighborhood": "South Shore Harbour",
            "latitude": 29.499797,
            "longitude": -95.089784,
        },
        {
            "neighborhood": "Magnolia Creek",
            "latitude": 29.49972222,
            "longitude": -95.08972222,
        },
    ],
    "Odessa,TX": [
        {
            "neighborhood": "Downtown Odessa",
            "latitude": 31.86333333,
            "longitude": -102.36555556,
        },
        {"neighborhood": "Gardens", "latitude": 32.0, "longitude": -102.1},
        {"neighborhood": "Village", "latitude": 32.0, "longitude": -102.1},
    ],
    "Manchester,NH": [
        {
            "neighborhood": "Downtown Manchester",
            "latitude": 42.99083333,
            "longitude": -71.46361111,
        },
        {
            "neighborhood": "North End",
            "latitude": 42.99083333,
            "longitude": -71.46361111,
        },
        {
            "neighborhood": "West Side",
            "latitude": 42.99083333,
            "longitude": -71.46361111,
        },
        {
            "neighborhood": "South End",
            "latitude": 42.99083333,
            "longitude": -71.46361111,
        },
    ],
    "Evansville,IN": [
        {
            "neighborhood": "Downtown Evansville",
            "latitude": 37.97722222,
            "longitude": -87.55055556,
        },
        {
            "neighborhood": "Riverview",
            "latitude": 37.97166667,
            "longitude": -87.57291667,
        },
        {
            "neighborhood": "Bayard Park",
            "latitude": 37.97722222,
            "longitude": -87.55055556,
        },
    ],
    "Waterbury,CT": [
        {
            "neighborhood": "Downtown Waterbury",
            "latitude": 41.55611111,
            "longitude": -73.04138889,
        },
        {
            "neighborhood": "Overlook",
            "latitude": 41.55611111,
            "longitude": -73.04138889,
        },
        {
            "neighborhood": "Bucks Hill",
            "latitude": 41.55611111,
            "longitude": -73.04138889,
        },
        {
            "neighborhood": "Waterville",
            "latitude": 41.55611111,
            "longitude": -73.04138889,
        },
    ],
    "West Jordan,UT": [
        {
            "neighborhood": "Downtown West Jordan",
            "latitude": 40.60638889,
            "longitude": -111.97611111,
        },
        {
            "neighborhood": "Oquirrh Shadows",
            "latitude": 40.65305556,
            "longitude": -112.00666667,
        },
        {
            "neighborhood": "Copper Creek",
            "latitude": 40.89777778,
            "longitude": -111.97361111,
        },
        {
            "neighborhood": "South Jordan Parkway",
            "latitude": 40.56166667,
            "longitude": -111.96083333,
        },
    ],
    "Las Cruces,NM": [
        {
            "neighborhood": "Downtown Las Cruces",
            "latitude": 32.31444444,
            "longitude": -106.77888889,
        },
        {
            "neighborhood": "Mesilla",
            "latitude": 32.31222222,
            "longitude": -106.77833333,
        },
        {
            "neighborhood": "University Hills",
            "latitude": 32.31222222,
            "longitude": -106.77833333,
        },
        {
            "neighborhood": "Picacho Hills",
            "latitude": 32.31222222,
            "longitude": -106.77833333,
        },
    ],
    "Westminster,CO": [
        {
            "neighborhood": "Downtown Westminster",
            "latitude": 49.20694444,
            "longitude": -122.91111111,
        },
        {
            "neighborhood": "Westminster Village",
            "latitude": 43.06944444,
            "longitude": -72.45388889,
        },
        {
            "neighborhood": "Bradburn Village",
            "latitude": 39.88361111,
            "longitude": -105.0625,
        },
        {
            "neighborhood": "Legacy Ridge",
            "latitude": 39.88361111,
            "longitude": -105.0625,
        },
    ],
    "Lowell,MA": [
        {
            "neighborhood": "Belvidere",
            "latitude": 42.63944444,
            "longitude": -71.31472222,
        },
        {
            "neighborhood": "The Acre",
            "latitude": 42.63944444,
            "longitude": -71.31472222,
        },
        {
            "neighborhood": "Pawtucketville",
            "latitude": 42.63944444,
            "longitude": -71.31472222,
        },
    ],
    "Nampa,ID": [
        {
            "neighborhood": "Downtown Nampa",
            "latitude": 43.60138889,
            "longitude": -116.52777778,
        },
        {"neighborhood": "North End", "latitude": 45.0, "longitude": -115.0},
        {"neighborhood": "Southwest Nampa", "latitude": 43.63, "longitude": -116.71},
        {
            "neighborhood": "Karcher",
            "latitude": 43.60138889,
            "longitude": -116.52777778,
        },
    ],
    "Richmond,CA": [
        {
            "neighborhood": "Downtown Richmond",
            "latitude": 37.93583333,
            "longitude": -122.34777778,
        },
        {
            "neighborhood": "Point Richmond",
            "latitude": 37.93583333,
            "longitude": -122.34777778,
        },
        {"neighborhood": "Marina Bay", "latitude": 37.9128, "longitude": -122.3465},
        {
            "neighborhood": "El Sobrante Hills",
            "latitude": 37.93583333,
            "longitude": -122.34777778,
        },
        {
            "neighborhood": "Iron Triangle",
            "latitude": 37.93574,
            "longitude": -122.36002,
        },
    ],
    "Pompano Beach,FL": [
        {
            "neighborhood": "Downtown Pompano Beach",
            "latitude": 26.23472222,
            "longitude": -80.12555556,
        },
        {
            "neighborhood": "Collier City",
            "latitude": 26.23472222,
            "longitude": -80.12555556,
        },
        {
            "neighborhood": "Golf Course",
            "latitude": 26.23472222,
            "longitude": -80.12555556,
        },
        {
            "neighborhood": "Cypress Bend",
            "latitude": 26.23472222,
            "longitude": -80.12555556,
        },
    ],
    "Carlsbad,CA": [
        {
            "neighborhood": "Downtown Carlsbad",
            "latitude": 33.12194444,
            "longitude": -117.29694444,
        },
        {
            "neighborhood": "Carlsbad Village",
            "latitude": 33.12194444,
            "longitude": -117.29694444,
        },
        {
            "neighborhood": "La Costa",
            "latitude": 33.12194444,
            "longitude": -117.29694444,
        },
        {"neighborhood": "Aviara", "latitude": 33.10416667, "longitude": -117.29583333},
    ],
    "Menifee,CA": [
        {
            "neighborhood": "Downtown Menifee",
            "latitude": 33.50333333,
            "longitude": -117.12361111,
        },
        {"neighborhood": "Sun City", "latitude": 33.708, "longitude": -117.199},
        {
            "neighborhood": "Menifee Lakes",
            "latitude": 33.69083333,
            "longitude": -117.185,
        },
        {
            "neighborhood": "Quail Valley",
            "latitude": 33.706595,
            "longitude": -117.246094,
        },
    ],
    "Provo,UT": [
        {
            "neighborhood": "Downtown Provo",
            "latitude": 40.24444444,
            "longitude": -111.66083333,
        },
        {
            "neighborhood": "Joaquin",
            "latitude": 40.24444444,
            "longitude": -111.66083333,
        },
        {
            "neighborhood": "Provo Bay",
            "latitude": 40.24444444,
            "longitude": -111.66083333,
        },
    ],
    "Elgin,IL": [
        {
            "neighborhood": "South Elgin",
            "latitude": 41.99777778,
            "longitude": -88.30777778,
        },
        {
            "neighborhood": "Elgin Hills",
            "latitude": 42.03833333,
            "longitude": -88.32277778,
        },
    ],
    "Greeley,CO": [
        {
            "neighborhood": "Downtown Greeley",
            "latitude": 40.42333333,
            "longitude": -104.70916667,
        },
        {"neighborhood": "Evans", "latitude": 40.42333333, "longitude": -104.70916667},
        {
            "neighborhood": "Garden City",
            "latitude": 40.42333333,
            "longitude": -104.70916667,
        },
    ],
    "Springfield,IL": [
        {
            "neighborhood": "Downtown Springfield",
            "latitude": 39.7975,
            "longitude": -89.645,
        },
        {"neighborhood": "Enos Park", "latitude": 39.7975, "longitude": -89.645},
        {"neighborhood": "Lincoln Park", "latitude": 39.7975, "longitude": -89.645},
        {"neighborhood": "Westside", "latitude": 41.65722222, "longitude": -87.68},
    ],
    "Beaumont,TX": [
        {
            "neighborhood": "Downtown Beaumont",
            "latitude": 30.08,
            "longitude": -94.12666667,
        },
        {"neighborhood": "South Park", "latitude": 30.08, "longitude": -94.12666667},
        {"neighborhood": "West End", "latitude": 30.08, "longitude": -94.12666667},
    ],
    "Lansing,MI": [
        {
            "neighborhood": "Downtown Lansing",
            "latitude": 42.71416667,
            "longitude": -84.56,
        },
        {"neighborhood": "Eastside", "latitude": 42.71416667, "longitude": -84.56},
        {"neighborhood": "Genesee", "latitude": 42.74694444, "longitude": -83.14305556},
        {"neighborhood": "Old Town", "latitude": 42.747427, "longitude": -84.549518},
        {"neighborhood": "REO Town", "latitude": 42.717, "longitude": -84.5537},
    ],
    "Murrieta,CA": [
        {
            "neighborhood": "Cal Oaks",
            "latitude": 33.50333333,
            "longitude": -117.12361111,
        },
        {
            "neighborhood": "Downtown Murrieta",
            "latitude": 33.56944444,
            "longitude": -117.2025,
        },
    ],
    "Goodyear,AZ": [
        {"neighborhood": "Canyon Trails", "latitude": 33.17, "longitude": -112.04},
        {
            "neighborhood": "Downtown Goodyear",
            "latitude": 33.45,
            "longitude": -112.35833333,
        },
        {
            "neighborhood": "Estrella",
            "latitude": 33.35191111,
            "longitude": -112.42914167,
        },
        {"neighborhood": "Palm Valley", "latitude": 33.45, "longitude": -112.35833333},
        {
            "neighborhood": "Sundance",
            "latitude": 33.37055556,
            "longitude": -112.59083333,
        },
    ],
    "Allen,TX": [
        {
            "neighborhood": "Allen Heights",
            "latitude": 33.12694444,
            "longitude": -96.66305556,
        },
        {
            "neighborhood": "Downtown Allen",
            "latitude": 33.12694444,
            "longitude": -96.66305556,
        },
        {
            "neighborhood": "Twin Creeks",
            "latitude": 33.12694444,
            "longitude": -96.66305556,
        },
    ],
    "Tuscaloosa,AL": [
        {
            "neighborhood": "Downtown Tuscaloosa",
            "latitude": 33.20972222,
            "longitude": -87.56916667,
        },
        {
            "neighborhood": "Lake Tuscaloosa",
            "latitude": 33.20972222,
            "longitude": -87.56916667,
        },
        {
            "neighborhood": "Taylorville",
            "latitude": 33.20972222,
            "longitude": -87.56916667,
        },
    ],
    "Everett,WA": [
        {
            "neighborhood": "Bayside",
            "latitude": 47.97916667,
            "longitude": -122.20166667,
        },
        {
            "neighborhood": "Downtown Everett",
            "latitude": 47.97916667,
            "longitude": -122.20166667,
        },
        {
            "neighborhood": "Evergreen",
            "latitude": 47.97916667,
            "longitude": -122.20166667,
        },
        {"neighborhood": "Holly", "latitude": 47.97916667, "longitude": -122.20166667},
    ],
    "Pueblo,CO": [
        {"neighborhood": "Beulah", "latitude": 38.0722, "longitude": -104.9664},
        {
            "neighborhood": "Minnequa",
            "latitude": 38.26694444,
            "longitude": -104.62027778,
        },
        {
            "neighborhood": "Regency",
            "latitude": 35.32880556,
            "longitude": -106.56555556,
        },
    ],
    "New Braunfels,TX": [
        {
            "neighborhood": "Downtown New Braunfels",
            "latitude": 29.725,
            "longitude": -98.12555556,
        },
        {"neighborhood": "Gruene", "latitude": 29.73833333, "longitude": -98.10388889},
        {"neighborhood": "Lake Dunlap", "latitude": 29.425, "longitude": -98.49388889},
        {"neighborhood": "Seele", "latitude": 29.725, "longitude": -98.12555556},
    ],
    "South Fulton,GA": [
        {"neighborhood": "Red Oak", "latitude": 33.5925899, "longitude": -84.6729381},
        {"neighborhood": "Fulton Industrial", "latitude": 33.79, "longitude": -84.47},
        {
            "neighborhood": "Camp Creek",
            "latitude": 33.5925899,
            "longitude": -84.6729381,
        },
        {"neighborhood": "Ben Hill", "latitude": 33.5925899, "longitude": -84.6729381},
    ],
    "Miami Gardens,FL": [
        {"neighborhood": "Andover", "latitude": 25.96611111, "longitude": -80.20527778},
        {
            "neighborhood": "Carol City",
            "latitude": 25.94111111,
            "longitude": -80.24527778,
        },
        {
            "neighborhood": "Lake Lucerne",
            "latitude": 25.94111111,
            "longitude": -80.24527778,
        },
        {"neighborhood": "Norland", "latitude": 25.94111111, "longitude": -80.24527778},
    ],
    "Gresham,OR": [
        {
            "neighborhood": "Downtown Gresham",
            "latitude": 45.48277778,
            "longitude": -122.43333333,
        },
        {
            "neighborhood": "Gresham Butte",
            "latitude": 45.48277778,
            "longitude": -122.43333333,
        },
        {"neighborhood": "Hogan", "latitude": 45.48277778, "longitude": -122.43333333},
        {
            "neighborhood": "Kelly Creek",
            "latitude": 45.48277778,
            "longitude": -122.43333333,
        },
    ],
    "Temecula,CA": [
        {
            "neighborhood": "Old Town",
            "latitude": 33.50333333,
            "longitude": -117.12361111,
        },
        {
            "neighborhood": "Downtown Temecula",
            "latitude": 33.50333333,
            "longitude": -117.12361111,
        },
        {
            "neighborhood": "Rancho California",
            "latitude": 33.50333333,
            "longitude": -117.12361111,
        },
        {
            "neighborhood": "Temecula Valley",
            "latitude": 33.50333333,
            "longitude": -117.12361111,
        },
    ],
    "Rio Rancho,NM": [
        {
            "neighborhood": "Enchanted Hills",
            "latitude": 35.28611111,
            "longitude": -106.67055556,
        },
        {
            "neighborhood": "Vista Hills",
            "latitude": 35.28611111,
            "longitude": -106.67055556,
        },
    ],
    "Peoria,IL": [
        {
            "neighborhood": "Downtown Peoria",
            "latitude": 40.69277778,
            "longitude": -89.59055556,
        },
        {
            "neighborhood": "East Bluff",
            "latitude": 40.69277778,
            "longitude": -89.59055556,
        },
        {
            "neighborhood": "North Valley",
            "latitude": 40.69277778,
            "longitude": -89.59055556,
        },
        {
            "neighborhood": "Peoria Heights",
            "latitude": 40.74666667,
            "longitude": -89.57,
        },
        {
            "neighborhood": "West Bluff",
            "latitude": 40.69277778,
            "longitude": -89.59055556,
        },
    ],
    "Tyler,TX": [
        {
            "neighborhood": "Azalea District",
            "latitude": 32.35138889,
            "longitude": -95.30111111,
        },
        {
            "neighborhood": "Downtown Tyler",
            "latitude": 32.35138889,
            "longitude": -95.30111111,
        },
        {
            "neighborhood": "South Tyler",
            "latitude": 32.35138889,
            "longitude": -95.30111111,
        },
    ],
    "Sparks,NV": [
        {
            "neighborhood": "Downtown Sparks",
            "latitude": 39.55444444,
            "longitude": -119.73555556,
        },
        {
            "neighborhood": "Spanish Springs",
            "latitude": 39.55444444,
            "longitude": -119.73555556,
        },
        {
            "neighborhood": "Sparks Marina",
            "latitude": 39.55444444,
            "longitude": -119.73555556,
        },
        {
            "neighborhood": "Wingfield Springs",
            "latitude": 39.52722222,
            "longitude": -119.82194444,
        },
    ],
    "Concord,NC": [
        {
            "neighborhood": "Downtown Concord",
            "latitude": 35.41027778,
            "longitude": -80.58527778,
        },
        {
            "neighborhood": "Historic District",
            "latitude": 35.41027778,
            "longitude": -80.58527778,
        },
        {
            "neighborhood": "Logan Community",
            "latitude": 35.433361,
            "longitude": -80.582324,
        },
        {
            "neighborhood": "North Concord",
            "latitude": 35.41027778,
            "longitude": -80.58527778,
        },
        {"neighborhood": "Odell", "latitude": 35.41027778, "longitude": -80.58527778},
    ],
    "Santa Maria,CA": [
        {
            "neighborhood": "Downtown Santa Maria",
            "latitude": 34.95138889,
            "longitude": -120.43333333,
        },
        {
            "neighborhood": "Fremont Avenue",
            "latitude": 38.44861111,
            "longitude": -122.70472222,
        },
        {
            "neighborhood": "North Santa Maria",
            "latitude": 34.95138889,
            "longitude": -120.43333333,
        },
        {
            "neighborhood": " Orcutt",
            "latitude": 34.95138889,
            "longitude": -120.43333333,
        },
    ],
    "Ventura,CA": [
        {
            "neighborhood": "Downtown Ventura",
            "latitude": 34.275,
            "longitude": -119.22777778,
        },
        {
            "neighborhood": "Midtown Ventura",
            "latitude": 34.275,
            "longitude": -119.22777778,
        },
        {
            "neighborhood": "Ventura Keys",
            "latitude": 34.275,
            "longitude": -119.22777778,
        },
        {
            "neighborhood": "East Ventura",
            "latitude": 34.275,
            "longitude": -119.22777778,
        },
    ],
    "Buckeye,AZ": [
        {
            "neighborhood": "Downtown Buckeye",
            "latitude": 33.37055556,
            "longitude": -112.59083333,
        },
        {
            "neighborhood": "Verrado",
            "latitude": 33.37055556,
            "longitude": -112.59083333,
        },
        {
            "neighborhood": "Sundance",
            "latitude": 33.37055556,
            "longitude": -112.59083333,
        },
        {
            "neighborhood": "Festival Ranch",
            "latitude": 33.37055556,
            "longitude": -112.59083333,
        },
        {
            "neighborhood": "Tartesso",
            "latitude": 33.37055556,
            "longitude": -112.59083333,
        },
    ],
    "Downey,CA": [
        {
            "neighborhood": "Downtown Downey",
            "latitude": 33.93805556,
            "longitude": -118.13083333,
        },
        {
            "neighborhood": "Stonewood",
            "latitude": 33.93805556,
            "longitude": -118.13083333,
        },
        {"neighborhood": "Brookshire", "latitude": 33.9353, "longitude": -118.1303},
        {
            "neighborhood": "Columbia",
            "latitude": 33.93805556,
            "longitude": -118.13083333,
        },
    ],
    "Sugar Land,TX": [
        {
            "neighborhood": "Downtown Sugar Land",
            "latitude": 29.59944444,
            "longitude": -95.61416667,
        },
        {
            "neighborhood": "Sugar Creek",
            "latitude": 29.59944444,
            "longitude": -95.61416667,
        },
        {
            "neighborhood": "Riverstone",
            "latitude": 29.59944444,
            "longitude": -95.61416667,
        },
        {
            "neighborhood": "First Colony",
            "latitude": 29.59944444,
            "longitude": -95.61416667,
        },
        {
            "neighborhood": "New Territory",
            "latitude": 29.59472222,
            "longitude": -95.6775,
        },
    ],
    "Costa Mesa,CA": [
        {"neighborhood": "Downtown Costa Mesa", "latitude": 34.0, "longitude": -118.2},
        {"neighborhood": "Mesa Verde", "latitude": 33.72, "longitude": -118.04},
        {
            "neighborhood": "South Coast Metro",
            "latitude": 33.665,
            "longitude": -117.91222222,
        },
        {"neighborhood": "Westside Costa Mesa", "latitude": 34.0, "longitude": -118.2},
    ],
    "Conroe,TX": [
        {
            "neighborhood": "Downtown Conroe",
            "latitude": 30.31611111,
            "longitude": -95.45888889,
        },
        {
            "neighborhood": "April Sound",
            "latitude": 29.76277778,
            "longitude": -95.38305556,
        },
        {
            "neighborhood": "Grand Central Park",
            "latitude": 29.76277778,
            "longitude": -95.38305556,
        },
        {"neighborhood": "Woodforest", "latitude": 30.1775, "longitude": -95.50388889},
    ],
    "Spokane Valley,WA": [
        {
            "neighborhood": "Downtown Spokane Valley",
            "latitude": 47.63055556,
            "longitude": -117.26166667,
        },
        {
            "neighborhood": "Mirabeau Park",
            "latitude": 47.63055556,
            "longitude": -117.26166667,
        },
        {"neighborhood": "Greenacres", "latitude": 47.7174, "longitude": -117.047423},
        {"neighborhood": "Opportunity", "latitude": 47.7174, "longitude": -117.047423},
        {
            "neighborhood": "Trentwood",
            "latitude": 47.63055556,
            "longitude": -117.26166667,
        },
    ],
    "Davie,FL": [
        {
            "neighborhood": "Hollywood Lakes",
            "latitude": 26.193535,
            "longitude": -80.476683,
        }
    ],
    "Hillsboro,OR": [
        {
            "neighborhood": "Downtown Hillsboro",
            "latitude": 45.52722222,
            "longitude": -122.93611111,
        },
        {
            "neighborhood": "Orenco Station",
            "latitude": 45.53055556,
            "longitude": -122.91666667,
        },
        {"neighborhood": "Tanasbourne", "latitude": 45.53649, "longitude": -122.878288},
        {
            "neighborhood": "Amberglen",
            "latitude": 45.52722222,
            "longitude": -122.93611111,
        },
        {
            "neighborhood": "Jackson School",
            "latitude": 36.10656,
            "longitude": -86.81191,
        },
    ],
    "Jurupa Valley,CA": [
        {
            "neighborhood": "Downtown Jurupa Valley",
            "latitude": 34.0,
            "longitude": -117.34,
        },
        {
            "neighborhood": "Glen Avon",
            "latitude": 34.01722222,
            "longitude": -117.49194444,
        },
        {
            "neighborhood": "Mira Loma",
            "latitude": 33.98472222,
            "longitude": -117.51527778,
        },
        {"neighborhood": "Pedley", "latitude": 34.0, "longitude": -117.48333333},
    ],
    "Centennial,CO": [
        {
            "neighborhood": "Downtown Centennial",
            "latitude": 43.78163333,
            "longitude": -79.23456111,
        },
        {
            "neighborhood": "Centennial Hills",
            "latitude": 39.97944444,
            "longitude": -75.20916667,
        },
        {
            "neighborhood": "Willow Creek",
            "latitude": 39.60388889,
            "longitude": -104.76027778,
        },
        {
            "neighborhood": "Eagle Ridge",
            "latitude": 39.60388889,
            "longitude": -104.76027778,
        },
        {"neighborhood": "Foxfield", "latitude": 39.58666667, "longitude": -104.7875},
    ],
    "Edison,NJ": [
        {"neighborhood": "Menlo Park", "latitude": 40.565, "longitude": -74.3375},
        {"neighborhood": "Oak Tree", "latitude": 40.5274, "longitude": -74.3933},
        {"neighborhood": "Pumptown", "latitude": 40.5274, "longitude": -74.3933},
    ],
    "Boulder,CO": [
        {
            "neighborhood": "Downtown Boulder",
            "latitude": 40.015,
            "longitude": -105.2705,
        },
        {
            "neighborhood": "Mapleton Hill",
            "latitude": 40.05972222,
            "longitude": -105.41888889,
        },
        {"neighborhood": "Whittier", "latitude": 40.014485, "longitude": -105.201221},
        {
            "neighborhood": "Gunbarrel",
            "latitude": 40.06333333,
            "longitude": -105.17138889,
        },
    ],
    "Dearborn,MI": [
        {
            "neighborhood": "Downtown Dearborn",
            "latitude": 42.31444444,
            "longitude": -83.21333333,
        },
        {
            "neighborhood": "East Dearborn",
            "latitude": 42.31444444,
            "longitude": -83.21333333,
        },
        {
            "neighborhood": "West Dearborn",
            "latitude": 42.31444444,
            "longitude": -83.21333333,
        },
        {
            "neighborhood": "Southwest Dearborn",
            "latitude": 42.305,
            "longitude": -83.165,
        },
    ],
    "Edinburg,TX": [
        {
            "neighborhood": "Cameron Park",
            "latitude": 26.21638889,
            "longitude": -98.23638889,
        }
    ],
    "Sandy Springs,GA": [
        {
            "neighborhood": "Downtown Sandy Springs",
            "latitude": 33.92416667,
            "longitude": -84.37861111,
        },
        {
            "neighborhood": "Ridgeview",
            "latitude": 33.92416667,
            "longitude": -84.37861111,
        },
    ],
    "Green Bay,WI": [
        {
            "neighborhood": "Downtown Green Bay",
            "latitude": 44.51333333,
            "longitude": -88.01583333,
        },
        {
            "neighborhood": "Olde Main",
            "latitude": 44.79874167,
            "longitude": -93.45336944,
        },
        {"neighborhood": "Allouez", "latitude": 44.75, "longitude": -88.0},
        {
            "neighborhood": "Ashwaubenon",
            "latitude": 44.48333333,
            "longitude": -88.08333333,
        },
    ],
    "West Covina,CA": [
        {
            "neighborhood": "Downtown West Covina",
            "latitude": 34.09166667,
            "longitude": -117.87916667,
        },
        {
            "neighborhood": "Vincent",
            "latitude": 34.09166667,
            "longitude": -117.87916667,
        },
        {"neighborhood": "Valley Boulevard", "latitude": 34.0, "longitude": -118.2},
        {
            "neighborhood": "Cameron Park",
            "latitude": 34.05666667,
            "longitude": -117.91861111,
        },
        {
            "neighborhood": "South Hills",
            "latitude": 34.05666667,
            "longitude": -117.91861111,
        },
    ],
    "Brockton,MA": [
        {
            "neighborhood": "Downtown Brockton",
            "latitude": 42.08333333,
            "longitude": -71.01888889,
        },
        {
            "neighborhood": "Campanelli",
            "latitude": 42.06933611,
            "longitude": -71.04269167,
        },
    ],
    "St. George,UT": [
        {
            "neighborhood": "Downtown St. George",
            "latitude": 37.28,
            "longitude": -113.52,
        },
        {"neighborhood": "Bloomington", "latitude": 37.075, "longitude": -113.57666667},
        {"neighborhood": "Sunbrook", "latitude": 37.075, "longitude": -113.57666667},
        {"neighborhood": "Tonaquint", "latitude": 37.075, "longitude": -113.57666667},
        {
            "neighborhood": "Little Valley",
            "latitude": 37.075,
            "longitude": -113.57666667,
        },
    ],
    "Bend,OR": [
        {
            "neighborhood": "Downtown Bend",
            "latitude": 44.05805556,
            "longitude": -121.31527778,
        },
        {
            "neighborhood": "Old Mill District",
            "latitude": 44.046,
            "longitude": -121.315,
        },
        {"neighborhood": "SW Bend", "latitude": 42.957761, "longitude": -94.451144},
        {"neighborhood": "Boyd Acres", "latitude": 44.08396, "longitude": -121.30324},
    ],
    "Renton,WA": [
        {"neighborhood": "Fairwood", "latitude": 47.44694444, "longitude": -122.1325}
    ],
    "Lee's Summit,MO": [
        {
            "neighborhood": "Downtown Lee's Summit",
            "latitude": 38.91722222,
            "longitude": -94.38166667,
        },
        {
            "neighborhood": "Eagle Creek",
            "latitude": 37.08416667,
            "longitude": -94.51305556,
        },
        {
            "neighborhood": "Greenwood",
            "latitude": 38.85083333,
            "longitude": -94.33805556,
        },
    ],
    "Fishers,IN": [
        {"neighborhood": "Geist", "latitude": 39.95611111, "longitude": -86.01277778},
        {
            "neighborhood": "Cumberland",
            "latitude": 39.95611111,
            "longitude": -86.01277778,
        },
    ],
    "El Monte,CA": [
        {
            "neighborhood": "Downtown El Monte",
            "latitude": 36.595,
            "longitude": -121.88527778,
        },
        {
            "neighborhood": "North El Monte",
            "latitude": 34.10305556,
            "longitude": -118.02333333,
        },
        {
            "neighborhood": "South El Monte",
            "latitude": 34.07333333,
            "longitude": -118.0275,
        },
        {
            "neighborhood": "Mountain View",
            "latitude": 34.07333333,
            "longitude": -118.0275,
        },
    ],
    "South Bend,IN": [
        {
            "neighborhood": "Downtown South Bend",
            "latitude": 41.6641,
            "longitude": -86.2208,
        },
        {"neighborhood": "River Park", "latitude": 29.25, "longitude": -103.25},
    ],
    "Rialto,CA": [
        {
            "neighborhood": "Downtown Rialto",
            "latitude": 34.11138889,
            "longitude": -117.3825,
        },
        {
            "neighborhood": "Rancho West",
            "latitude": 34.11138889,
            "longitude": -117.3825,
        },
        {"neighborhood": "Sierra Lakes", "latitude": 34.1, "longitude": -117.3},
    ],
    "Woodbridge,NJ": [
        {
            "neighborhood": "Woodbridge Township",
            "latitude": 40.556666,
            "longitude": -74.299213,
        },
        {"neighborhood": "Hopelawn", "latitude": 40.56, "longitude": -74.29},
    ],
    "El Cajon,CA": [
        {
            "neighborhood": "Downtown El Cajon",
            "latitude": 32.79833333,
            "longitude": -116.96,
        },
        {
            "neighborhood": "Rancho San Diego",
            "latitude": 32.79833333,
            "longitude": -116.96,
        },
        {"neighborhood": "Santee", "latitude": 32.79833333, "longitude": -116.96},
    ],
    "Inglewood,CA": [
        {
            "neighborhood": "Downtown Inglewood",
            "latitude": 33.9575,
            "longitude": -118.34611111,
        },
        {
            "neighborhood": "Morningside Park",
            "latitude": 33.9575,
            "longitude": -118.34611111,
        },
        {
            "neighborhood": "North Inglewood",
            "latitude": 33.9575,
            "longitude": -118.34611111,
        },
        {
            "neighborhood": "Fairview Heights",
            "latitude": 33.9575,
            "longitude": -118.34611111,
        },
        {"neighborhood": "Crenshaw", "latitude": 33.9575, "longitude": -118.34611111},
    ],
    "Burbank,CA": [
        {
            "neighborhood": "Downtown Burbank",
            "latitude": 34.18027778,
            "longitude": -118.32833333,
        },
        {
            "neighborhood": "Magnolia Park",
            "latitude": 34.18027778,
            "longitude": -118.32833333,
        },
        {
            "neighborhood": "Rancho District",
            "latitude": 34.18027778,
            "longitude": -118.32833333,
        },
        {
            "neighborhood": "Hillside District",
            "latitude": 34.14611111,
            "longitude": -118.255,
        },
        {
            "neighborhood": "Media District",
            "latitude": 34.18027778,
            "longitude": -118.32833333,
        },
    ],
    "Wichita Falls,TX": [
        {
            "neighborhood": "Downtown Wichita Falls",
            "latitude": 33.91216667,
            "longitude": -98.49475,
        },
        {"neighborhood": "Weeks Park", "latitude": 33.91216667, "longitude": -98.49475},
    ],
    "Vacaville,CA": [
        {
            "neighborhood": "Downtown Vacaville",
            "latitude": 38.35388889,
            "longitude": -121.97277778,
        },
        {
            "neighborhood": "North Vacaville",
            "latitude": 38.35388889,
            "longitude": -121.97277778,
        },
        {
            "neighborhood": "South Vacaville",
            "latitude": 38.35388889,
            "longitude": -121.97277778,
        },
        {
            "neighborhood": "East Vacaville",
            "latitude": 38.35388889,
            "longitude": -121.97277778,
        },
    ],
    "Carmel,IN": [
        {
            "neighborhood": "Arts and Design District",
            "latitude": 39.96805556,
            "longitude": -86.1125,
        },
        {"neighborhood": "Old Town", "latitude": 41.385, "longitude": -73.72944444},
        {
            "neighborhood": "Carmel Valley",
            "latitude": 36.55527778,
            "longitude": -121.92333333,
        },
        {
            "neighborhood": "Meridian Corridor",
            "latitude": 39.96805556,
            "longitude": -86.1125,
        },
    ],
    "Palm Coast,FL": [
        {
            "neighborhood": "Downtown Palm Coast",
            "latitude": 26.70972222,
            "longitude": -80.06416667,
        },
        {"neighborhood": "Palm Harbor", "latitude": 26.71, "longitude": -80.05},
        {"neighborhood": "Quail Hollow", "latitude": 28.3, "longitude": -82.44},
        {"neighborhood": "Indian Trails", "latitude": 29.47, "longitude": -81.3},
        {"neighborhood": "Pine Lakes", "latitude": 26.13333333, "longitude": -80.2},
    ],
    "Fayetteville,AR": [
        {
            "neighborhood": "Downtown Fayetteville",
            "latitude": 36.0625,
            "longitude": -94.1575,
        },
        {
            "neighborhood": "Dickson Street",
            "latitude": 36.06638889,
            "longitude": -94.16444444,
        },
        {
            "neighborhood": "Fayette Junction",
            "latitude": 36.0625,
            "longitude": -94.1575,
        },
        {
            "neighborhood": "University of Arkansas Campus",
            "latitude": 36.0625,
            "longitude": -94.1575,
        },
    ],
    "Quincy,MA": [
        {"neighborhood": "North Quincy", "latitude": 42.25, "longitude": -71.0},
        {
            "neighborhood": "Wollaston",
            "latitude": 42.26666667,
            "longitude": -71.01444444,
        },
        {"neighborhood": "Adams Shore", "latitude": 42.25, "longitude": -71.0},
        {"neighborhood": "Merrymount", "latitude": 42.2626, "longitude": -70.9953},
    ],
    "San Mateo,CA": [
        {
            "neighborhood": "Downtown San Mateo",
            "latitude": 37.55416667,
            "longitude": -122.31305556,
        },
        {
            "neighborhood": "Central Park",
            "latitude": 37.55416667,
            "longitude": -122.31305556,
        },
        {
            "neighborhood": "Bay Meadows",
            "latitude": 37.55416667,
            "longitude": -122.31305556,
        },
        {"neighborhood": "Hillsdale", "latitude": 37.53758, "longitude": -122.30031},
        {
            "neighborhood": "Foster City",
            "latitude": 37.55138889,
            "longitude": -122.26638889,
        },
    ],
    "Chico,CA": [
        {
            "neighborhood": "Downtown Chico",
            "latitude": 39.74,
            "longitude": -121.83555556,
        },
        {"neighborhood": "South Campus", "latitude": 39.74, "longitude": -121.83555556},
        {
            "neighborhood": "Upper Bidwell Park",
            "latitude": 39.769888,
            "longitude": -121.779156,
        },
    ],
    "Lynn,MA": [
        {"neighborhood": "Downtown Lynn", "latitude": 42.46666667, "longitude": -70.95},
        {
            "neighborhood": "Lynn Shore Drive",
            "latitude": 42.46666667,
            "longitude": -70.95,
        },
        {
            "neighborhood": "Diamond District",
            "latitude": 42.46666667,
            "longitude": -70.95,
        },
        {"neighborhood": "West Lynn", "latitude": 42.46666667, "longitude": -70.95},
    ],
    "Albany,NY": [
        {
            "neighborhood": "Downtown Albany",
            "latitude": 42.6525,
            "longitude": -73.75722222,
        },
        {"neighborhood": "Lark Street", "latitude": 42.6525, "longitude": -73.75722222},
        {"neighborhood": "Center Square", "latitude": 42.6, "longitude": -73.96666667},
    ],
    "Yuma,AZ": [
        {
            "neighborhood": "Downtown Yuma",
            "latitude": 32.66666667,
            "longitude": -114.57222222,
        },
        {
            "neighborhood": "Foothills",
            "latitude": 32.78694444,
            "longitude": -113.98277778,
        },
        {
            "neighborhood": "Desert Hills",
            "latitude": 32.78694444,
            "longitude": -113.98277778,
        },
        {
            "neighborhood": "Avenue B",
            "latitude": 32.78694444,
            "longitude": -113.98277778,
        },
    ],
    "New Bedford,MA": [
        {
            "neighborhood": "Downtown New Bedford",
            "latitude": 41.63611111,
            "longitude": -70.93472222,
        },
        {
            "neighborhood": "North End",
            "latitude": 41.63611111,
            "longitude": -70.93472222,
        },
        {
            "neighborhood": "South End",
            "latitude": 41.63611111,
            "longitude": -70.93472222,
        },
        {
            "neighborhood": "West End",
            "latitude": 41.63611111,
            "longitude": -70.93472222,
        },
        {
            "neighborhood": "Acushnet Heights",
            "latitude": 41.63611111,
            "longitude": -70.93472222,
        },
    ],
    "Suffolk,VA": [
        {
            "neighborhood": "Downtown Suffolk",
            "latitude": 36.74111111,
            "longitude": -76.60972222,
        },
        {
            "neighborhood": "North Suffolk",
            "latitude": 36.74111111,
            "longitude": -76.60972222,
        },
        {"neighborhood": "Driver", "latitude": 36.74111111, "longitude": -76.60972222},
        {
            "neighborhood": "Holy Neck",
            "latitude": 36.74111111,
            "longitude": -76.60972222,
        },
    ],
    "Hesperia,CA": [
        {
            "neighborhood": "Downtown Hesperia",
            "latitude": 34.37222222,
            "longitude": -117.33111111,
        },
        {"neighborhood": "Oak Hills", "latitude": 34.39, "longitude": -117.40305556},
        {"neighborhood": "Mesa Linda", "latitude": 34.0, "longitude": -118.2},
        {
            "neighborhood": "Victor Valley",
            "latitude": 34.37222222,
            "longitude": -117.33111111,
        },
    ],
}


syn_conversation_templates = {
    "sample_1": "assistant: Hi there! What can I do for you today?\nuser: I need to get to <CITY_1> from <CITY_2> sometime next month\nassistant: Sure thing! Do you have specific dates in mind, or are you flexible?\nuser: Probably around <DEPARTURE_DATE_1>, and I'd like to come back <DEPARTURE_DATE_2>\nassistant: Perfect. Any preferences on flight class or airlines?\nuser: Economy is fine. Just need something under <PRICE_1>\nassistant: Got it. How many people are traveling?\nuser: Just me",
    "sample_2": "assistant: Welcome! How may I assist you?\nuser: Looking for flights <CITY_1> to <CITY_2> leaving <DEPARTURE_DATE_1> for <NUM_TRAVELERS_1> people, business class, preferably <AIRLINE_1>, arriving before <ARRIVAL_TIME_1>\nassistant: Understood. Is this a one-way trip?\nuser: Yes\nassistant: And do you have any airport preferences in <CITY_2>?\nuser: <AIRPORT_1> if possible",
    "sample_3": "assistant: Good day! What brings you here?\nuser: Flights?\nassistant: Of course. Where are you headed?\nuser: <CITY_1>\nassistant: And where will you be departing from?\nuser: <CITY_2>\nassistant: When would you like to travel?\nuser: <DEPARTURE_DATE_1>\nassistant: One-way or round trip?\nuser: Round trip, back on <DEPARTURE_DATE_2>\nassistant: How many travelers?\nuser: <NUM_TRAVELERS_1> adults and they want <CLASS_1>",
    "sample_4": "assistant: Hello! What can I help you find today?\nuser: My anniversary is coming up and I want to surprise my wife with a trip to <CITY_1>. We're in <CITY_2>. I'm thinking we leave <DEPARTURE_DATE_1> and come back <DEPARTURE_DATE_2>. We've never flown anything better than economy but maybe this time we could do <CLASS_1>? Budget is around <PRICE_1> total for both of us. Oh, and she hates early morning flights so nothing before <DEPARTURE_TIME_1>\nassistant: That sounds wonderful! Just to confirm, that's <NUM_TRAVELERS_1> travelers in <CLASS_1>, departing after <DEPARTURE_TIME_1> on <DEPARTURE_DATE_1> and returning <DEPARTURE_DATE_2>?\nuser: Exactly right",
    "sample_5": "assistant: Hey! What do you need help with?\nuser: Need to fly out tomorrow\nassistant: That's short notice! Where to?\nuser: <CITY_1> from <CITY_2>\nassistant: Tomorrow being <DEPARTURE_DATE_1>. One-way?\nuser: Yeah. How many seats left usually?\nassistant: That varies by flight. How many do you need?\nuser: Just <NUM_TRAVELERS_1>\nassistant: Any time preferences or requirements?\nuser: Afternoon works. After <DEPARTURE_TIME_1>. And non-stop only, I can't deal with layovers",
    "sample_6": "assistant: Greetings! How can I assist with your travel plans?\nuser: I'm organizing a group trip. We need to get <NUM_TRAVELERS_1> people from <CITY_1> to <CITY_2> and then to <CITY_3> and finally back to <CITY_1>\nassistant: A multi-city itinerary. What are your travel dates for each leg?\nuser: <CITY_1> to <CITY_2> on <DEPARTURE_DATE_1>, <CITY_2> to <CITY_3> on <DEPARTURE_DATE_2>, and <CITY_3> back to <CITY_1> on <DEPARTURE_DATE_3>\nassistant: Excellent. Any class or budget constraints?\nuser: Economy, and we're hoping to stay under <PRICE_1> per person",
    "sample_7": "assistant: Hi! What are you looking for?\nuser: Cheap flight <CITY_1> to <CITY_2>\nassistant: When do you want to go?\nuser: Uh, maybe <DEPARTURE_DATE_1>? Or <DEPARTURE_DATE_2>? I'm not sure yet\nassistant: Are you flexible on dates to get a better price?\nuser: Yeah definitely. Anytime that week\nassistant: One-way or returning?\nuser: Oh returning, yeah. Back around <DEPARTURE_DATE_3> maybe?\nassistant: How many flying?\nuser: <NUM_TRAVELERS_1>",
    "sample_8": "assistant: Welcome aboard! What can I do for you?\nuser: I need the earliest possible flight from <CITY_1> to <CITY_2> on <DEPARTURE_DATE_1>. It's for work so I'll expense <CLASS_1>. Only <AIRLINE_1> though, company policy\nassistant: Understood. Just yourself traveling?\nuser: Correct, <NUM_TRAVELERS_1> traveler\nassistant: And is this one-way or will you need a return?\nuser: One-way for now. I'll book the return separately once I know my meeting schedule",
    "sample_9": "assistant: Hello there! How may I help?\nuser: Family vacation time! We're taking the kids to <CITY_1>\nassistant: Fun! Where are you coming from?\nuser: <CITY_2>\nassistant: And how many in your family?\nuser: <NUM_TRAVELERS_1> of us total\nassistant: When are you planning to go?\nuser: Leaving <DEPARTURE_DATE_1>, coming back <DEPARTURE_DATE_2>. We're trying to keep it under <PRICE_1> total if that's doable. Economy is fine\nassistant: Any specific departure times to work around school schedules or anything?\nuser: Not really, just prefer to arrive in <CITY_1> before <ARRIVAL_TIME_1> so we can check into the hotel",
    "sample_10": "assistant: Good afternoon! What do you need today?\nuser: Quick weekend trip\nassistant: Where to?\nuser: <CITY_1>\nassistant: From?\nuser: <CITY_2>\nassistant: Dates?\nuser: Out Friday <DEPARTURE_DATE_1>, back Sunday <DEPARTURE_DATE_2>\nassistant: Just you?\nuser: Me plus <NUM_TRAVELERS_1> friend, so <NUM_TRAVELERS_2> total\nassistant: Class preference?\nuser: Whatever's cheapest under <PRICE_1> each",
    "sample_11": "assistant: Hi! How can I help you today?\nuser: I want to go from <CITY_1> to <CITY_2> on <DEPARTURE_DATE_1> but I need to leave after <DEPARTURE_TIME_1> because I have a meeting. And I need to be there by <ARRIVAL_TIME_1> at the latest. It's just me, <NUM_TRAVELERS_1> person\nassistant: Noted. Is this round trip?\nuser: No, one-way. Actually, wait, can I see both one-way and round trip options? If I came back on <DEPARTURE_DATE_2>?\nassistant: Certainly. Any preference on airlines or class?\nuser: I usually fly <AIRLINE_1> and <CLASS_1> is preferred but I'll consider anything under <PRICE_1>",
    "sample_12": "assistant: Welcome! What are we booking today?\nuser: Trying to find something from <CITY_1> to <CITY_2>\nassistant: Excellent. What dates work for you?\nuser: That's the thing, I'm super flexible. Anytime in the next three weeks\nassistant: Perfect. That gives us options. Round trip or one-way?\nuser: Round trip, and I'd want to stay for about a week wherever I go\nassistant: How many travelers?\nuser: <NUM_TRAVELERS_1>\nassistant: Budget or class preferences?\nuser: Under <PRICE_1> and I'm fine with economy but if <CLASS_1> is close in price I'd love that",
    "sample_13": "assistant: Good evening! What can I assist you with?\nuser: <CITY_1> to <CITY_2>, <NUM_TRAVELERS_1> passengers, departing <DEPARTURE_DATE_1>\nassistant: Is this a round trip?\nuser: Yes, return <DEPARTURE_DATE_2>\nassistant: Any requirements regarding flight times, airlines, or class?\nuser: Must depart <CITY_1> after <DEPARTURE_TIME_1> and must arrive in <CITY_2> before <ARRIVAL_TIME_1>. No preference on airline. <CLASS_1> please",
    "sample_14": "assistant: Hey there! What's up?\nuser: So I'm thinking about visiting my sister in <CITY_1> but I'm not totally sure when. Maybe late next month? She lives near <AIRPORT_1> so that airport would be easiest\nassistant: No problem! Where would you be flying from?\nuser: <CITY_2>. There are like three airports here though. Probably <AIRPORT_2>\nassistant: Got it. When you say late next month, any specific date range?\nuser: Maybe around <DEPARTURE_DATE_1>? Give or take a few days\nassistant: And would you want to come back, or just one-way for now?\nuser: Oh definitely round trip. Back around <DEPARTURE_DATE_2>. It's just me traveling\nassistant: Any budget in mind?\nuser: Trying to keep it under <PRICE_1>",
    "sample_15": "assistant: Hello! How can I help?\nuser: Business trip <CITY_1> to <CITY_2> leaving tomorrow <DEPARTURE_DATE_1>\nassistant: Last minute! How many traveling?\nuser: <NUM_TRAVELERS_1> colleagues and myself, so <NUM_TRAVELERS_2> total\nassistant: Return date?\nuser: Same day, actually. Return flight after <DEPARTURE_TIME_1>\nassistant: Understood. Class preference?\nuser: <CLASS_1> for all of us. Company is paying",
    "sample_16": "assistant: Greetings! What brings you in?\nuser: I need help finding flights but I have really specific requirements\nassistant: That's what I'm here for. Tell me what you need\nuser: <CITY_1> to <CITY_2>, departing <DEPARTURE_DATE_1> between <DEPARTURE_TIME_1> and <DEPARTURE_TIME_2>, only <AIRLINE_1> or <AIRLINE_2>, must be non-stop, <CLASS_1>, for <NUM_TRAVELERS_1> travelers\nassistant: Very specific indeed. Is this one-way?\nuser: Round trip, returning <DEPARTURE_DATE_2>, same requirements for the return\nassistant: Budget?\nuser: No budget constraint, just meet those requirements",
    "sample_17": "assistant: Hi! What do you need?\nuser: Flight\nassistant: Where from and to?\nuser: <CITY_1> and <CITY_2>\nassistant: Which is departure and which is arrival?\nuser: Oh sorry, leaving from <CITY_1> going to <CITY_2>\nassistant: Travel dates?\nuser: <DEPARTURE_DATE_1>\nassistant: One-way or round trip?\nuser: Round trip, back <DEPARTURE_DATE_2>\nassistant: Number of people?\nuser: <NUM_TRAVELERS_1>\nassistant: Anything else I should know?\nuser: Yeah, we need <CLASS_1> and prefer flights that get us there before <ARRIVAL_TIME_1>",
    "sample_18": "assistant: Welcome! How may I assist with your travel?\nuser: Taking my elderly parents from <CITY_1> to <CITY_2> for a medical appointment. It's on <DEPARTURE_DATE_1> at <ARRIVAL_TIME_1> so we need to arrive the night before, <DEPARTURE_DATE_2>. Coming back the day after, <DEPARTURE_DATE_3>. There's three of us total, <NUM_TRAVELERS_1> travelers. They need <CLASS_1> for the extra legroom and comfort. Prefer <AIRLINE_1> if available since they have good accessibility services\nassistant: I understand. Any budget concerns?\nuser: Not really, their health is priority. Under <PRICE_1> total would be nice but not required",
    "sample_19": "assistant: Good day! What can I do for you?\nuser: Cheapest possible flight <CITY_1> to <CITY_2>\nassistant: When?\nuser: Anytime next week\nassistant: Which day is best?\nuser: Literally any day, just cheapest\nassistant: One-way?\nuser: Yeah\nassistant: Just you?\nuser: <NUM_TRAVELERS_1> person yeah\nassistant: Red-eye flights okay? Those tend to be cheaper\nuser: Sure, anything under <PRICE_1>",
    "sample_20": "assistant: Hello! What are you looking for today?\nuser: I'm relocating to <CITY_1> for a new job. Flying from <CITY_2> on <DEPARTURE_DATE_1>. One-way since I'm moving permanently. Just me, <NUM_TRAVELERS_1> traveler. I'll have lots of luggage so maybe <CLASS_1> for the baggage allowance? Trying to stay under <PRICE_1>\nassistant: Congratulations on the new job! Any preferred departure time?\nuser: Morning is better, before <DEPARTURE_TIME_1> if possible\nassistant: Any airline preferences?\nuser: No preference at all",
    "sample_21": "assistant: Hey! How can I help?\nuser: Yo, need flights for a bachelor party. <NUM_TRAVELERS_1> guys going from <CITY_1> to <CITY_2>\nassistant: Nice! When's the party?\nuser: Heading out <DEPARTURE_DATE_1>, coming back <DEPARTURE_DATE_2>\nassistant: Any must-haves?\nuser: We wanna get there by <ARRIVAL_TIME_1> to maximize the first day. And short layovers are okay but nothing crazy long. Budget is <PRICE_1> per person max\nassistant: Class preference?\nuser: Economy is cool",
    "sample_22": "assistant: Good morning! How may I help you?\nuser: I need to book a flight from <CITY_1> to <CITY_2> on <DEPARTURE_DATE_1> for <NUM_TRAVELERS_1> travelers in <CLASS_1>. We must fly <AIRLINE_1>. Our return is <DEPARTURE_DATE_2>. We need to depart after <DEPARTURE_TIME_1> on both legs\nassistant: Understood. Do you have a budget range?\nuser: Up to <PRICE_1> per person is acceptable",
    "sample_23": "assistant: Welcome! What can I help you with?\nuser: Conference in <CITY_1>, coming from <CITY_2>\nassistant: When is the conference?\nuser: Starts <DEPARTURE_DATE_1> morning so I should get in the day before, <DEPARTURE_DATE_2>\nassistant: And when does it end?\nuser: <DEPARTURE_DATE_3>, so I'd fly back that evening or <DEPARTURE_DATE_4> morning\nassistant: Just yourself?\nuser: Actually there are <NUM_TRAVELERS_1> of us from the office going\nassistant: Class preference?\nuser: Economy is standard but if <CLASS_1> is within <PRICE_1> of economy we'd upgrade",
    "sample_24": "assistant: Hi there! What do you need today?\nuser: Spontaneous trip! <CITY_1> to <CITY_2>, leaving in two days\nassistant: Adventurous! That would be <DEPARTURE_DATE_1>?\nuser: Yep!\nassistant: Coming back?\nuser: Hmm, maybe a week later? <DEPARTURE_DATE_2>?\nassistant: How many people?\nuser: Solo trip, <NUM_TRAVELERS_1>\nassistant: Budget?\nuser: Under <PRICE_1> total for both ways\nassistant: Any other preferences?\nuser: Window seat if possible and I hate connections so non-stop only please",
    "sample_25": "assistant: Hello! How can I assist?\nuser: I'm trying to coordinate travel for a wedding. Bride and groom need to get from <CITY_1> to <CITY_2> for their honeymoon, departing <DEPARTURE_DATE_1>. That's <NUM_TRAVELERS_1> people. They want <CLASS_1> obviously, it's their honeymoon. They're hoping for <AIRLINE_1> since they have status there. Budget isn't really an issue but let's say under <PRICE_1> total. One-way since they'll be traveling elsewhere after\nassistant: How romantic! Any preferred departure time?\nuser: They want to leave right after the reception, so evening departure, after <DEPARTURE_TIME_1>",
    "sample_26": "assistant: Good afternoon! What brings you here?\nuser: Looking at options for <CITY_1> to <CITY_2>\nassistant: Sure! What dates are you considering?\nuser: Well that's where I'm stuck. Either <DEPARTURE_DATE_1> or <DEPARTURE_DATE_2>. Which would be cheaper?\nassistant: I can check both. Is this round trip?\nuser: One-way\nassistant: How many passengers?\nuser: <NUM_TRAVELERS_1>\nassistant: I'll look at both dates. Any other requirements?\nuser: Yeah, needs to be <AIRLINE_1> and arrive before <ARRIVAL_TIME_1>. <CLASS_1>",
    "sample_27": "assistant: Hey! What's going on?\nuser: Need a flight\nassistant: Cool. Where are you headed?\nuser: <CITY_1> from <CITY_2>\nassistant: When?\nuser: This weekend, <DEPARTURE_DATE_1>\nassistant: Back the same weekend?\nuser: Nah, staying through next week, back <DEPARTURE_DATE_2>\nassistant: How many?\nuser: <NUM_TRAVELERS_1>\nassistant: What else?\nuser: Gotta be under <PRICE_1> and I'll take economy",
    "sample_28": "assistant: Welcome! How may I be of service?\nuser: I require a first-class flight from <CITY_1> to <CITY_2> departing <DEPARTURE_DATE_1> at approximately <DEPARTURE_TIME_1>. Party of <NUM_TRAVELERS_1>. I must arrive by <ARRIVAL_TIME_1> as I have an engagement. This is one-way travel. I prefer <AIRLINE_1> or <AIRLINE_2>. Price is not a concern\nassistant: Certainly. Would you like me to prioritize non-stop flights?\nuser: Yes, non-stop only. And <AIRPORT_1> in <CITY_2> specifically",
    "sample_29": "assistant: Hi! How can I help you today?\nuser: Me and my partner want to go somewhere warm. We're in <CITY_1>. Thinking maybe <CITY_2>? Or <CITY_3>? We're flexible. Sometime around <DEPARTURE_DATE_1>, back around <DEPARTURE_DATE_2>. Two of us, <NUM_TRAVELERS_1> travelers. We've got about <PRICE_1> to spend total. Economy is fine\nassistant: Great! Would you like me to check both <CITY_2> and <CITY_3> to see which fits better?\nuser: Yeah that would be awesome\nassistant: Any preferences on departure times or airlines?\nuser: Not picky, just want a good deal",
    "sample_30": "assistant: Good evening! What can I do for you?\nuser: Rush job interview in <CITY_1>. I'm in <CITY_2>. Interview is <DEPARTURE_DATE_1> at <ARRIVAL_TIME_1> so I need to get there the night before, <DEPARTURE_DATE_2>, arriving before <ARRIVAL_TIME_2>. Flying back same day as interview, evening flight after <DEPARTURE_TIME_1>. Just me, <NUM_TRAVELERS_1>. I'll do <CLASS_1> so I can work on the flight. Under <PRICE_1> total ideally\nassistant: I understand the urgency. Any airline preference?\nuser: None, just reliable with good wifi",
}

syn_plan_templates = {
    "sample_1": 'seek_information("We need the specific departure date")\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights", value=flights)\nfiltered_flights = get_results_from_cache(key="flights")',
    "sample_2": 'flights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"], airline=["<AIRLINE_1>"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"])\nsave_to_cache(key="flights", value=flights)\nfiltered_flights = get_results_from_cache(key="flights")',
    "sample_3": 'seek_information("We need the departure city")\nseek_information("We need the departure date")\nseek_information("We need to know if this is one-way or round trip")\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_4": 'flights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"])\nsave_to_cache(key="flights", value=flights)',
    "sample_5": 'seek_information("We need the destination city")\nseek_information("We need to confirm if this is one-way or round trip")\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"], num_layovers=[0])\nsave_to_cache(key="flights", value=flights)',
    "sample_6": 'flights_leg1 = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"])\nsave_to_cache(key="flights_leg1", value=flights_leg1)\nflights_leg2 = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_3>", departure_date=["<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights_leg2", value=flights_leg2)\nflights_leg3 = search_flights(start_airport_city="<CITY_3>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_3>"])\nsave_to_cache(key="flights_leg3", value=flights_leg3)',
    "sample_7": 'seek_information("We need to confirm the preferred departure date")\nseek_information("We need to confirm the return date")\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>", "<DEPARTURE_DATE_3>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_8": 'flights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"], airline=["<AIRLINE_1>"], departure_time=["00:00:00", "23:59:59"])\nsave_to_cache(key="flights", value=flights)',
    "sample_9": 'seek_information("We need the departure city")\nseek_information("We need the number of travelers")\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_10": 'seek_information("We need the departure city")\nseek_information("We need the travel dates")\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_11": 'flights_oneway = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"], airline=["<AIRLINE_1>"])\nsave_to_cache(key="flights_oneway", value=flights_oneway)\nflights_roundtrip = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"], airline=["<AIRLINE_1>"])\nsave_to_cache(key="flights_roundtrip", value=flights_roundtrip)',
    "sample_12": 'seek_information("We need a more specific date range for the flexible travel dates")\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>", "<DEPARTURE_DATE_3>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_13": 'flights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_14": 'seek_information("We need a more specific date or date range for the flexible travel dates")\nflights = search_flights(start_airport="<AIRPORT_2>", end_airport="<AIRPORT_1>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_15": 'flights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"])\nsave_to_cache(key="flights", value=flights)',
    "sample_16": 'flights_outbound = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"], departure_time=["<DEPARTURE_TIME_1>", "<DEPARTURE_TIME_2>"], airline=["<AIRLINE_1>", "<AIRLINE_2>"], num_layovers=[0])\nsave_to_cache(key="flights_outbound", value=flights_outbound)\nflights_return = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_2>"], departure_time=["<DEPARTURE_TIME_1>", "<DEPARTURE_TIME_2>"], airline=["<AIRLINE_1>", "<AIRLINE_2>"], num_layovers=[0])\nsave_to_cache(key="flights_return", value=flights_return)',
    "sample_17": 'seek_information("We need to clarify which city is departure and which is arrival")\nseek_information("We need to know if this is one-way or round trip")\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_18": 'flights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_2>", "<DEPARTURE_DATE_3>"], airline=["<AIRLINE_1>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_19": 'seek_information("We need a specific date from next week")\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>", "<DEPARTURE_DATE_3>", "<DEPARTURE_DATE_4>", "<DEPARTURE_DATE_5>", "<DEPARTURE_DATE_6>", "<DEPARTURE_DATE_7>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_20": 'flights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>"], departure_time=["00:00:00", "<DEPARTURE_TIME_1>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_21": 'flights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_22": 'flights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], airline=["<AIRLINE_1>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"])\nsave_to_cache(key="flights", value=flights)',
    "sample_23": 'seek_information("We need to confirm the return date preference")\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_2>", "<DEPARTURE_DATE_3>", "<DEPARTURE_DATE_4>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_24": 'seek_information("We need to confirm the departure date is in two days")\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"], num_layovers=[0])\nsave_to_cache(key="flights", value=flights)',
    "sample_25": 'flights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"], airline=["<AIRLINE_1>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"])\nsave_to_cache(key="flights", value=flights)',
    "sample_26": 'flights_option1 = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"], airline=["<AIRLINE_1>"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"])\nsave_to_cache(key="flights_option1", value=flights_option1)\nflights_option2 = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_2>"], airline=["<AIRLINE_1>"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"])\nsave_to_cache(key="flights_option2", value=flights_option2)',
    "sample_27": 'seek_information("We need to confirm the exact departure date this weekend")\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_28": 'flights = search_flights(start_airport_city="<CITY_1>", end_airport="<AIRPORT_1>", departure_date=["<DEPARTURE_DATE_1>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"], airline=["<AIRLINE_1>", "<AIRLINE_2>"], num_layovers=[0])\nsave_to_cache(key="flights", value=flights)',
    "sample_29": 'flights_city2 = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights_city2", value=flights_city2)\nflights_city3 = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_3>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights_city3", value=flights_city3)',
    "sample_30": 'flights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_2>", "<DEPARTURE_DATE_1>"], arrival_time=["00:00:00", "<ARRIVAL_TIME_2>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"])\nsave_to_cache(key="flights", value=flights)',
}

syn_plan_templates_v2 = {
    "sample_1": '\nseek_information("We need the specific departure date")\n\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights", value=flights)\n\nflighted_flights = get_results_from_cache(key="flights")',
    "sample_2": '\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"], airline=["<AIRLINE_1>"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"])\nsave_to_cache(key="flights", value=flights)\n\nfiltered_flights = get_results_from_cache(key="flights")',
    "sample_3": '\nseek_information("We need the departure city")\n\nseek_information("We need the departure date")\n\nseek_information("We need to know if this is one-way or round trip")\n\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_4": '\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"])\nsave_to_cache(key="flights", value=flights)',
    "sample_5": '\nseek_information("We need the destination city")\n\nseek_information("We need to confirm if this is one-way or round trip")\n\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"], num_layovers=[0])\nsave_to_cache(key="flights", value=flights)',
    "sample_6": '\nflights_leg1 = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"])\nsave_to_cache(key="flights_leg1", value=flights_leg1)\nflights_leg2 = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_3>", departure_date=["<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights_leg2", value=flights_leg2)\nflights_leg3 = search_flights(start_airport_city="<CITY_3>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_3>"])\nsave_to_cache(key="flights_leg3", value=flights_leg3)',
    "sample_7": '\nseek_information("We need to confirm the preferred departure date")\n\nseek_information("We need to confirm the return date")\n\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>", "<DEPARTURE_DATE_3>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_8": '\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"], airline=["<AIRLINE_1>"], departure_time=["00:00:00", "23:59:59"])\nsave_to_cache(key="flights", value=flights)',
    "sample_9": '\nseek_information("We need the departure city")\n\nseek_information("We need the number of travelers")\n\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_10": '\nseek_information("We need the departure city")\n\nseek_information("We need the travel dates")\n\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_11": '\nflights_oneway = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"], airline=["<AIRLINE_1>"])\nsave_to_cache(key="flights_oneway", value=flights_oneway)\nflights_roundtrip = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"], airline=["<AIRLINE_1>"])\nsave_to_cache(key="flights_roundtrip", value=flights_roundtrip)',
    "sample_12": '\nseek_information("We need a more specific date range for the flexible travel dates")\n\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>", "<DEPARTURE_DATE_3>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_13": '\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_14": '\nseek_information("We need a more specific date or date range for the flexible travel dates")\n\nflights = search_flights(start_airport="<AIRPORT_2>", end_airport="<AIRPORT_1>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_15": '\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"])\nsave_to_cache(key="flights", value=flights)',
    "sample_16": '\nflights_outbound = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"], departure_time=["<DEPARTURE_TIME_1>", "<DEPARTURE_TIME_2>"], airline=["<AIRLINE_1>", "<AIRLINE_2>"], num_layovers=[0])\nsave_to_cache(key="flights_outbound", value=flights_outbound)\nflights_return = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_2>"], departure_time=["<DEPARTURE_TIME_1>", "<DEPARTURE_TIME_2>"], airline=["<AIRLINE_1>", "<AIRLINE_2>"], num_layovers=[0])\nsave_to_cache(key="flights_return", value=flights_return)',
    "sample_17": '\nseek_information("We need to clarify which city is departure and which is arrival")\n\nseek_information("We need to know if this is one-way or round trip")\n\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_18": '\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_2>", "<DEPARTURE_DATE_3>"], airline=["<AIRLINE_1>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_19": '\nseek_information("We need a specific date from next week")\n\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>", "<DEPARTURE_DATE_3>", "<DEPARTURE_DATE_4>", "<DEPARTURE_DATE_5>", "<DEPARTURE_DATE_6>", "<DEPARTURE_DATE_7>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_20": '\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>"], departure_time=["00:00:00", "<DEPARTURE_TIME_1>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_21": '\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_22": '\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], airline=["<AIRLINE_1>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"])\nsave_to_cache(key="flights", value=flights)',
    "sample_23": '\nseek_information("We need to confirm the return date preference")\n\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_2>", "<DEPARTURE_DATE_3>", "<DEPARTURE_DATE_4>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_24": '\nseek_information("We need to confirm the departure date is in two days")\n\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"], num_layovers=[0])\nsave_to_cache(key="flights", value=flights)',
    "sample_25": '\nflights = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"], airline=["<AIRLINE_1>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"])\nsave_to_cache(key="flights", value=flights)',
    "sample_26": '\nflights_option1 = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>"], airline=["<AIRLINE_1>"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"])\nsave_to_cache(key="flights_option1", value=flights_option1)\nflights_option2 = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_2>"], airline=["<AIRLINE_1>"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"])\nsave_to_cache(key="flights_option2", value=flights_option2)',
    "sample_27": '\nseek_information("We need to confirm the exact departure date this weekend")\n\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights", value=flights)',
    "sample_28": '\nflights = search_flights(start_airport_city="<CITY_1>", end_airport="<AIRPORT_1>", departure_date=["<DEPARTURE_DATE_1>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"], arrival_time=["00:00:00", "<ARRIVAL_TIME_1>"], airline=["<AIRLINE_1>", "<AIRLINE_2>"], num_layovers=[0])\nsave_to_cache(key="flights", value=flights)',
    "sample_29": '\nflights_city2 = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_2>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights_city2", value=flights_city2)\nflights_city3 = search_flights(start_airport_city="<CITY_1>", end_airport_city="<CITY_3>", departure_date=["<DEPARTURE_DATE_1>", "<DEPARTURE_DATE_2>"])\nsave_to_cache(key="flights_city3", value=flights_city3)',
    "sample_30": '\nflights = search_flights(start_airport_city="<CITY_2>", end_airport_city="<CITY_1>", departure_date=["<DEPARTURE_DATE_2>", "<DEPARTURE_DATE_1>"], arrival_time=["00:00:00", "<ARRIVAL_TIME_2>"], departure_time=["<DEPARTURE_TIME_1>", "23:59:59"])\nsave_to_cache(key="flights", value=flights)',
}


def load_cities() -> List[str]:
    return [f"{city[0]},{city[1]}" for city in CITIES]


def load_airports() -> Dict[str, str]:
    # Map airport code to city name
    airports = {}
    for airport in FLIGHT_AIRPORTS:
        city_name = airport[0]
        airport_code = airport[1]
        airports[airport_code] = city_name
    return airports


def extract_placeholders(text: str) -> List[str]:
    return re.findall(r"<([A-Z_]+_\d+)>", text)


def generate_date(start_offset_days: int = 1, end_offset_days: int = 365) -> str:
    today = datetime.now()
    offset = random.randint(start_offset_days, end_offset_days)
    future_date = today + timedelta(days=offset)
    return future_date.strftime("%Y-%m-%d")


def generate_time() -> str:
    hour = random.randint(0, 23)
    minute = random.choice([0, 15, 30, 45])
    return f"{hour:02d}:{minute:02d}:00"


def generate_price(min_price: int = 50, max_price: int = 3000) -> str:
    return str(random.randint(min_price, max_price))


def generate_num_travelers() -> str:
    return str(random.randint(1, 10))


def sample_placeholder_value(
    placeholder: str,
    cities: List[str],
    airports: Dict[str, str],
    placeholder_values: Dict[str, str],
) -> str:
    airlines = [
        "AA",
        "AB",
        "AC",
        "AD",
        "AE",
        "AF",
        "AG",
        "AH",
        "AI",
        "AJ",
        "AK",
        "AL",
        "AM",
        "AN",
    ]
    flight_classes = ["economy", "business", "first"]

    base_type = re.match(r"([A-Z_]+)_\d+", placeholder).group(1)

    if base_type == "CITY":
        city = random.choice(cities)
        return city.split(",")[0]
    elif base_type == "AIRPORT":
        placeholder_num = re.match(r"[A-Z_]+_(\d+)", placeholder).group(1)
        city_placeholder = f"CITY_{placeholder_num}"

        if city_placeholder in placeholder_values:
            city = placeholder_values[city_placeholder]
            city_airports = [
                code for code, city_name in airports.items() if city_name == city
            ]
            if city_airports:
                return random.choice(city_airports)

        return random.choice(list(airports.keys()))
    elif base_type == "AIRLINE":
        return random.choice(airlines)
    elif base_type == "CLASS":
        return random.choice(flight_classes)
    elif base_type == "DEPARTURE_DATE":
        return generate_date()
    elif base_type == "DEPARTURE_TIME":
        return generate_time()
    elif base_type == "ARRIVAL_DATE":
        return generate_date()
    elif base_type == "ARRIVAL_TIME":
        return generate_time()
    elif base_type == "PRICE":
        return generate_price()
    elif base_type == "NUM_TRAVELERS":
        return generate_num_travelers()
    else:
        return f"UNKNOWN_{base_type}"


def fill_conv_plan_pair(
    conv: str, plan: str, cities: List[str], airports: Dict[str, str]
) -> tuple[str, str]:
    conv_placeholders = set(extract_placeholders(conv))
    plan_placeholders = set(extract_placeholders(plan))
    all_placeholders = conv_placeholders.union(plan_placeholders)

    placeholder_values = {}
    for placeholder in sorted(all_placeholders):
        placeholder_values[placeholder] = sample_placeholder_value(
            placeholder, cities, airports, placeholder_values
        )

    filled_conv = conv
    filled_plan = plan
    for placeholder, value in placeholder_values.items():
        filled_conv = filled_conv.replace(f"<{placeholder}>", value)
        filled_plan = filled_plan.replace(f"<{placeholder}>", value)

    return filled_conv, filled_plan


def main():
    seed = 42
    random.seed(seed)

    cities = load_cities()
    airports = load_airports()

    convs = syn_conversation_templates
    plans = syn_plan_templates_v2

    results = {}
    for sample_id in convs.keys():
        if sample_id in plans.keys():
            print(f"Processing {sample_id}")
            filled_conv, filled_plan = fill_conv_plan_pair(
                convs[sample_id], plans[sample_id], cities, airports
            )
            results[sample_id] = {"conversation": filled_conv, "plan": filled_plan}

    with open("filled_templates.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Generated {len(results)} filled templates")


if __name__ == "__main__":
    main()
