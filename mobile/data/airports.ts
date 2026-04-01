export interface Airport {
  iata: string;
  name: string;
  city: string;
  country: string;
}

export interface CityGroup {
  type: "city";
  city: string;
  country: string;
  airports: string[]; // IATA codes in priority order
  label: string;      // e.g. "London (LHR, LGW, STN +2)"
}

export type AirportOption = Airport | CityGroup;

// Cities with multiple major airports — shown at top of search results
export const CITY_GROUPS: CityGroup[] = [
  {
    type: "city", city: "London", country: "GB",
    airports: ["LHR", "LGW", "STN", "LTN", "LCY"],
    label: "London — all airports (LHR, LGW, STN, LTN, LCY)",
  },
  {
    type: "city", city: "New York", country: "US",
    airports: ["JFK", "LGA", "EWR"],
    label: "New York — all airports (JFK, LGA, EWR)",
  },
  {
    type: "city", city: "Tokyo", country: "JP",
    airports: ["NRT", "HND"],
    label: "Tokyo — all airports (NRT, HND)",
  },
  {
    type: "city", city: "Paris", country: "FR",
    airports: ["CDG", "ORY"],
    label: "Paris — all airports (CDG, ORY)",
  },
  {
    type: "city", city: "Milan", country: "IT",
    airports: ["MXP", "BGY", "LIN"],
    label: "Milan — all airports (MXP, BGY, LIN)",
  },
  {
    type: "city", city: "Chicago", country: "US",
    airports: ["ORD", "MDW"],
    label: "Chicago — all airports (ORD, MDW)",
  },
  {
    type: "city", city: "Istanbul", country: "TR",
    airports: ["IST", "SAW"],
    label: "Istanbul — all airports (IST, SAW)",
  },
  {
    type: "city", city: "Bangkok", country: "TH",
    airports: ["BKK", "DMK"],
    label: "Bangkok — all airports (BKK, DMK)",
  },
  {
    type: "city", city: "Shanghai", country: "CN",
    airports: ["PVG", "SHA"],
    label: "Shanghai — all airports (PVG, SHA)",
  },
  {
    type: "city", city: "Beijing", country: "CN",
    airports: ["PEK", "PKX"],
    label: "Beijing — all airports (PEK, PKX)",
  },
  {
    type: "city", city: "Washington DC", country: "US",
    airports: ["IAD", "DCA"],
    label: "Washington DC — all airports (IAD, DCA)",
  },
  {
    type: "city", city: "Osaka", country: "JP",
    airports: ["KIX", "ITM"],
    label: "Osaka — all airports (KIX, ITM)",
  },
  {
    type: "city", city: "Rome", country: "IT",
    airports: ["FCO", "CIA"],
    label: "Rome — all airports (FCO, CIA)",
  },
];


export const AIRPORTS: Airport[] = [
  { iata: "LHR", name: "Heathrow", city: "London", country: "GB" },
  { iata: "LGW", name: "Gatwick", city: "London", country: "GB" },
  { iata: "STN", name: "Stansted", city: "London", country: "GB" },
  { iata: "LTN", name: "Luton", city: "London", country: "GB" },
  { iata: "LCY", name: "City Airport", city: "London", country: "GB" },
  { iata: "MAN", name: "Manchester", city: "Manchester", country: "GB" },
  { iata: "EDI", name: "Edinburgh", city: "Edinburgh", country: "GB" },
  { iata: "BHX", name: "Birmingham", city: "Birmingham", country: "GB" },
  { iata: "GLA", name: "Glasgow", city: "Glasgow", country: "GB" },
  { iata: "BRS", name: "Bristol", city: "Bristol", country: "GB" },
  { iata: "NCL", name: "Newcastle", city: "Newcastle", country: "GB" },
  { iata: "LBA", name: "Leeds Bradford", city: "Leeds", country: "GB" },
  { iata: "BFS", name: "Belfast International", city: "Belfast", country: "GB" },
  { iata: "JFK", name: "John F. Kennedy", city: "New York", country: "US" },
  { iata: "LGA", name: "LaGuardia", city: "New York", country: "US" },
  { iata: "EWR", name: "Newark", city: "New York", country: "US" },
  { iata: "LAX", name: "Los Angeles", city: "Los Angeles", country: "US" },
  { iata: "ORD", name: "O'Hare", city: "Chicago", country: "US" },
  { iata: "MDW", name: "Midway", city: "Chicago", country: "US" },
  { iata: "ATL", name: "Hartsfield-Jackson", city: "Atlanta", country: "US" },
  { iata: "DFW", name: "Dallas/Fort Worth", city: "Dallas", country: "US" },
  { iata: "DEN", name: "Denver", city: "Denver", country: "US" },
  { iata: "SFO", name: "San Francisco", city: "San Francisco", country: "US" },
  { iata: "SEA", name: "Seattle-Tacoma", city: "Seattle", country: "US" },
  { iata: "MIA", name: "Miami", city: "Miami", country: "US" },
  { iata: "BOS", name: "Logan", city: "Boston", country: "US" },
  { iata: "LAS", name: "Las Vegas", city: "Las Vegas", country: "US" },
  { iata: "MCO", name: "Orlando", city: "Orlando", country: "US" },
  { iata: "PHX", name: "Phoenix Sky Harbor", city: "Phoenix", country: "US" },
  { iata: "IAD", name: "Dulles", city: "Washington DC", country: "US" },
  { iata: "DCA", name: "Reagan National", city: "Washington DC", country: "US" },
  { iata: "YYZ", name: "Pearson", city: "Toronto", country: "CA" },
  { iata: "YVR", name: "Vancouver", city: "Vancouver", country: "CA" },
  { iata: "YUL", name: "Montreal-Trudeau", city: "Montreal", country: "CA" },
  { iata: "YYC", name: "Calgary", city: "Calgary", country: "CA" },
  { iata: "CDG", name: "Charles de Gaulle", city: "Paris", country: "FR" },
  { iata: "ORY", name: "Orly", city: "Paris", country: "FR" },
  { iata: "FRA", name: "Frankfurt", city: "Frankfurt", country: "DE" },
  { iata: "MUC", name: "Munich", city: "Munich", country: "DE" },
  { iata: "BER", name: "Brandenburg", city: "Berlin", country: "DE" },
  { iata: "HAM", name: "Hamburg", city: "Hamburg", country: "DE" },
  { iata: "AMS", name: "Schiphol", city: "Amsterdam", country: "NL" },
  { iata: "MAD", name: "Barajas", city: "Madrid", country: "ES" },
  { iata: "BCN", name: "El Prat", city: "Barcelona", country: "ES" },
  { iata: "FCO", name: "Fiumicino", city: "Rome", country: "IT" },
  { iata: "MXP", name: "Malpensa", city: "Milan", country: "IT" },
  { iata: "ZRH", name: "Zurich", city: "Zurich", country: "CH" },
  { iata: "GVA", name: "Geneva", city: "Geneva", country: "CH" },
  { iata: "VIE", name: "Vienna", city: "Vienna", country: "AT" },
  { iata: "BRU", name: "Brussels", city: "Brussels", country: "BE" },
  { iata: "CPH", name: "Copenhagen", city: "Copenhagen", country: "DK" },
  { iata: "ARN", name: "Arlanda", city: "Stockholm", country: "SE" },
  { iata: "OSL", name: "Gardermoen", city: "Oslo", country: "NO" },
  { iata: "HEL", name: "Helsinki-Vantaa", city: "Helsinki", country: "FI" },
  { iata: "LIS", name: "Lisbon", city: "Lisbon", country: "PT" },
  { iata: "OPO", name: "Porto", city: "Porto", country: "PT" },
  { iata: "ATH", name: "Athens", city: "Athens", country: "GR" },
  { iata: "IST", name: "Istanbul", city: "Istanbul", country: "TR" },
  { iata: "SAW", name: "Sabiha Gokcen", city: "Istanbul", country: "TR" },
  { iata: "DXB", name: "Dubai", city: "Dubai", country: "AE" },
  { iata: "AUH", name: "Abu Dhabi", city: "Abu Dhabi", country: "AE" },
  { iata: "DOH", name: "Hamad", city: "Doha", country: "QA" },
  { iata: "KWI", name: "Kuwait", city: "Kuwait City", country: "KW" },
  { iata: "RUH", name: "King Khalid", city: "Riyadh", country: "SA" },
  { iata: "JED", name: "King Abdulaziz", city: "Jeddah", country: "SA" },
  { iata: "CAI", name: "Cairo", city: "Cairo", country: "EG" },
  { iata: "NBO", name: "Jomo Kenyatta", city: "Nairobi", country: "KE" },
  { iata: "JNB", name: "OR Tambo", city: "Johannesburg", country: "ZA" },
  { iata: "CPT", name: "Cape Town", city: "Cape Town", country: "ZA" },
  { iata: "ACC", name: "Kotoka", city: "Accra", country: "GH" },
  { iata: "LOS", name: "Murtala Muhammed", city: "Lagos", country: "NG" },
  { iata: "ADD", name: "Bole", city: "Addis Ababa", country: "ET" },
  { iata: "NRT", name: "Narita", city: "Tokyo", country: "JP" },
  { iata: "HND", name: "Haneda", city: "Tokyo", country: "JP" },
  { iata: "KIX", name: "Kansai", city: "Osaka", country: "JP" },
  { iata: "ICN", name: "Incheon", city: "Seoul", country: "KR" },
  { iata: "PEK", name: "Capital", city: "Beijing", country: "CN" },
  { iata: "PKX", name: "Daxing", city: "Beijing", country: "CN" },
  { iata: "PVG", name: "Pudong", city: "Shanghai", country: "CN" },
  { iata: "SHA", name: "Hongqiao", city: "Shanghai", country: "CN" },
  { iata: "HKG", name: "Hong Kong", city: "Hong Kong", country: "HK" },
  { iata: "SIN", name: "Changi", city: "Singapore", country: "SG" },
  { iata: "KUL", name: "KLIA", city: "Kuala Lumpur", country: "MY" },
  { iata: "BKK", name: "Suvarnabhumi", city: "Bangkok", country: "TH" },
  { iata: "DMK", name: "Don Mueang", city: "Bangkok", country: "TH" },
  { iata: "CGK", name: "Soekarno-Hatta", city: "Jakarta", country: "ID" },
  { iata: "MNL", name: "Ninoy Aquino", city: "Manila", country: "PH" },
  { iata: "SGN", name: "Tan Son Nhat", city: "Ho Chi Minh City", country: "VN" },
  { iata: "HAN", name: "Noi Bai", city: "Hanoi", country: "VN" },
  { iata: "BOM", name: "Chhatrapati Shivaji", city: "Mumbai", country: "IN" },
  { iata: "DEL", name: "Indira Gandhi", city: "Delhi", country: "IN" },
  { iata: "BLR", name: "Kempegowda", city: "Bangalore", country: "IN" },
  { iata: "MAA", name: "Chennai", city: "Chennai", country: "IN" },
  { iata: "CCU", name: "Netaji Subhas", city: "Kolkata", country: "IN" },
  { iata: "CMB", name: "Bandaranaike", city: "Colombo", country: "LK" },
  { iata: "DAC", name: "Hazrat Shahjalal", city: "Dhaka", country: "BD" },
  { iata: "KHI", name: "Jinnah", city: "Karachi", country: "PK" },
  { iata: "LHE", name: "Allama Iqbal", city: "Lahore", country: "PK" },
  { iata: "ISB", name: "Islamabad", city: "Islamabad", country: "PK" },
  { iata: "SYD", name: "Kingsford Smith", city: "Sydney", country: "AU" },
  { iata: "MEL", name: "Melbourne", city: "Melbourne", country: "AU" },
  { iata: "BNE", name: "Brisbane", city: "Brisbane", country: "AU" },
  { iata: "PER", name: "Perth", city: "Perth", country: "AU" },
  { iata: "AKL", name: "Auckland", city: "Auckland", country: "NZ" },
  { iata: "GRU", name: "Guarulhos", city: "São Paulo", country: "BR" },
  { iata: "GIG", name: "Galeão", city: "Rio de Janeiro", country: "BR" },
  { iata: "EZE", name: "Ezeiza", city: "Buenos Aires", country: "AR" },
  { iata: "SCL", name: "Arturo Merino Benítez", city: "Santiago", country: "CL" },
  { iata: "BOG", name: "El Dorado", city: "Bogotá", country: "CO" },
  { iata: "LIM", name: "Jorge Chávez", city: "Lima", country: "PE" },
  { iata: "MEX", name: "Benito Juárez", city: "Mexico City", country: "MX" },
  { iata: "CUN", name: "Cancún", city: "Cancún", country: "MX" },
  { iata: "TLV", name: "Ben Gurion", city: "Tel Aviv", country: "IL" },
  { iata: "AMM", name: "Queen Alia", city: "Amman", country: "JO" },
  { iata: "BEY", name: "Beirut-Rafic Hariri", city: "Beirut", country: "LB" },
  { iata: "WAW", name: "Chopin", city: "Warsaw", country: "PL" },
  { iata: "PRG", name: "Václav Havel", city: "Prague", country: "CZ" },
  { iata: "BUD", name: "Liszt Ferenc", city: "Budapest", country: "HU" },
  { iata: "OTP", name: "Henri Coandă", city: "Bucharest", country: "RO" },
  { iata: "SOF", name: "Sofia", city: "Sofia", country: "BG" },
  { iata: "SVO", name: "Sheremetyevo", city: "Moscow", country: "RU" },
  { iata: "LED", name: "Pulkovo", city: "St Petersburg", country: "RU" },
  { iata: "PMI", name: "Palma de Mallorca", city: "Palma", country: "ES" },
  { iata: "AGP", name: "Málaga", city: "Malaga", country: "ES" },
  { iata: "ALC", name: "Alicante-Elche", city: "Alicante", country: "ES" },
  { iata: "TFS", name: "Tenerife South", city: "Tenerife", country: "ES" },
  { iata: "LPA", name: "Gran Canaria", city: "Las Palmas", country: "ES" },
  { iata: "FUE", name: "Fuerteventura", city: "Fuerteventura", country: "ES" },
  { iata: "ACE", name: "Lanzarote", city: "Lanzarote", country: "ES" },
  { iata: "HER", name: "Nikos Kazantzakis", city: "Heraklion", country: "GR" },
  { iata: "RHO", name: "Rhodes", city: "Rhodes", country: "GR" },
  { iata: "CFU", name: "Corfu", city: "Corfu", country: "GR" },
  { iata: "SKG", name: "Thessaloniki", city: "Thessaloniki", country: "GR" },
  { iata: "NCE", name: "Nice Côte d'Azur", city: "Nice", country: "FR" },
  { iata: "MRS", name: "Marseille", city: "Marseille", country: "FR" },
  { iata: "LYS", name: "Lyon Saint-Exupéry", city: "Lyon", country: "FR" },
  { iata: "DUB", name: "Dublin", city: "Dublin", country: "IE" },
  { iata: "ORK", name: "Cork", city: "Cork", country: "IE" },
  { iata: "DBV", name: "Dubrovnik", city: "Dubrovnik", country: "HR" },
  { iata: "SPU", name: "Split", city: "Split", country: "HR" },
  { iata: "ZAG", name: "Zagreb", city: "Zagreb", country: "HR" },
  { iata: "OPO", name: "Francisco Sá Carneiro", city: "Porto", country: "PT" },
  { iata: "FAO", name: "Faro", city: "Faro", country: "PT" },
  { iata: "FNC", name: "Madeira", city: "Funchal", country: "PT" },
  { iata: "PDL", name: "João Paulo II", city: "Ponta Delgada", country: "PT" },
  { iata: "CMN", name: "Mohammed V", city: "Casablanca", country: "MA" },
  { iata: "RAK", name: "Marrakech-Menara", city: "Marrakech", country: "MA" },
  { iata: "TUN", name: "Tunis-Carthage", city: "Tunis", country: "TN" },
  { iata: "ALG", name: "Houari Boumediene", city: "Algiers", country: "DZ" },
  { iata: "HRG", name: "Hurghada", city: "Hurghada", country: "EG" },
  { iata: "SSH", name: "Sharm el-Sheikh", city: "Sharm el-Sheikh", country: "EG" },
  { iata: "MLE", name: "Velana", city: "Malé", country: "MV" },
  { iata: "SEZ", name: "Seychelles", city: "Mahé", country: "SC" },
  { iata: "MRU", name: "Sir Seewoosagur Ramgoolam", city: "Mauritius", country: "MU" },
  { iata: "ZNZ", name: "Abeid Amani Karume", city: "Zanzibar", country: "TZ" },
  { iata: "MBA", name: "Mombasa", city: "Mombasa", country: "KE" },
  { iata: "BKO", name: "Bamako-Sénou", city: "Bamako", country: "ML" },
  { iata: "ABV", name: "Nnamdi Azikiwe", city: "Abuja", country: "NG" },
];

export function searchOptions(query: string): AirportOption[] {
  if (!query || query.length < 2) return [];
  const q = query.toLowerCase().trim();

  // Match city groups first
  const cityMatches = CITY_GROUPS.filter(
    (g) =>
      g.city.toLowerCase().includes(q) ||
      g.airports.some((a) => a.toLowerCase().startsWith(q)) ||
      g.country.toLowerCase() === q
  );

  // Then individual airports (excluding airports already in a city group match)
  const groupedIatas = new Set(cityMatches.flatMap((g) => g.airports));
  const airportMatches = AIRPORTS.filter(
    (a) =>
      !groupedIatas.has(a.iata) &&
      (a.iata.toLowerCase().startsWith(q) ||
        a.city.toLowerCase().includes(q) ||
        a.name.toLowerCase().includes(q))
  ).slice(0, 6);

  return [...cityMatches, ...airportMatches].slice(0, 8);
}
